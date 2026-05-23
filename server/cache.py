#!/usr/bin/env python3
"""
bazi-pro 缓存层 v5.0
Redis 优先，未配置时降级为内存 LRU dict（支持 TTL）
降级状态通过 backend 属性和 _degraded_reason 暴露
"""

import json
import logging
import os
import time
from collections import OrderedDict
from typing import Optional

logger = logging.getLogger("bazi-pro.cache")


class LRUDict:

    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self._store: OrderedDict = OrderedDict()

    def get(self, key: str) -> Optional[dict]:
        if key in self._store:
            entry = self._store[key]
            if entry['_expires_at'] and time.time() > entry['_expires_at']:
                self._store.pop(key)
                return None
            self._store.move_to_end(key)
            return entry['value']
        return None

    def set(self, key: str, value: dict, ttl: int = 0) -> None:
        expires_at = time.time() + ttl if ttl > 0 else None
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = {'value': value, '_expires_at': expires_at}
        while len(self._store) > self.maxsize:
            self._store.popitem(last=False)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


class CacheStore:

    def __init__(self, redis_url: str = '', maxsize: int = 128):
        self._redis = None
        self._lru = LRUDict(maxsize=maxsize)
        self._degraded_reason: str = ''

        if redis_url:
            self._init_redis(redis_url)

    def _init_redis(self, redis_url: str) -> None:
        try:
            import redis
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
        except ImportError:
            self._degraded_reason = 'redis package not installed'
            logger.warning("Cache: redis package not installed, falling back to LRU memory")
        except Exception as e:
            self._degraded_reason = f'redis connection failed: {e}'
            logger.warning("Cache: Redis connection failed (%s), falling back to LRU memory", e)
            self._redis = None

    def get(self, key: str) -> Optional[dict]:
        if self._redis:
            try:
                val = self._redis.get(key)
                return json.loads(val) if val else None
            except Exception as e:
                logger.warning("Cache: Redis get failed (%s), falling back to LRU", e)
        return self._lru.get(key)

    def set(self, key: str, value: dict, ttl: int = 3600) -> None:
        if self._redis:
            try:
                self._redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
                return
            except Exception as e:
                logger.warning("Cache: Redis set failed (%s), falling back to LRU", e)
        self._lru.set(key, value, ttl=ttl)

    def delete(self, key: str) -> None:
        if self._redis:
            try:
                self._redis.delete(key)
                return
            except Exception as e:
                logger.warning("Cache: Redis delete failed (%s), falling back to LRU", e)
        self._lru.delete(key)

    @property
    def backend(self) -> str:
        return 'redis' if self._redis else 'lru_memory'

    @property
    def degraded_reason(self) -> str:
        return self._degraded_reason


_cache_instance: Optional[CacheStore] = None


def get_cache() -> CacheStore:
    global _cache_instance
    if _cache_instance is None:
        redis_url = os.environ.get('REDIS_URL', '')
        _cache_instance = CacheStore(redis_url=redis_url)
    return _cache_instance
