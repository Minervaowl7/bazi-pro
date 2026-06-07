from __future__ import annotations

import hmac
import logging
import os
import re
import time

from fastapi import Request, Security
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from server.ratelimiter import MemoryRateLimiter, RateLimiter, RedisRateLimiter, create_rate_limiter
from server.taskstore import MemoryTaskStore, RedisTaskStore, create_task_store

logger = logging.getLogger("bazi-pro")

ANALYSIS_ID_PATTERN = re.compile(r'^ana_[0-9a-f]{8,24}$')


def validate_analysis_id(analysis_id: str) -> bool:
    return bool(ANALYSIS_ID_PATTERN.match(analysis_id))


def get_int_env(name: str, default: int, min_value: int = 1) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
        if value < min_value:
            raise ValueError
        return value
    except (ValueError, TypeError):
        logger.warning("Invalid %s=%r, using default %s", name, raw, default)
        return default


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


task_store = create_task_store()
TASK_TTL_SECONDS = get_int_env("BAZI_TASK_TTL_SECONDS", 7200)
MAX_CONCURRENT_TASKS = get_int_env("BAZI_MAX_CONCURRENT_TASKS", 1000)

MAX_PAYLOAD_BYTES = get_int_env("BAZI_MAX_PAYLOAD_BYTES", 10240)
RATE_LIMIT_REQUESTS = get_int_env("BAZI_RATE_LIMIT_REQUESTS", 30)
RATE_LIMIT_WINDOW_SECONDS = get_int_env("BAZI_RATE_LIMIT_WINDOW_SECONDS", 60)
rate_limiter = create_rate_limiter(
    max_requests=RATE_LIMIT_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
)

API_KEY = os.environ.get('BAZI_API_KEY', '')
_api_key_scheme = APIKeyHeader(name='X-API-Key', auto_error=False)


class APIKeyError(Exception):
    pass


async def verify_api_key(request: Request, api_key: str = Security(_api_key_scheme)):
    if not API_KEY:
        if os.environ.get('ENV', '').lower() in ('prod', 'production'):
            logger.error("API key not configured in production environment!")
            raise APIKeyError()
        return True
    if api_key and hmac.compare_digest(api_key, API_KEY):
        return True
    token = request.query_params.get("token", "")
    if token and hmac.compare_digest(token, API_KEY):
        return True
    raise APIKeyError()


def cleanup_expired_tasks() -> None:
    task_store.cleanup_expired(TASK_TTL_SECONDS)


def backend_name(store) -> str:
    if isinstance(store, RedisTaskStore):
        if store.is_degraded:
            return "redis(degraded)"
        return "redis"
    if isinstance(store, MemoryTaskStore):
        return "memory"
    return type(store).__name__


def ratelimiter_backend_name(limiter) -> str:
    if isinstance(limiter, RedisRateLimiter):
        if limiter.is_degraded:
            return "redis(degraded)"
        return "redis"
    if isinstance(limiter, MemoryRateLimiter):
        return "memory"
    return type(limiter).__name__
