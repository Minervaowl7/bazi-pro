from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    user_id: str = Field(..., description="用户 ID")
    amount: int = Field(..., gt=0, description="金额，单位为分")
    payment_method: str = Field(..., pattern="^(wechat|alipay)$", description="支付方式")
    description: str = Field(..., min_length=1, max_length=200, description="订单描述")


class OrderResponse(BaseModel):
    order_id: str
    amount: int
    status: str
    payment_url: Optional[str] = None
    created_at: Optional[datetime] = None


class SubscriptionCreate(BaseModel):
    user_id: str = Field(..., description="用户 ID")
    plan: str = Field(..., pattern="^(free|pro|enterprise)$", description="订阅计划")


class SubscriptionResponse(BaseModel):
    id: str
    plan: str
    status: str
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class QuotaCheck(BaseModel):
    allowed: bool
    remaining: int
    plan: str
