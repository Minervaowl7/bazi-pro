#!/usr/bin/env python3
import pytest
import time
from pydantic import ValidationError

from server.schemas import BaziAnalysisRequest, BaziPillars, DayunItem


class TestBaziAnalysisRequestValidation:

    def test_valid_request(self):
        req = BaziAnalysisRequest(性别='女', 八字='壬午 乙巳 丁亥 癸卯', 日主='丁')
        assert req.八字 == '壬午 乙巳 丁亥 癸卯'
        assert req.日主 == '丁'
        assert req.性别 == '女'
        assert req.detail_level == 'standard'

    def test_invalid_bazi_format(self):
        with pytest.raises(ValidationError, match='八字格式不合法'):
            BaziAnalysisRequest(性别='女', 八字='abc', 日主='丁')

    def test_invalid_bazi_too_few_pillars(self):
        with pytest.raises(ValidationError, match='八字格式不合法'):
            BaziAnalysisRequest(性别='女', 八字='壬午 乙巳', 日主='丁')

    def test_invalid_bazi_wrong_gan(self):
        with pytest.raises(ValidationError, match='八字格式不合法'):
            BaziAnalysisRequest(性别='女', 八字='X午 乙巳 丁亥 癸卯', 日主='丁')

    def test_invalid_bazi_wrong_zhi(self):
        with pytest.raises(ValidationError, match='八字格式不合法'):
            BaziAnalysisRequest(性别='女', 八字='壬X 乙巳 丁亥 癸卯', 日主='丁')

    def test_invalid_day_master(self):
        with pytest.raises(ValidationError, match='日主.*不合法'):
            BaziAnalysisRequest(性别='女', 八字='壬午 乙巳 丁亥 癸卯', 日主='X')

    def test_invalid_gender(self):
        with pytest.raises(ValidationError, match='性别必须为'):
            BaziAnalysisRequest(性别='unknown', 八字='壬午 乙巳 丁亥 癸卯', 日主='丁')

    def test_valid_gender_options(self):
        for g in ('男', '女', '其他'):
            req = BaziAnalysisRequest(性别=g, 八字='壬午 乙巳 丁亥 癸卯', 日主='丁')
            assert req.性别 == g

    def test_detail_level_default(self):
        req = BaziAnalysisRequest(性别='女', 八字='壬午 乙巳 丁亥 癸卯', 日主='丁')
        assert req.detail_level == 'standard'

    def test_detail_level_options(self):
        for level in ('standard', 'detailed', 'brief'):
            req = BaziAnalysisRequest(
                性别='女', 八字='壬午 乙巳 丁亥 癸卯', 日主='丁',
                detail_level=level,
            )
            assert req.detail_level == level

    def test_invalid_detail_level(self):
        with pytest.raises(ValidationError):
            BaziAnalysisRequest(
                性别='女', 八字='壬午 乙巳 丁亥 癸卯', 日主='丁',
                detail_level='super',
            )

    def test_bazi_whitespace_trimmed(self):
        req = BaziAnalysisRequest(性别='女', 八字='  壬午 乙巳 丁亥 癸卯  ', 日主='丁')
        assert req.八字 == '壬午 乙巳 丁亥 癸卯'

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            BaziAnalysisRequest(八字='壬午 乙巳 丁亥 癸卯', 日主='丁')

    def test_optional_fields(self):
        req = BaziAnalysisRequest(
            性别='女', 八字='壬午 乙巳 丁亥 癸卯', 日主='丁',
            阳历='2002-05-19', 农历='壬午年四月初八', 生肖='马',
        )
        assert req.阳历 == '2002-05-19'
        assert req.生肖 == '马'

    def test_valid_dayun(self):
        req = BaziAnalysisRequest(
            性别='女', 八字='壬午 乙巳 丁亥 癸卯', 日主='丁',
            大运=[{'gan': '甲', 'zhi': '寅'}, {'gan': '乙', 'zhi': '卯'}],
        )
        assert len(req.大运) == 2
        assert req.大运[0].gan == '甲'
        assert req.大运[0].zhi == '寅'

    def test_invalid_dayun_gan(self):
        with pytest.raises(ValidationError, match='大运天干'):
            BaziAnalysisRequest(
                性别='女', 八字='壬午 乙巳 丁亥 癸卯', 日主='丁',
                大运=[{'gan': 'X', 'zhi': '寅'}],
            )

    def test_invalid_dayun_zhi(self):
        with pytest.raises(ValidationError, match='大运地支'):
            BaziAnalysisRequest(
                性别='女', 八字='壬午 乙巳 丁亥 癸卯', 日主='丁',
                大运=[{'gan': '甲', 'zhi': 'X'}],
            )

    def test_dayun_max_length(self):
        items = [{'gan': '甲', 'zhi': '寅'}] * 13
        with pytest.raises(ValidationError):
            BaziAnalysisRequest(
                性别='女', 八字='壬午 乙巳 丁亥 癸卯', 日主='丁',
                大运=items,
            )


