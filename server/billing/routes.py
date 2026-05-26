from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.billing.alipay import AlipayClient
from server.billing.models import (
    OrderCreate,
    OrderResponse,
    QuotaCheck,
    SubscriptionCreate,
    SubscriptionResponse,
)
from server.billing.quota import check_quota, get_subscription_status
from server.billing.wechat_pay import WechatPayClient
from server.database import get_db
from server.models import Order, Subscription

logger = logging.getLogger("bazi-pro.billing.routes")

router = APIRouter(prefix="/api/billing", tags=["billing"])

_wechat_client = WechatPayClient()
_alipay_client = AlipayClient()


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


@router.post("/order", response_model=OrderResponse)
async def create_order(
    payload: OrderCreate,
    db: Optional[AsyncSession] = Depends(get_db),
):
    if db is None:
        return _error_response(503, "SERVICE_UNAVAILABLE", "数据库不可用")

    order_id = uuid.uuid4()
    order = Order(
        id=order_id,
        user_id=uuid.UUID(payload.user_id),
        amount=payload.amount,
        payment_method=payload.payment_method,
        status="pending",
        description=payload.description,
    )
    db.add(order)
    await db.flush()

    notify_url = ""
    payment_url: Optional[str] = None

    if payload.payment_method == "wechat":
        result = _wechat_client.create_order(
            order_id=str(order_id),
            amount=payload.amount,
            description=payload.description,
            notify_url=notify_url,
        )
        if result:
            payment_url = result.get("code_url")
        else:
            payment_url = None
    elif payload.payment_method == "alipay":
        return_url = ""
        payment_url = _alipay_client.create_order(
            order_id=str(order_id),
            amount=payload.amount,
            description=payload.description,
            notify_url=notify_url,
            return_url=return_url,
        )

    return OrderResponse(
        order_id=str(order_id),
        amount=payload.amount,
        status="pending",
        payment_url=payment_url,
        created_at=order.created_at,
    )


@router.post("/wechat/callback")
async def wechat_callback(request: Request):
    body = await request.form()
    data = dict(body)

    sign = data.pop("sign", "")
    if not _wechat_client.verify_callback(data, sign):
        return JSONResponse(
            status_code=400,
            content={"return_code": "FAIL", "return_msg": "签名验证失败"},
        )

    order_id = data.get("out_trade_no", "")
    transaction_id = data.get("transaction_id", "")

    db_gen = get_db()
    db = await db_gen.__anext__()
    try:
        if order_id:
            stmt = select(Order).where(Order.id == uuid.UUID(order_id))
            result = await db.execute(stmt)
            order = result.scalar_one_or_none()
            if order and order.status == "pending":
                order.status = "paid"
                order.transaction_id = transaction_id
                order.paid_at = datetime.now(timezone.utc)
                await db.flush()
    except Exception as e:
        logger.error("WechatPay callback processing failed: %s", e)
    finally:
        try:
            await db.commit()
        except Exception:
            await db.rollback()
        try:
            await db_gen.aclose()
        except Exception:
            pass

    return JSONResponse(content={"return_code": "SUCCESS", "return_msg": "OK"})


@router.post("/alipay/callback")
async def alipay_callback(request: Request):
    body = await request.form()
    data = dict(body)

    sign = data.pop("sign", "")
    data.pop("sign_type", "")

    if not _alipay_client.verify_callback(data, sign):
        return JSONResponse(status_code=400, content={"status": "fail", "message": "签名验证失败"})

    order_id = data.get("out_trade_no", "")
    transaction_id = data.get("trade_no", "")
    trade_status = data.get("trade_status", "")

    if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        return JSONResponse(content={"status": "success"})

    db_gen = get_db()
    db = await db_gen.__anext__()
    try:
        if order_id:
            stmt = select(Order).where(Order.id == uuid.UUID(order_id))
            result = await db.execute(stmt)
            order = result.scalar_one_or_none()
            if order and order.status == "pending":
                order.status = "paid"
                order.transaction_id = transaction_id
                order.paid_at = datetime.now(timezone.utc)
                await db.flush()
    except Exception as e:
        logger.error("Alipay callback processing failed: %s", e)
    finally:
        try:
            await db.commit()
        except Exception:
            await db.rollback()
        try:
            await db_gen.aclose()
        except Exception:
            pass

    return JSONResponse(content={"status": "success"})


@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_subscription(
    user_id: str,
    db: Optional[AsyncSession] = Depends(get_db),
):
    sub = await get_subscription_status(user_id, db)
    if sub is None:
        return _error_response(404, "NOT_FOUND", "未找到活跃订阅")
    return sub


@router.post("/subscription", response_model=SubscriptionResponse)
async def create_subscription(
    payload: SubscriptionCreate,
    db: Optional[AsyncSession] = Depends(get_db),
):
    if db is None:
        return _error_response(503, "SERVICE_UNAVAILABLE", "数据库不可用")

    uid = uuid.UUID(payload.user_id)

    stmt = (
        select(Subscription)
        .where(
            Subscription.user_id == uid,
            Subscription.status == "active",
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        existing.plan = payload.plan
        existing.status = "active"
        existing.started_at = datetime.now(timezone.utc)
        await db.flush()

        return SubscriptionResponse(
            id=str(existing.id),
            plan=existing.plan,
            status=existing.status,
            started_at=existing.started_at,
            expires_at=existing.expires_at,
        )

    sub = Subscription(
        user_id=uid,
        plan=payload.plan,
        status="active",
        started_at=datetime.now(timezone.utc),
    )
    db.add(sub)
    await db.flush()

    return SubscriptionResponse(
        id=str(sub.id),
        plan=sub.plan,
        status=sub.status,
        started_at=sub.started_at,
        expires_at=sub.expires_at,
    )


@router.get("/quota", response_model=QuotaCheck)
async def get_quota(
    user_id: str,
    db: Optional[AsyncSession] = Depends(get_db),
):
    return await check_quota(user_id, db)
