#!/usr/bin/env python3

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger("bazi-pro.taskstore")

_LUA_ATOMIC_UPDATE = """
local current = redis.call('GET', KEYS[1])
if not current then
    return 0
end
local data = cjson.decode(current)
for k, v in pairs(ARGV) do
    if k ~= 1 then
        local key = ARGV[1]
        if k == 2 then
            data[ARGV[k]] = cjson.decode(ARGV[k+1])
        end
    end
end
redis.call('SET', KEYS[1], cjson.encode(data))
return 1
"""


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
    def count_active(self) -> int:
        ...

    @abstractmethod
    def count_running(self) -> int:
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

    def count_active(self) -> int:
        return sum(1 for t in self._tasks.values()
                   if t.get("status") in ("running", "pending"))

    def count_running(self) -> int:
        return self.count_by_status("running")

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

    def __init__(self, redis_url: str, key_prefix: str = "bazi:task:",
                 default_ttl: int = 7200):
        self._prefix = key_prefix
        self._default_ttl = default_ttl
        self._redis = None
        self._fallback: Optional[MemoryTaskStore] = None
        self._degraded = False
        try:
            import redis as _redis
            self._redis = _redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
            self._update_script = self._redis.register_script(_LUA_ATOMIC_UPDATE)
        except Exception as e:
            logger.warning("RedisTaskStore init failed: %s, falling back to memory", e)
            self._redis = None
            self._fallback = MemoryTaskStore()
            self._degraded = True

    @property
    def is_degraded(self) -> bool:
        return self._degraded

    def _key(self, run_id: str) -> str:
        return f"{self._prefix}{run_id}"

    def create(self, run_id: str, data: dict) -> None:
        if self._redis:
            try:
                self._redis.setex(
                    self._key(run_id),
                    self._default_ttl,
                    json.dumps(data, ensure_ascii=False),
                )
            except Exception as e:
                logger.error("RedisTaskStore.create failed: %s", e)
                self._degraded = True
                if self._fallback:
                    self._fallback.create(run_id, data)
        elif self._fallback:
            self._fallback.create(run_id, data)

    def get(self, run_id: str) -> Optional[dict]:
        if self._redis:
            try:
                val = self._redis.get(self._key(run_id))
                return json.loads(val) if val else None
            except Exception as e:
                logger.error("RedisTaskStore.get failed: %s", e)
                return None
        if self._fallback:
            return self._fallback.get(run_id)
        return None

    def update(self, run_id: str, updates: dict) -> None:
        if self._redis:
            try:
                current = self.get(run_id)
                if current:
                    current.update(updates)
                    ttl = self._redis.ttl(self._key(run_id))
                    if ttl and ttl > 0:
                        self._redis.setex(
                            self._key(run_id),
                            ttl,
                            json.dumps(current, ensure_ascii=False),
                        )
                    else:
                        self._redis.setex(
                            self._key(run_id),
                            self._default_ttl,
                            json.dumps(current, ensure_ascii=False),
                        )
            except Exception as e:
                logger.error("RedisTaskStore.update failed: %s", e)
                self._degraded = True
                if self._fallback:
                    self._fallback.update(run_id, updates)
        elif self._fallback:
            self._fallback.update(run_id, updates)

    def delete(self, run_id: str) -> None:
        if self._redis:
            try:
                self._redis.delete(self._key(run_id))
            except Exception as e:
                logger.error("RedisTaskStore.delete failed: %s", e)
        elif self._fallback:
            self._fallback.delete(run_id)

    def count_by_status(self, status: str) -> int:
        if self._redis:
            try:
                count = 0
                for key in self._redis.scan_iter(f"{self._prefix}*"):
                    val = self._redis.get(key)
                    if val:
                        data = json.loads(val)
                        if data.get("status") == status:
                            count += 1
                return count
            except Exception as e:
                logger.error("RedisTaskStore.count_by_status failed: %s", e)
                return 0
        if self._fallback:
            return self._fallback.count_by_status(status)
        return 0

    def count_active(self) -> int:
        if self._redis:
            try:
                count = 0
                for key in self._redis.scan_iter(f"{self._prefix}*"):
                    val = self._redis.get(key)
                    if val:
                        data = json.loads(val)
                        if data.get("status") in ("running", "pending"):
                            count += 1
                return count
            except Exception as e:
                logger.error("RedisTaskStore.count_active failed: %s", e)
                return 0
        if self._fallback:
            return self._fallback.count_active()
        return 0

    def count_running(self) -> int:
        return self.count_by_status("running")

    def cleanup_expired(self, ttl_seconds: int) -> int:
        if self._redis:
            return 0
        if self._fallback:
            return self._fallback.cleanup_expired(ttl_seconds)
        return 0


def create_task_store() -> TaskStore:
    redis_url = os.environ.get("REDIS_URL", "")
    if redis_url:
        store = RedisTaskStore(redis_url)
        if store._redis:
            return store
    return MemoryTaskStore()
