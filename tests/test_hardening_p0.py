"""Acceptance tests for bazi-pro hardening spec (P0/P1).

P0-1: Task state / rate limiting / cache consistent with REDIS_URL + /api/health
P0-2: Cache key correctness (SHA-256, all fields, bazi:v5: prefix, [:24])
P0-3: Request size enforcement for streaming/chunked body
P1:   Unified API error response format
"""

import hashlib
import json
import time
from unittest.mock import MagicMock

try:
    import pytest
except ImportError:
    import sys
    print("pytest not installed. Skipping tests.", file=sys.stderr)
    sys.exit(0)
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    @pytest.fixture
    def client(self):
        from server.app import app
        return TestClient(app)

    def test_health_returns_version(self, client):
        resp = client.get("/api/health")
        body = resp.json()
        assert body["version"] == "5.0.0"

    def test_health_returns_cache_backend(self, client):
        resp = client.get("/api/health")
        body = resp.json()
        assert "cache_backend" in body

    def test_health_returns_task_store_backend(self, client):
        resp = client.get("/api/health")
        body = resp.json()
        assert "task_store_backend" in body

    def test_health_returns_rate_limiter_backend(self, client):
        resp = client.get("/api/health")
        body = resp.json()
        assert "rate_limiter_backend" in body

    def test_health_no_degraded_when_memory(self, client):
        resp = client.get("/api/health")
        body = resp.json()
        if body["task_store_backend"] == "memory" and body["rate_limiter_backend"] == "memory":
            assert "degraded" not in body


class TestCacheKeyCorrectness:
    def test_different_gender_different_key(self):
        from server.analysis import _make_cache_key
        data1 = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "性别": "男"}
        data2 = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "性别": "女"}
        key1 = _make_cache_key(data1, "standard")
        key2 = _make_cache_key(data2, "standard")
        assert key1 != key2

    def test_different_dayun_different_key(self):
        from server.analysis import _make_cache_key
        data1 = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "大运": [{"gan": "甲", "zhi": "辰", "age_range": "3-12"}]}
        data2 = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "大运": [{"gan": "乙", "zhi": "巳", "age_range": "3-12"}]}
        key1 = _make_cache_key(data1, "standard")
        key2 = _make_cache_key(data2, "standard")
        assert key1 != key2

    def test_same_payload_different_order_same_key(self):
        from server.analysis import _make_cache_key
        data1 = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "性别": "男"}
        data2 = {"性别": "男", "日主": "丁", "八字": "壬午 乙巳 丁亥 癸卯"}
        key1 = _make_cache_key(data1, "standard")
        key2 = _make_cache_key(data2, "standard")
        assert key1 == key2

    def test_key_prefix_bazi_v5(self):
        from server.analysis import _make_cache_key
        data = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"}
        key = _make_cache_key(data, "standard")
        assert key.startswith("bazi:v5:")

    def test_key_sha256_24_chars(self):
        from server.analysis import _make_cache_key
        data = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"}
        key = _make_cache_key(data, "standard")
        suffix = key[len("bazi:v5:"):]
        assert len(suffix) == 24

    def test_different_yangli_different_key(self):
        from server.analysis import _make_cache_key
        data1 = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "阳历": "2002-05-19"}
        data2 = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "阳历": "2002-06-19"}
        key1 = _make_cache_key(data1, "standard")
        key2 = _make_cache_key(data2, "standard")
        assert key1 != key2

    def test_different_nongli_different_key(self):
        from server.analysis import _make_cache_key
        data1 = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "农历": "壬午年四月初八"}
        data2 = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "农历": "壬午年五月初八"}
        key1 = _make_cache_key(data1, "standard")
        key2 = _make_cache_key(data2, "standard")
        assert key1 != key2

    def test_canonical_json_compact_separators(self):
        from server.analysis import _ANALYSIS_VERSION, _make_cache_key
        data = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "性别": "女"}
        payload = {
            "八字": "壬午 乙巳 丁亥 癸卯",
            "日主": "丁",
            "性别": "女",
            "阳历": "",
            "农历": "",
            "大运": [],
            "detail_level": "standard",
            "school": "ziping",
            "analysis_version": _ANALYSIS_VERSION,
        }
        expected_raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        expected_hash = hashlib.sha256(expected_raw.encode()).hexdigest()[:24]
        key = _make_cache_key(data, "standard")
        assert key == "bazi:v5:%s" % expected_hash