class TestDayunItemValidation:

    def test_valid_dayun_item(self):
        item = DayunItem(gan='甲', zhi='寅')
        assert item.gan == '甲'
        assert item.zhi == '寅'

    def test_dayun_item_with_age_range(self):
        item = DayunItem(gan='乙', zhi='卯', age_range='3-12')
        assert item.age_range == '3-12'

    def test_dayun_item_invalid_gan(self):
        with pytest.raises(ValidationError, match='大运天干'):
            DayunItem(gan='X', zhi='寅')

    def test_dayun_item_invalid_zhi(self):
        with pytest.raises(ValidationError, match='大运地支'):
            DayunItem(gan='甲', zhi='X')


class TestBaziPillarsValidation:

    def test_valid_pillars(self):
        p = BaziPillars(year='壬午', month='乙巳', day='丁亥', hour='癸卯')
        assert p.to_bazi_string() == '壬午 乙巳 丁亥 癸卯'

    def test_invalid_gan_in_pillar(self):
        with pytest.raises(ValidationError, match='天干.*不合法'):
            BaziPillars(year='X午', month='乙巳', day='丁亥', hour='癸卯')

    def test_invalid_zhi_in_pillar(self):
        with pytest.raises(ValidationError, match='地支.*不合法'):
            BaziPillars(year='壬X', month='乙巳', day='丁亥', hour='癸卯')

    def test_pillar_too_short(self):
        with pytest.raises(ValidationError):
            BaziPillars(year='壬', month='乙巳', day='丁亥', hour='癸卯')


class TestCacheDegradedMode:

    def test_lru_backend(self):
        from server.cache import CacheStore
        store = CacheStore(redis_url='')
        assert store.backend == 'lru_memory'
        assert store.degraded_reason == ''

    def test_lru_set_get(self):
        from server.cache import CacheStore
        store = CacheStore(redis_url='')
        store.set('test_key', {'value': 42}, ttl=60)
        result = store.get('test_key')
        assert result == {'value': 42}

    def test_lru_ttl_expiry(self):
        from server.cache import CacheStore
        store = CacheStore(redis_url='')
        store.set('exp_key', {'value': 1}, ttl=1)
        time.sleep(1.1)
        result = store.get('exp_key')
        assert result is None

    def test_redis_degraded_reason(self):
        from server.cache import CacheStore
        store = CacheStore(redis_url='redis://nonexistent:6379/0')
        assert store.backend == 'lru_memory'
        assert store.degraded_reason != ''

    def test_lru_eviction(self):
        from server.cache import CacheStore
        store = CacheStore(redis_url='', maxsize=3)
        for i in range(5):
            store.set(f'key_{i}', {'v': i}, ttl=60)
        assert store.get('key_0') is None
        assert store.get('key_4') is not None


