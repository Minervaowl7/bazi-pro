#!/usr/bin/env python3
"""
bazi-pro 缓存层 v4.6
Redis 优先，未配置时降级为内存 LRU dict
"""

import os
import json
import time
from collections import OrderedDict
from typing import Optional


class LRUDict:
    """简单的 LRU 字典实现"""

    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self._store: OrderedDict = OrderedDict()

    def get(self, key: str) -> Optional[dict]:
        if key in self._store:
            self._store.move_to_end(key)
            return self._store[key]
        return None

    def set(self, key: str, value: dict) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        while len(self._store) > self.maxsize:
            self._store.popitem(last=False)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


class CacheStore:
    """缓存封装：Redis（可选）或内存 LRU"""

    def __init__(self, redis_url: str = '', maxsize: int = 128):
        self._redis = None
        self._lru = LRUDict(maxsize=maxsize)

        if redis_url:
            self._init_redis(redis_url)

    def _init_redis(self, redis_url: str) -> None:
        try:
            import redis
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
        except Exception:
            self._redis = None

    def get(self, key: str) -> Optional[dict]:
        if self._redis:
            try:
                val = self._redis.get(key)
                return json.loads(val) if val else None
            except Exception:
                pass
        cached = self._lru.get(key)
        return cached

    def set(self, key: str, value: dict, ttl: int = 3600) -> None:
        if self._redis:
            try:
                self._redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
                return
            except Exception:
                pass
        self._lru.set(key, value)

    def delete(self, key: str) -> None:
        if self._redis:
            try:
                self._redis.delete(key)
                return
            except Exception:
                pass
        self._lru.delete(key)

    @property
    def backend(self) -> str:
        return 'redis' if self._redis else 'lru_memory'


# 单例
_cache_instance: Optional[CacheStore] = None


def get_cache() -> CacheStore:
    global _cache_instance
    if _cache_instance is None:
        redis_url = os.environ.get('REDIS_URL', '')
        _cache_instance = CacheStore(redis_url=redis_url)
    return _cache_instance
