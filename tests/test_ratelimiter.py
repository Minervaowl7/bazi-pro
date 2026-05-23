#!/usr/bin/env python3

from server.ratelimiter import MemoryRateLimiter, RedisRateLimiter, create_rate_limiter


class TestMemoryRateLimiter:

    def test_allows_under_limit(self):
        rl = MemoryRateLimiter(max_requests=3, window_seconds=60)
        assert rl.is_allowed("key1") is True
        assert rl.is_allowed("key1") is True
        assert rl.is_allowed("key1") is True

    def test_blocks_over_limit(self):
        rl = MemoryRateLimiter(max_requests=2, window_seconds=60)
        rl.is_allowed("key1")
        rl.is_allowed("key1")
        assert rl.is_allowed("key1") is False

    def test_different_keys_independent(self):
        rl = MemoryRateLimiter(max_requests=1, window_seconds=60)
        assert rl.is_allowed("key1") is True
        assert rl.is_allowed("key2") is True
        assert rl.is_allowed("key1") is False
        assert rl.is_allowed("key2") is False

    def test_cleanup_removes_expired(self, monkeypatch):
        import time
        rl = MemoryRateLimiter(max_requests=1, window_seconds=10)
        rl.is_allowed("key1")
        future = time.time() + 20
        removed = rl.cleanup(future)
        assert removed >= 1
        assert rl.is_allowed("key1") is True

    def test_window_expiry(self, monkeypatch):
        import time
        rl = MemoryRateLimiter(max_requests=1, window_seconds=10)
        rl.is_allowed("key1")
        assert rl.is_allowed("key1") is False
        now = time.time()
        monkeypatch.setattr(time, "time", lambda: now + 11)
        assert rl.is_allowed("key1") is True


class TestRedisRateLimiterFallback:

    def test_falls_back_to_memory_on_bad_url(self):
        rl = RedisRateLimiter("redis://nonexistent:6379/0", max_requests=2, window_seconds=60)
        assert rl._redis is None
        assert rl._fallback is not None
        assert rl.is_allowed("key1") is True
        rl.is_allowed("key1")
        assert rl.is_allowed("key1") is False


class TestCreateRateLimiter:

    def test_creates_memory_without_redis(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        rl = create_rate_limiter(max_requests=5, window_seconds=30)
        assert isinstance(rl, MemoryRateLimiter)

    def test_creates_redis_fallback_with_bad_url(self, monkeypatch):
        monkeypatch.setenv("REDIS_URL", "redis://nonexistent:6379/0")
        rl = create_rate_limiter(max_requests=5, window_seconds=30)
        assert isinstance(rl, MemoryRateLimiter)
