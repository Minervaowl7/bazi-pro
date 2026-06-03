#!/usr/bin/env python3

import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger("bazi-pro.ratelimit")


class RateLimiter(ABC):

    @abstractmethod
    def is_allowed(self, key: str) -> bool:
        ...

    @abstractmethod
    def cleanup(self, now: float) -> int:
        ...


class MemoryRateLimiter(RateLimiter):

    _MAX_BUCKETS = 10000

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = {}

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        timestamps = self._buckets.setdefault(key, [])
        self._buckets[key] = [t for t in timestamps if now - t < self.window_seconds]
        if len(self._buckets[key]) >= self.max_requests:
            return False
        self._buckets[key].append(now)
        if len(self._buckets) > self._MAX_BUCKETS:
            self.cleanup(now)
        return True

    def cleanup(self, now: float) -> int:
        expired_keys = []
        for key, timestamps in self._buckets.items():
            filtered = [t for t in timestamps if now - t < self.window_seconds]
            if not filtered:
                expired_keys.append(key)
            else:
                self._buckets[key] = filtered
        for key in expired_keys:
            self._buckets.pop(key, None)
        return len(expired_keys)


class RedisRateLimiter(RateLimiter):

    def __init__(self, redis_url: str, max_requests: int = 30,
                 window_seconds: int = 60, key_prefix: str = "bazi:rl:"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._prefix = key_prefix
        self._redis = None
        self._fallback: Optional[MemoryRateLimiter] = None
        self._degraded = False
        try:
            import redis
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
        except Exception as e:
            logger.warning("RedisRateLimiter init failed: %s, falling back to memory", e)
            self._redis = None
            self._fallback = MemoryRateLimiter(max_requests, window_seconds)
            self._degraded = True

    def _key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def is_allowed(self, key: str) -> bool:
        if self._redis:
            try:
                now = time.time()
                rkey = self._key(key)
                member = f"{now}:{uuid.uuid4()}"
                pipe = self._redis.pipeline()
                pipe.zremrangebyscore(rkey, 0, now - self.window_seconds)
                pipe.zcard(rkey)
                pipe.zadd(rkey, {member: now})
                pipe.expire(rkey, self.window_seconds + 1)
                results = pipe.execute()
                count = results[1]
                if count >= self.max_requests:
                    self._redis.zrem(rkey, member)
                    return False
                return True
            except Exception as e:
                logger.warning("Redis rate limit failed: %s, falling back to memory", e)
                self._degraded = True
                self._redis = None
                if self._fallback is None:
                    self._fallback = MemoryRateLimiter(self.max_requests, self.window_seconds)
        if self._fallback:
            return self._fallback.is_allowed(key)
        logger.error("Rate limiter has no backend available, denying request")
        return False

    def cleanup(self, now: float) -> int:
        if self._fallback:
            return self._fallback.cleanup(now)
        return 0

    @property
    def is_degraded(self) -> bool:
        return self._degraded


def create_rate_limiter(max_requests: int = 30,
                        window_seconds: int = 60) -> RateLimiter:
    redis_url = os.environ.get("REDIS_URL", "")
    if redis_url:
        limiter = RedisRateLimiter(redis_url, max_requests, window_seconds)
        if limiter._redis:
            return limiter
    return MemoryRateLimiter(max_requests, window_seconds)