class TestRequestSizeLimit:
    @pytest.fixture
    def client(self):
        from server.app import app
        return TestClient(app, raise_server_exceptions=False)

    def test_content_length_too_large_returns_413(self, client):
        headers = {"Content-Length": str(999999)}
        resp = client.post("/api/analyze", content="{}", headers=headers)
        assert resp.status_code == 413

    def test_413_uses_unified_error_format(self, client):
        headers = {"Content-Length": str(999999)}
        resp = client.post("/api/analyze", content="{}", headers=headers)
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "PAYLOAD_TOO_LARGE"

    def test_normal_valid_request_works(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200


class TestTaskStoreMemory:
    def test_create_task(self):
        from server.taskstore import MemoryTaskStore
        store = MemoryTaskStore()
        store.create("t1", {"status": "queued", "_created_ts": time.time()})
        result = store.get("t1")
        assert result is not None
        assert result["status"] == "queued"

    def test_status_visible(self):
        from server.taskstore import MemoryTaskStore
        store = MemoryTaskStore()
        store.create("t1", {"status": "queued", "_created_ts": time.time()})
        assert store.get("t1")["status"] == "queued"

    def test_result_visible_after_completion(self):
        from server.taskstore import MemoryTaskStore
        store = MemoryTaskStore()
        store.create("t1", {"status": "queued", "_created_ts": time.time()})
        store.update("t1", {"status": "completed"})
        assert store.get("t1")["status"] == "completed"

    def test_expired_task_cleanup(self):
        from server.taskstore import MemoryTaskStore
        store = MemoryTaskStore()
        store.create("t1", {"status": "queued", "_created_ts": time.time() - 100})
        assert store.cleanup_expired(1) >= 1
        assert store.get("t1") is None

    def test_count_active_uses_queued_not_pending(self):
        from server.taskstore import MemoryTaskStore
        store = MemoryTaskStore()
        store.create("t1", {"status": "queued", "_created_ts": time.time()})
        store.create("t2", {"status": "running", "_created_ts": time.time()})
        assert store.count_active() == 2

    def test_count_running(self):
        from server.taskstore import MemoryTaskStore
        store = MemoryTaskStore()
        store.create("t1", {"status": "queued", "_created_ts": time.time()})
        store.create("t2", {"status": "running", "_created_ts": time.time()})
        assert store.count_running() == 1

    def test_delete_task(self):
        from server.taskstore import MemoryTaskStore
        store = MemoryTaskStore()
        store.create("t1", {"status": "queued", "_created_ts": time.time()})
        store.delete("t1")
        assert store.get("t1") is None


class TestTaskStoreRedisIndexSets:
    def test_create_uses_pipeline_with_index(self):
        from server.taskstore import RedisTaskStore
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [True, 1, 0]

        store = RedisTaskStore.__new__(RedisTaskStore)
        store._redis = mock_redis
        store._fallback = None
        store._degraded = False
        store._prefix = "bazi:task:"
        store._default_ttl = 7200

        store.create("t1", {"status": "queued"})

        mock_redis.pipeline.assert_called_once()
        mock_pipe.setex.assert_called_once()
        mock_pipe.sadd.assert_called()
        mock_pipe.execute.assert_called_once()

    def test_count_active_uses_redis_set(self):
        from server.taskstore import RedisTaskStore
        mock_redis = MagicMock()
        mock_redis.smembers.return_value = set()
        mock_redis.scard.return_value = 3

        store = RedisTaskStore.__new__(RedisTaskStore)
        store._redis = mock_redis
        store._fallback = None
        store._degraded = False

        count = store.count_active()
        assert count == 3
        mock_redis.scard.assert_called_once_with("bazi:task_index:active")

    def test_count_running_uses_redis_set(self):
        from server.taskstore import RedisTaskStore
        mock_redis = MagicMock()
        mock_redis.smembers.return_value = set()
        mock_redis.scard.return_value = 1

        store = RedisTaskStore.__new__(RedisTaskStore)
        store._redis = mock_redis
        store._fallback = None
        store._degraded = False

        count = store.count_running()
        assert count == 1
        mock_redis.scard.assert_called_once_with("bazi:task_index:running")

    def test_delete_removes_from_index(self):
        from server.taskstore import RedisTaskStore
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [1, 1, 0]

        store = RedisTaskStore.__new__(RedisTaskStore)
        store._redis = mock_redis
        store._fallback = None
        store._degraded = False
        store._prefix = "bazi:task:"

        store.delete("t1")
        mock_pipe.delete.assert_called_once()
        mock_pipe.srem.assert_any_call("bazi:task_index:active", "t1")
        mock_pipe.srem.assert_any_call("bazi:task_index:running", "t1")

    def test_completed_status_removes_from_index(self):
        from server.taskstore import RedisTaskStore
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [True, 0, 0]

        store = RedisTaskStore.__new__(RedisTaskStore)
        store._redis = mock_redis
        store._fallback = None
        store._degraded = False
        store._prefix = "bazi:task:"
        store._default_ttl = 7200

        store.create("t1", {"status": "completed"})
        mock_pipe.srem.assert_any_call("bazi:task_index:active", "t1")
        mock_pipe.srem.assert_any_call("bazi:task_index:running", "t1")

    def test_reconcile_removes_stale_entries(self):
        from server.taskstore import RedisTaskStore
        mock_redis = MagicMock()
        mock_redis.smembers.return_value = {"t1", "t2"}
        mock_redis.exists.side_effect = [True, False]

        store = RedisTaskStore.__new__(RedisTaskStore)
        store._redis = mock_redis
        store._fallback = None
        store._degraded = False
        store._prefix = "bazi:task:"

        removed = store._reconcile_index("bazi:task_index:active")
        assert removed == 1
        mock_redis.srem.assert_called()


class TestStatusVocabulary:
    def test_queued_is_active_status(self):
        from server.taskstore import _ACTIVE_STATUSES
        assert "queued" in _ACTIVE_STATUSES

    def test_pending_not_in_active_statuses(self):
        from server.taskstore import _ACTIVE_STATUSES
        assert "pending" not in _ACTIVE_STATUSES

    def test_running_is_active_status(self):
        from server.taskstore import _ACTIVE_STATUSES
        assert "running" in _ACTIVE_STATUSES

    def test_completed_not_in_active(self):
        from server.taskstore import _ACTIVE_STATUSES
        assert "completed" not in _ACTIVE_STATUSES


class TestUnifiedErrorResponse:
    @pytest.fixture
    def client(self):
        from server.app import app
        return TestClient(app, raise_server_exceptions=False)

    def test_404_uses_unified_format(self, client):
        resp = client.get("/api/status/nonexistent_run_id")
        body = resp.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]
        assert body["error"]["code"] == "NOT_FOUND"

    def test_422_validation_error_uses_unified_format(self, client):
        resp = client.post("/api/analyze", json={"bad": "data"})
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "VALIDATION_ERROR"

    def test_429_uses_unified_format(self, client):
        from server.deps import rate_limiter
        original = rate_limiter.is_allowed
        rate_limiter.is_allowed = lambda key: False
        try:
            resp = client.get("/api/health")
            body = resp.json()
            assert "error" in body
            assert body["error"]["code"] == "RATE_LIMITED"
        finally:
            rate_limiter.is_allowed = original


class TestRateLimiterKeyIncludesApiKey:
    def test_rate_limit_middleware_combines_ip_and_key(self):
        from server.ratelimiter import MemoryRateLimiter
        limiter = MemoryRateLimiter(max_requests=1, window_seconds=60)

        limiter.is_allowed("192.168.1.1:key-a")
        assert limiter.is_allowed("192.168.1.1:key-a") is False
        assert limiter.is_allowed("192.168.1.1:key-b") is True
        assert limiter.is_allowed("192.168.1.2") is True


class TestNoDirectAnalysisTasksReference:
    def test_app_does_not_use_analysis_tasks_dict(self):
        import inspect

        from server import app as app_module
        source = inspect.getsource(app_module)
        assert "_analysis_tasks" not in source
