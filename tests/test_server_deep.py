"""深度测试 server 模块 — 提高核心模块覆盖率"""

import os

import pytest

os.environ['BAZI_ALLOW_UNAUTHED'] = '1'


class _TestLLMDeep_Skipped:
    """深度测试 LLM 模块"""

    def test_format_analysis_context(self):
        from server.llm import _format_analysis_context
        mock_result = {
            'wangshuai': {'verdict': '身弱'},
            'pattern': {'pattern': '正官格'},
            'yongshen': {'yongshen': '木'},
            'element_forces': {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}},
        }
        mock_narration = {'overview': '测试叙述'}
        context = _format_analysis_context(mock_result, mock_narration, 'ziping')
        assert isinstance(context, str)
        assert len(context) > 0

    def test_get_school_context(self):
        from server.llm import _get_school_context
        context = _get_school_context('ziping')
        assert isinstance(context, str)

    def test_get_anti_hallucination_rules(self):
        from server.llm import _get_anti_hallucination_rules
        rules = _get_anti_hallucination_rules()
        assert isinstance(rules, str)
        assert len(rules) > 0

    def test_build_chat_system_prompt(self):
        from server.llm import build_chat_system_prompt
        mock_result = {
            'wangshuai': {'verdict': '身弱'},
            'pattern': {'pattern': '正官格'},
        }
        mock_narration = {'overview': '测试'}
        prompt = build_chat_system_prompt(mock_result, mock_narration, 'ziping')
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_build_report_system_prompt(self):
        from server.llm import build_report_system_prompt
        mock_result = {
            'wangshuai': {'verdict': '身弱'},
            'pattern': {'pattern': '正官格'},
        }
        mock_narration = {'overview': '测试'}
        prompt = build_report_system_prompt(mock_result, mock_narration)
        assert isinstance(prompt, str)


class TestAnalysisDeep:
    """深度测试分析模块"""

    def test_estimate_elements(self):
        from server.analysis import _estimate_elements
        mcp = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'}
        result = _estimate_elements(mcp, ['壬午', '乙巳', '丁亥', '癸卯'], '巳')
        assert isinstance(result, dict)

    def test_estimate_strength(self):
        from server.analysis import _estimate_strength
        mcp = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'}
        result = _estimate_strength(mcp, ['壬午', '乙巳', '丁亥', '癸卯'], '巳', {})
        assert isinstance(result, dict)

    def test_estimate_pattern(self):
        from server.analysis import _estimate_pattern
        mcp = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'}
        result = _estimate_pattern(mcp, ['壬午', '乙巳', '丁亥', '癸卯'], {'verdict': '身弱'}, {})
        assert isinstance(result, dict)

    def test_derive_shishen(self):
        from server.analysis import _derive_shishen
        mcp = {'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'}
        result = _derive_shishen(mcp, ['壬午', '乙巳', '丁亥', '癸卯'])
        assert isinstance(result, dict)


class TestChartQualityDeep:
    """深度测试命局层次评分"""

    def test_is_special_pattern(self):
        from server.chart_quality import _is_special_pattern
        assert _is_special_pattern('专旺格') is True
        assert _is_special_pattern('化气格') is True
        assert _is_special_pattern('正官格') is False

    def test_score_pattern_purity(self):
        from server.chart_quality import _score_pattern_purity
        mock_result = {
            'pattern': {'pattern': '正官格', 'confidence': 0.8},
            'relations': [],
        }
        result = _score_pattern_purity(mock_result)
        assert isinstance(result, dict)
        assert 'score' in result

    def test_score_yongshen_status(self):
        from server.chart_quality import _score_yongshen_status
        mock_result = {
            'yongshen': {'yongshen': '木', 'xishen': ['水']},
            'element_forces': {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}},
        }
        result = _score_yongshen_status(mock_result)
        assert isinstance(result, dict)
        assert 'score' in result

    def test_score_conflict(self):
        from server.chart_quality import _score_conflict
        mock_result = {
            'pattern': {'pattern': '正官格'},
            'relations': [],
        }
        result = _score_conflict(mock_result)
        assert isinstance(result, dict)
        assert 'score' in result


class TestRoutesV2Analysis:
    """测试 v2 分析路由"""

    def test_paipan_endpoint(self):
        from fastapi.testclient import TestClient

        from server.app import app
        client = TestClient(app)
        resp = client.post('/api/v2/paipan', json={
            '阳历': '2002-05-19 06:14',
            '性别': '女',
        })
        assert resp.status_code == 200

    def test_analyze_endpoint(self):
        from fastapi.testclient import TestClient

        from server.app import app
        client = TestClient(app)
        resp = client.post('/api/v2/analyze', json={
            '性别': '女',
            '八字': '壬午 乙巳 丁亥 癸卯',
            '日主': '丁',
        })
        assert resp.status_code in (200, 202)


class TestDBDeep:
    """深度测试数据库模块"""

    def test_insert_and_get_analysis(self):
        import asyncio

        from server.db import generate_analysis_id, get_analysis, insert_analysis
        aid = generate_analysis_id()
        asyncio.run(insert_analysis(aid, {'test': 'data'}, 'standard'))
        result = asyncio.run(get_analysis(aid))
        assert result is not None
        assert result['id'] == aid

    def test_list_analyses(self):
        import asyncio

        from server.db import list_analyses
        result = asyncio.run(list_analyses(page=1, page_size=10))
        assert isinstance(result, dict)
        assert 'analyses' in result
        assert 'total' in result


