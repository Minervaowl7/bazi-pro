#!/usr/bin/env python3

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger("bazi-pro.taskstore")


class TaskStore(ABC):

    @abstractmethod
    def create(self, run_id: str, data: dict) -> None:
        ...

    @abstractmethod
    def get(self, run_id: str) -> Optional[dict]:
        ...

    @abstractmethod
    def update(self, run_id: str, updates: dict) -> None:
        ...

    @abstractmethod
    def delete(self, run_id: str) -> None:
        ...

    @abstractmethod
    def count_by_status(self, status: str) -> int:
        ...

    @abstractmethod
    def cleanup_expired(self, ttl_seconds: int) -> int:
        ...


class MemoryTaskStore(TaskStore):

    def __init__(self):
        self._tasks: dict[str, dict] = {}

    def create(self, run_id: str, data: dict) -> None:
        self._tasks[run_id] = data

    def get(self, run_id: str) -> Optional[dict]:
        return self._tasks.get(run_id)

    def update(self, run_id: str, updates: dict) -> None:
        if run_id in self._tasks:
            self._tasks[run_id].update(updates)

    def delete(self, run_id: str) -> None:
        self._tasks.pop(run_id, None)

    def count_by_status(self, status: str) -> int:
        return sum(1 for t in self._tasks.values() if t.get("status") == status)

    def cleanup_expired(self, ttl_seconds: int) -> int:
        now = time.time()
        expired = [
            rid for rid, info in self._tasks.items()
            if now - info.get("_created_ts", 0) > ttl_seconds
        ]
        for rid in expired:
            self._tasks.pop(rid, None)
        return len(expired)

    def __len__(self) -> int:
        return len(self._tasks)

    def clear(self) -> None:
        self._tasks.clear()


class RedisTaskStore(TaskStore):

    def __init__(self, redis_url: str, key_prefix: str = "bazi:task:"):
        self._prefix = key_prefix
        self._redis = None
        try:
            import redis
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
        except Exception as e:
            logger.warning("RedisTaskStore init failed: %s, falling back to memory", e)
            self._redis = None
            self._fallback = MemoryTaskStore()

    @property
    def _store(self):
        if self._redis:
            return self._redis
        return self._fallback

    def _key(self, run_id: str) -> str:
        return f"{self._prefix}{run_id}"

    def create(self, run_id: str, data: dict) -> None:
        if self._redis:
            self._redis.set(self._key(run_id), json.dumps(data, ensure_ascii=False))
        else:
            self._fallback.create(run_id, data)

    def get(self, run_id: str) -> Optional[dict]:
        if self._redis:
            val = self._redis.get(self._key(run_id))
            return json.loads(val) if val else None
        return self._fallback.get(run_id)

    def update(self, run_id: str, updates: dict) -> None:
        if self._redis:
            current = self.get(run_id)
            if current:
                current.update(updates)
                self._redis.set(self._key(run_id), json.dumps(current, ensure_ascii=False))
        else:
            self._fallback.update(run_id, updates)

    def delete(self, run_id: str) -> None:
        if self._redis:
            self._redis.delete(self._key(run_id))
        else:
            self._fallback.delete(run_id)

    def count_by_status(self, status: str) -> int:
        if self._redis:
            count = 0
            for key in self._redis.scan_iter(f"{self._prefix}*"):
                val = self._redis.get(key)
                if val:
                    data = json.loads(val)
                    if data.get("status") == status:
                        count += 1
            return count
        return self._fallback.count_by_status(status)

    def cleanup_expired(self, ttl_seconds: int) -> int:
        if self._redis:
            now = time.time()
            expired = []
            for key in self._redis.scan_iter(f"{self._prefix}*"):
                val = self._redis.get(key)
                if val:
                    data = json.loads(val)
                    if now - data.get("_created_ts", 0) > ttl_seconds:
                        expired.append(key)
            for key in expired:
                self._redis.delete(key)
            return len(expired)
        return self._fallback.cleanup_expired(ttl_seconds)


def create_task_store() -> TaskStore:
    redis_url = os.environ.get("REDIS_URL", "")
    if redis_url:
        store = RedisTaskStore(redis_url)
        if store._redis:
            return store
    return MemoryTaskStore()
