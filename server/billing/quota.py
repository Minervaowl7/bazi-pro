from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.billing.models import QuotaCheck, SubscriptionResponse
from server.models import Analysis, Subscription

logger = logging.getLogger("bazi-pro.billing.quota")

FREE_MONTHLY_QUOTA = 3


async def check_quota(user_id: str, db_session: Optional[AsyncSession]) -> QuotaCheck:
    if db_session is None:
        return QuotaCheck(allowed=True, remaining=999, plan="free")

    sub = await _get_active_subscription(user_id, db_session)
    plan = sub.plan if sub else "free"

    if plan in ("pro", "enterprise"):
        return QuotaCheck(allowed=True, remaining=-1, plan=plan)

    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    used = await _count_monthly_analyses(user_id, month_start, db_session)
    remaining = max(0, FREE_MONTHLY_QUOTA - used)
    allowed = remaining > 0

    return QuotaCheck(allowed=allowed, remaining=remaining, plan=plan)


async def deduct_quota(user_id: str, db_session: Optional[AsyncSession]) -> bool:
    if db_session is None:
        return True

    quota = await check_quota(user_id, db_session)
    if not quota.allowed:
        return False

    return True


async def get_subscription_status(user_id: str, db_session: Optional[AsyncSession]) -> Optional[SubscriptionResponse]:
    if db_session is None:
        return None

    sub = await _get_active_subscription(user_id, db_session)
    if sub is None:
        return None

    return SubscriptionResponse(
        id=str(sub.id),
        plan=sub.plan,
        status=sub.status,
        started_at=sub.started_at,
        expires_at=sub.expires_at,
    )


async def _get_active_subscription(user_id: str, db_session: AsyncSession) -> Optional[Subscription]:
    try:
        uid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        return None

    now = datetime.now(timezone.utc)
    stmt = (
        select(Subscription)
        .where(
            Subscription.user_id == uid,
            Subscription.status == "active",
            Subscription.started_at <= now,
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    result = await db_session.execute(stmt)
    sub = result.scalar_one_or_none()

    if sub is None:
        return None

    if sub.expires_at is not None and sub.expires_at < now:
        sub.status = "expired"
        await db_session.flush()
        return None

    return sub


async def _count_monthly_analyses(user_id: str, month_start: datetime, db_session: AsyncSession) -> int:
    try:
        uid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        return 0

    now = datetime.now(timezone.utc)
    if now.month == 12:
        month_end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        month_end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)

    stmt = (
        select(func.count())
        .select_from(Analysis)
        .where(
            Analysis.user_id == uid,
            Analysis.created_at >= month_start,
            Analysis.created_at < month_end,
        )
    )
    result = await db_session.execute(stmt)
    count = result.scalar_one()
    return count if count is not None else 0