class TestAppEndpoints:

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from server.app import app
        return TestClient(app)

    def test_index_page(self, client):
        resp = client.get('/')
        assert resp.status_code == 200
        assert 'bazi-pro' in resp.text

    def test_analyze_valid(self, client):
        resp = client.post('/api/analyze', json={
            '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
        })
        assert resp.status_code == 200
        data = resp.json()
        assert 'run_id' in data
        assert len(data['run_id']) == 32
        assert data['status'] == 'queued'

    def test_analyze_with_dayun(self, client):
        resp = client.post('/api/analyze', json={
            '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
            '大运': [{'gan': '甲', 'zhi': '寅', 'age_range': '3-12'}],
        })
        assert resp.status_code == 200

    def test_analyze_invalid_bazi(self, client):
        resp = client.post('/api/analyze', json={
            '性别': '女', '八字': 'invalid', '日主': '丁',
        })
        assert resp.status_code == 422

    def test_analyze_invalid_day_master(self, client):
        resp = client.post('/api/analyze', json={
            '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': 'X',
        })
        assert resp.status_code == 422

    def test_analyze_missing_field(self, client):
        resp = client.post('/api/analyze', json={
            '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
        })
        assert resp.status_code == 422

    def test_status_not_found(self, client):
        resp = client.get('/api/status/nonexistent')
        assert resp.status_code == 404

    def test_result_not_found(self, client):
        resp = client.get('/api/result/nonexistent')
        assert resp.status_code == 404

    def test_api_key_enforced(self, client):
        import os
        import importlib
        import server.app as app_module
        original = os.environ.get('BAZI_API_KEY', '')
        os.environ['BAZI_API_KEY'] = 'test-secret-key'
        try:
            importlib.reload(app_module)
            from fastapi.testclient import TestClient
            fresh_client = TestClient(app_module.app)
            resp = fresh_client.post('/api/analyze', json={
                '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
            })
            assert resp.status_code == 401
            resp = fresh_client.post('/api/analyze', json={
                '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
            }, headers={'X-API-Key': 'wrong-key'})
            assert resp.status_code == 401
            resp = fresh_client.post('/api/analyze', json={
                '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
            }, headers={'X-API-Key': 'test-secret-key'})
            assert resp.status_code == 200
        finally:
            os.environ['BAZI_API_KEY'] = original
            importlib.reload(app_module)

    def test_request_too_large(self, client):
        big_payload = {
            '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
            '阳历': 'x' * 20000,
        }
        resp = client.post('/api/analyze', json=big_payload)
        assert resp.status_code == 413

    def test_max_concurrent_tasks(self, client):
        import os
        import importlib
        import server.app as app_module
        original_max = app_module._MAX_CONCURRENT_TASKS
        app_module._MAX_CONCURRENT_TASKS = 2
        app_module._analysis_tasks.clear()
        try:
            for i in range(2):
                app_module._analysis_tasks[f'filler-{i}'] = {
                    'status': 'running', '_created_ts': time.time()
                }
            count_before = len(app_module._analysis_tasks)
            resp = client.post('/api/analyze', json={
                '性别': '女', '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁',
            })
            assert resp.status_code == 503
            assert len(app_module._analysis_tasks) == count_before
        finally:
            app_module._MAX_CONCURRENT_TASKS = original_max
            app_module._analysis_tasks.clear()

    def test_ws_api_key_rejected(self, client):
        import os
        import importlib
        import server.app as app_module
        original = os.environ.get('BAZI_API_KEY', '')
        os.environ['BAZI_API_KEY'] = 'ws-test-key'
        try:
            importlib.reload(app_module)
            from fastapi.testclient import TestClient
            fresh_client = TestClient(app_module.app)
            with fresh_client.websocket_connect('/ws/test-run-id') as ws:
                msg = ws.receive()
                assert msg['type'] == 'websocket.close'
                assert msg['code'] == 4001
        finally:
            os.environ['BAZI_API_KEY'] = original
            importlib.reload(app_module)

    def test_cors_disabled_by_default(self, client):
        resp = client.options('/api/analyze', headers={
            'Origin': 'http://evil.com',
            'Access-Control-Request-Method': 'POST',
        })
        assert 'access-control-allow-origin' not in resp.headers

    def test_status_strips_internal_fields(self, client):
        import server.app as app_module
        run_id = 'test-internal-strip'
        app_module._analysis_tasks[run_id] = {
            'status': 'running',
            '_created_ts': time.time(),
            '_secret': 'hidden',
            'visible_field': 'ok',
        }
        try:
            resp = client.get(f'/api/status/{run_id}')
            data = resp.json()
            assert 'visible_field' in data
            assert '_created_ts' not in data
            assert '_secret' not in data
        finally:
            app_module._analysis_tasks.pop(run_id, None)