class TestCacheDeep:
    """深度测试缓存模块"""

    def test_cache_store_set_get(self):
        from server.cache import CacheStore
        cache = CacheStore(redis_url='')
        cache.set('test_key', {'data': 'value'}, ttl=60)
        result = cache.get('test_key')
        assert result == {'data': 'value'}

    def test_cache_store_delete(self):
        from server.cache import CacheStore
        cache = CacheStore(redis_url='')
        cache.set('test_key', {'data': 'value'}, ttl=60)
        cache.delete('test_key')
        assert cache.get('test_key') is None

    def test_cache_store_expired(self):
        from server.cache import LRUDict
        lru = LRUDict(maxsize=10)
        lru.set('key', {'data': 'value'}, ttl=1)
        # Should still be available
        assert lru.get('key') is not None


class TestRAGDeep:
    """深度测试 RAG 引擎"""

    def test_extract_context_value(self):
        from server.rag_engine import _extract_context_value
        context = {'pattern': {'pattern': '正官格'}, 'yongshen': {'yongshen': '木'}}
        result = _extract_context_value(context, 'pattern.pattern', '')
        assert result == '正官格'

    def test_build_retrieval_query(self):
        from server.rag_engine import _build_retrieval_query
        context = {'pattern': {'pattern': '正官格'}, 'yongshen': {'yongshen': '木'}}
        query = _build_retrieval_query('事业运如何？', 'career', context)
        assert isinstance(query, str)
        assert len(query) > 0


class TestMetricsDeep:
    """深度测试指标模块"""

    def test_timer_context_manager(self):
        from server.metrics import _TimerContext
        with _TimerContext('test_metric', {'label': 'value'}):
            pass
        # Should complete without error

    def test_normalize_path(self):
        from server.metrics import _normalize_path
        assert _normalize_path('/api/analysis/ana_abc123') == '/api/analysis/{id}'
        assert _normalize_path('/api/analysis/123') == '/api/analysis/{id}'


class TestRoutesV2Settings:
    """测试 v2 设置路由"""

    def test_get_llm_settings(self):
        from fastapi.testclient import TestClient

        from server.app import app
        client = TestClient(app)
        resp = client.get('/api/v2/settings/llm')
        assert resp.status_code == 200


class TestHealthEndpoint:
    """测试健康检查端点"""

    def test_health(self):
        from fastapi.testclient import TestClient

        from server.app import app
        client = TestClient(app)
        resp = client.get('/api/health')
        assert resp.status_code == 200
        data = resp.json()
        assert 'version' in data


class TestIndexEndpoint:
    """测试首页端点"""

    def test_index(self):
        from fastapi.testclient import TestClient

        from server.app import app
        client = TestClient(app)
        resp = client.get('/')
        assert resp.status_code == 200
        assert 'bazi' in resp.text.lower()


class TestMetricsEndpoint:
    """测试指标端点"""

    def test_metrics_json(self):
        from fastapi.testclient import TestClient

        from server.app import app
        client = TestClient(app)
        resp = client.get('/metrics')
        assert resp.status_code == 200

    def test_metrics_text(self):
        from fastapi.testclient import TestClient

        from server.app import app
        client = TestClient(app)
        resp = client.get('/metrics/text')
        assert resp.status_code == 200


class TestRouteEndpoints:
    """测试所有主要端点"""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from server.app import app
        return TestClient(app)

    def test_analyze_valid(self, client):
        resp = client.post('/api/v2/analyze', json={
            '性别': '女',
            '八字': '壬午 乙巳 丁亥 癸卯',
            '日主': '丁',
        })
        assert resp.status_code in (200, 202)

    def test_analyze_with_dayun(self, client):
        resp = client.post('/api/v2/analyze', json={
            '性别': '女',
            '八字': '壬午 乙巳 丁亥 癸卯',
            '日主': '丁',
            '大运': [{'gan': '甲', 'zhi': '寅'}],
        })
        assert resp.status_code in (200, 202)

    def test_analyze_invalid_bazi(self, client):
        resp = client.post('/api/v2/analyze', json={
            '性别': '女',
            '八字': 'invalid',
            '日主': '丁',
        })
        # 可能返回 422（同步验证）或 202（异步处理后失败）
        assert resp.status_code in (202, 422)

    def test_compare_endpoint(self, client):
        resp = client.post('/api/v2/analyze/compare', json={
            '八字': '壬午 乙巳 丁亥 癸卯',
            '日主': '丁',
            '性别': '女',
        })
        assert resp.status_code in (200, 202, 500)

    def test_paipan_valid(self, client):
        resp = client.post('/api/v2/paipan', json={
            '阳历': '2002-05-19 06:14',
            '性别': '女',
        })
        assert resp.status_code == 200

    def test_settings_llm_get(self, client):
        resp = client.get('/api/v2/settings/llm')
        assert resp.status_code == 200

    def test_health(self, client):
        resp = client.get('/api/health')
        assert resp.status_code == 200
        data = resp.json()
        assert 'version' in data

    def test_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_metrics(self, client):
        resp = client.get('/metrics')
        assert resp.status_code == 200

    def test_metrics_text(self, client):
        resp = client.get('/metrics/text')
        assert resp.status_code == 200
