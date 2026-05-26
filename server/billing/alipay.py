from __future__ import annotations

import base64
import logging
import os
from typing import Optional
from urllib.parse import urlencode

logger = logging.getLogger("bazi-pro.billing.alipay")


class AlipayClient:
    def __init__(self) -> None:
        self.app_id = os.environ.get("ALIPAY_APP_ID", "")
        self.private_key = os.environ.get("ALIPAY_PRIVATE_KEY", "")
        self.public_key = os.environ.get("ALIPAY_PUBLIC_KEY", "")
        self._configured = bool(self.app_id and self.private_key and self.public_key)

        if not self._configured:
            logger.info("Alipay: environment variables not set, client disabled")

    def create_order(
        self,
        order_id: str,
        amount: int,
        description: str,
        notify_url: str,
        return_url: str,
    ) -> Optional[str]:
        if not self._configured:
            logger.warning("Alipay: client not configured, cannot create order")
            return None

        amount_yuan = amount / 100.0

        biz_content = (
            f'{{"out_trade_no":"{order_id}",'
            f'"total_amount":"{amount_yuan:.2f}",'
            f'"subject":"{description}",'
            f'"product_code":"FAST_INSTANT_TRADE_PAY"}}'
        )

        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.page.pay",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": _now_formatted(),
            "version": "1.0",
            "notify_url": notify_url,
            "return_url": return_url,
            "biz_content": biz_content,
        }

        sign = self._sign(params)
        params["sign"] = sign

        return f"https://openapi.alipay.com/gateway.do?{urlencode(params)}"

    def verify_callback(self, data: dict, signature: str) -> bool:
        if not self._configured:
            logger.warning("Alipay: client not configured, cannot verify callback")
            return False

        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding

            filtered = {k: v for k, v in sorted(data.items()) if k != "sign" and k != "sign_type" and v}
            sign_string = "&".join(f"{k}={v}" for k, v in filtered.items())

            public_key_obj = serialization.load_pem_public_key(
                self.public_key.encode("utf-8")
            )
            public_key_obj.verify(
                signature.encode("utf-8") if isinstance(signature, str) else signature,
                sign_string.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True
        except Exception as e:
            logger.error("Alipay: callback verification failed: %s", e)
            return False

    def _sign(self, params: dict) -> str:
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding

            filtered = {k: v for k, v in sorted(params.items()) if k != "sign" and v}
            sign_string = "&".join(f"{k}={v}" for k, v in filtered.items())

            private_key_obj = serialization.load_pem_private_key(
                self.private_key.encode("utf-8"),
                password=None,
            )
            raw_sign = private_key_obj.sign(
                sign_string.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )

            return base64.b64encode(raw_sign).decode("utf-8")
        except Exception as e:
            logger.error("Alipay: signing failed: %s", e)
            return ""


def _now_formatted() -> str:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M:%S")
