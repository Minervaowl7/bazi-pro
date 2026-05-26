#!/usr/bin/env python3

import logging
import os
import uuid as _uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from server.models import Analysis, Base

logger = logging.getLogger("bazi-pro.database")

_engine = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
_degraded: bool = False
_degraded_reason: str = ""


def _build_database_url() -> str:
    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        return ""
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+asyncpg://", 1)
    return raw


def is_degraded() -> bool:
    return _degraded


def degraded_reason() -> str:
    return _degraded_reason


def backend() -> str:
    return "memory" if _degraded else "postgresql"


async def init_db() -> None:
    global _engine, _session_factory, _degraded, _degraded_reason

    database_url = _build_database_url()
    if not database_url:
        _degraded = True
        _degraded_reason = "DATABASE_URL not set"
        logger.warning("Database: DATABASE_URL not set, running in memory mode")
        return

    try:
        _engine = create_async_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            echo=False,
        )
        _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        _degraded = False
        _degraded_reason = ""
        logger.info("Database: PostgreSQL connected, tables created")
    except ImportError:
        _degraded = True
        _degraded_reason = "asyncpg package not installed"
        logger.warning("Database: asyncpg not installed, running in memory mode")
        _engine = None
        _session_factory = None
    except Exception as e:
        _degraded = True
        _degraded_reason = f"postgresql connection failed: {e}"
        logger.warning("Database: PostgreSQL connection failed (%s), running in memory mode", e)
        _engine = None
        _session_factory = None


async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    if _session_factory is None:
        yield None
        return
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def persist_analysis(run_id: str, user_id: Optional[str], bazi: str,
                           day_master: str, gender: str, solar_date: Optional[str],
                           detail_level: str, status: str,
                           result: Optional[dict]) -> None:
    if _session_factory is None:
        return

    async with _session_factory() as session:
        try:
            stmt = Analysis.__table__.select().where(Analysis.run_id == run_id)
            row = await session.execute(stmt)
            existing = row.first()

            if existing:
                update_values = {"status": status}
                if result is not None:
                    update_values["result"] = result
                if status in ("completed", "failed"):
                    update_values["completed_at"] = datetime.now(timezone.utc)
                await session.execute(
                    Analysis.__table__.update().where(Analysis.run_id == run_id).values(**update_values)
                )
            else:
                uid = _uuid.UUID(user_id) if user_id else None
                analysis = Analysis(
                    user_id=uid,
                    run_id=run_id,
                    bazi=bazi,
                    day_master=day_master,
                    gender=gender,
                    solar_date=solar_date,
                    detail_level=detail_level,
                    status=status,
                    result=result,
                    completed_at=datetime.now(timezone.utc) if status in ("completed", "failed") else None,
                )
                session.add(analysis)

            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Database: persist_analysis failed for run_id=%s: %s", run_id, e)


async def get_user_analyses(user_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
    if _session_factory is None:
        return []

    async with _session_factory() as session:
        try:
            stmt = (
                Analysis.__table__.select()
                .where(Analysis.user_id == _uuid.UUID(user_id))
                .order_by(Analysis.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            rows = result.fetchall()
            return [
                {
                    "id": str(row.id),
                    "run_id": row.run_id,
                    "bazi": row.bazi,
                    "day_master": row.day_master,
                    "gender": row.gender,
                    "solar_date": row.solar_date,
                    "detail_level": row.detail_level,
                    "status": row.status,
                    "result": row.result,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                }
                for row in rows
            ]
        except Exception as e:
            logger.error("Database: get_user_analyses failed: %s", e)
            return []


async def close_db() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
