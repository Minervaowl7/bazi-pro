from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
import uuid
from typing import Optional

logger = logging.getLogger("bazi-pro.billing.wechat")


class WechatPayClient:
    def __init__(self) -> None:
        self.app_id = os.environ.get("WECHAT_APP_ID", "")
        self.mch_id = os.environ.get("WECHAT_MCH_ID", "")
        self.api_key = os.environ.get("WECHAT_API_KEY", "")
        self._configured = bool(self.app_id and self.mch_id and self.api_key)

        if not self._configured:
            logger.info("WechatPay: environment variables not set, client disabled")

    def create_order(
        self,
        order_id: str,
        amount: int,
        description: str,
        notify_url: str,
    ) -> Optional[dict]:
        if not self._configured:
            logger.warning("WechatPay: client not configured, cannot create order")
            return None

        nonce_str = uuid.uuid4().hex
        prepay_id = f"wx{uuid.uuid4().hex[:28]}"

        params = {
            "appid": self.app_id,
            "mch_id": self.mch_id,
            "nonce_str": nonce_str,
            "body": description,
            "out_trade_no": order_id,
            "total_fee": str(amount),
            "spbill_create_ip": "127.0.0.1",
            "notify_url": notify_url,
            "trade_type": "NATIVE",
        }

        sign = self._sign(params)
        params["sign"] = sign

        return {
            "prepay_id": prepay_id,
            "trade_type": "NATIVE",
            "code_url": self.generate_payment_url(prepay_id),
            "params": params,
        }

    def verify_callback(self, data: dict, signature: str) -> bool:
        if not self._configured:
            logger.warning("WechatPay: client not configured, cannot verify callback")
            return False

        filtered = {k: v for k, v in data.items() if k != "sign" and v}
        expected_sign = self._sign(filtered)
        return hmac.compare_digest(expected_sign, signature)

    def generate_payment_url(self, prepay_id: str) -> str:
        if not self._configured:
            return ""

        timestamp = str(int(time.time()))
        nonce_str = uuid.uuid4().hex
        params = {
            "appId": self.app_id,
            "timeStamp": timestamp,
            "nonceStr": nonce_str,
            "package": f"prepay_id={prepay_id}",
            "signType": "MD5",
        }
        pay_sign = self._sign(params)
        return f"weixin://wxpay/bizpayurl?pr={prepay_id}&sign={pay_sign}"

    def _sign(self, params: dict) -> str:
        sorted_items = sorted(params.items())
        query = "&".join(f"{k}={v}" for k, v in sorted_items if v)
        query_with_key = f"{query}&key={self.api_key}"
        return hashlib.md5(query_with_key.encode("utf-8")).hexdigest().upper()
