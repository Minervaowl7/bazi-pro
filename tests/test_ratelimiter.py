#!/usr/bin/env python3
from unittest.mock import MagicMock

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
        assert rl.is_degraded is True
        assert rl.is_allowed("key1") is True
        rl.is_allowed("key1")
        assert rl.is_allowed("key1") is False

    def test_no_backend_denies_request(self):
        rl = RedisRateLimiter.__new__(RedisRateLimiter)
        rl._redis = None
        rl._fallback = None
        rl._degraded = True
        assert rl.is_allowed("key1") is False


class TestRedisRateLimiterPipeline:

    def test_pipeline_executes_once(self):
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [0, 0, True, True]
        mock_redis.pipeline.return_value = mock_pipe
        mock_redis.zrem.return_value = 1

        rl = RedisRateLimiter.__new__(RedisRateLimiter)
        rl._redis = mock_redis
        rl._fallback = None
        rl._degraded = False
        rl.max_requests = 5
        rl.window_seconds = 60
        rl._prefix = "bazi:rl:"

        result = rl.is_allowed("test-key")
        assert result is True
        mock_redis.pipeline.assert_called_once()
        mock_pipe.execute.assert_called_once()
        mock_pipe.zremrangebyscore.assert_called_once()
        mock_pipe.zcard.assert_called_once()
        mock_pipe.zadd.assert_called_once()
        mock_pipe.expire.assert_called_once()

    def test_pipeline_blocks_over_limit(self):
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [0, 5, True, True]
        mock_redis.pipeline.return_value = mock_pipe
        mock_redis.zrem.return_value = 1

        rl = RedisRateLimiter.__new__(RedisRateLimiter)
        rl._redis = mock_redis
        rl._fallback = None
        rl._degraded = False
        rl.max_requests = 5
        rl.window_seconds = 60
        rl._prefix = "bazi:rl:"

        result = rl.is_allowed("test-key")
        assert result is False
        mock_redis.zrem.assert_called_once()

    def test_pipeline_exception_falls_back_to_memory(self):
        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = Exception("connection lost")

        rl = RedisRateLimiter.__new__(RedisRateLimiter)
        rl._redis = mock_redis
        rl._fallback = MemoryRateLimiter(max_requests=2, window_seconds=60)
        rl._degraded = False
        rl.max_requests = 2
        rl.window_seconds = 60
        rl._prefix = "bazi:rl:"

        assert rl.is_allowed("key1") is True
        assert rl.is_degraded is True

    def test_unique_member_per_request(self):
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [0, 0, True, True]
        mock_redis.pipeline.return_value = mock_pipe

        rl = RedisRateLimiter.__new__(RedisRateLimiter)
        rl._redis = mock_redis
        rl._fallback = None
        rl._degraded = False
        rl.max_requests = 5
        rl.window_seconds = 60
        rl._prefix = "bazi:rl:"

        rl.is_allowed("key1")
        rl.is_allowed("key1")

        calls = mock_pipe.zadd.call_args_list
        assert len(calls) == 2
        member1 = list(calls[0][0][1].keys())[0]
        member2 = list(calls[1][0][1].keys())[0]
        assert member1 != member2


class TestCreateRateLimiter:

    def test_creates_memory_without_redis(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        rl = create_rate_limiter(max_requests=5, window_seconds=30)
        assert isinstance(rl, MemoryRateLimiter)

    def test_creates_redis_fallback_with_bad_url(self, monkeypatch):
        monkeypatch.setenv("REDIS_URL", "redis://nonexistent:6379/0")
        rl = create_rate_limiter(max_requests=5, window_seconds=30)
        assert isinstance(rl, MemoryRateLimiter)
