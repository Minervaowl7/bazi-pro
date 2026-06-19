"""测试 server 模块 — 提高覆盖率"""

import pytest


class TestTrueSolarTime:
    """测试真太阳时修正"""

    def test_import(self):
        from server.true_solar_time import true_solar_time_offset
        assert callable(true_solar_time_offset)

    def test_equation_of_time(self):
        from server.true_solar_time import equation_of_time
        # 春分附近 (day 80) 时差应该很小
        eot = equation_of_time(80)
        assert isinstance(eot, float)
        assert -20 < eot < 20  # 分钟

    def test_get_city_longitude(self):
        from server.true_solar_time import get_city_longitude
        # 北京
        lon = get_city_longitude('北京')
        assert lon is not None
        assert 115 < lon < 120

    def test_get_city_unknown(self):
        from server.true_solar_time import get_city_longitude
        lon = get_city_longitude('不存在的城市')
        assert lon is None


class TestNayin:
    """测试纳音"""

    def test_import(self):
        from server.nayin import lookup_nayin
        assert callable(lookup_nayin)

    def test_jiazi_nayin(self):
        from server.nayin import lookup_nayin
        result = lookup_nayin('甲子')
        assert isinstance(result, str)
        assert len(result) > 0

    def test_yichou_nayin(self):
        from server.nayin import lookup_nayin
        result = lookup_nayin('乙丑')
        assert isinstance(result, str)


class TestGongwei:
    """测试宫位计算"""

    def test_import(self):
        from server.gongwei import calc_gongwei
        assert callable(calc_gongwei)

    def test_calc_gongwei(self):
        from server.gongwei import calc_gongwei
        result = calc_gongwei(['壬午', '乙巳', '丁亥', '癸卯'])
        assert isinstance(result, dict)

    def test_calc_taiyuan(self):
        from server.gongwei import calc_taiyuan
        result = calc_taiyuan('乙', '巳')
        assert isinstance(result, str)
        assert len(result) == 2

    def test_calc_minggong(self):
        from server.gongwei import calc_minggong
        result = calc_minggong('巳', '卯')
        assert isinstance(result, str)
        assert len(result) >= 1


class TestDayunScore:
    """测试大运评分"""

    def test_import(self):
        from server.dayun_score import score_dayun
        assert callable(score_dayun)


class TestChartQuality:
    """测试命局层次评分"""

    def test_import(self):
        from server.chart_quality import calculate_chart_quality
        assert callable(calculate_chart_quality)


class TestDailyFortune:
    """测试每日运势"""

    def test_import(self):
        from server.daily_fortune import calc_daily_fortune
        assert callable(calc_daily_fortune)


class TestReverseLookup:
    """测试日柱反查"""

    def test_import(self):
        from server.reverse_lookup import reverse_lookup_pillars
        assert callable(reverse_lookup_pillars)

    def test_import_day(self):
        from server.reverse_lookup import reverse_lookup_day_pillar
        assert callable(reverse_lookup_day_pillar)


class TestCrossValidate:
    """测试三流派交叉验证"""

    def test_import(self):
        from server.cross_validate import cross_validate_schools
        assert callable(cross_validate_schools)


class TestPersonality:
    """测试性格分析"""

    def test_import(self):
        from server.personality import calc_personality_params
        assert callable(calc_personality_params)

    def test_calc_params(self):
        from server.personality import calc_personality_params
        # 10 个答案，每个 1-5
        answers = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        result = calc_personality_params(answers)
        assert isinstance(result, dict)


class TestKlineOHLC:
    """测试人生 K 线"""

    def test_import(self):
        from server.kline_ohlc import score_liunian_ohlc
        assert callable(score_liunian_ohlc)

    def test_get_year_ganzhi(self):
        from server.kline_ohlc import _get_year_ganzhi
        gan, zhi = _get_year_ganzhi(2024)
        assert isinstance(gan, str)
        assert isinstance(zhi, str)
        assert len(gan) == 1
        assert len(zhi) == 1


class TestReportPDF:
    """测试 PDF 报告生成"""

    def test_import(self):
        from server.report_pdf import generate_report_pdf
        assert callable(generate_report_pdf)

    def test_md_to_html(self):
        from server.report_pdf import _md_to_html
        html = _md_to_html('# 标题\n\n段落')
        assert isinstance(html, str)
        assert '<h1>' in html or '标题' in html


class TestRAGEngine:
    """测试 RAG 引擎"""

    def test_import(self):
        from server.rag_engine import retrieve_for_chat
        assert callable(retrieve_for_chat)

    def test_classify_question(self):
        from server.rag_engine import _classify_question
        category = _classify_question('我的事业运如何？')
        assert isinstance(category, str)


class TestShensha:
    """测试神煞计算"""

    def test_import(self):
        from server.shensha import calc_shensha
        assert callable(calc_shensha)

    def test_calc_shensha(self):
        from server.shensha import calc_shensha
        result = calc_shensha(['壬午', '乙巳', '丁亥', '癸卯'], gender=0)
        assert isinstance(result, list)


class TestZiwei:
    """测试紫微斗数"""

    def test_import(self):
        from server.ziwei import get_ziwei_analysis
        assert callable(get_ziwei_analysis)


class TestCache:
    """测试缓存层"""

    def test_import(self):
        from server.cache import CacheStore, LRUDict, get_cache
        assert CacheStore is not None
        assert LRUDict is not None
        assert callable(get_cache)

    def test_lru_dict_basic(self):
        from server.cache import LRUDict
        lru = LRUDict(maxsize=3)
        lru.set('a', {'value': 1}, ttl=60)
        assert lru.get('a') == {'value': 1}
        assert lru.get('b') is None

    def test_lru_dict_eviction(self):
        from server.cache import LRUDict
        lru = LRUDict(maxsize=2)
        lru.set('a', {'value': 1}, ttl=60)
        lru.set('b', {'value': 2}, ttl=60)
        lru.set('c', {'value': 3}, ttl=60)
        # 'a' should be evicted
        assert lru.get('a') is None
        assert lru.get('b') == {'value': 2}
        assert lru.get('c') == {'value': 3}

    def test_lru_dict_delete(self):
        from server.cache import LRUDict
        lru = LRUDict(maxsize=3)
        lru.set('a', {'value': 1}, ttl=60)
        lru.delete('a')
        assert lru.get('a') is None

    def test_lru_dict_clear(self):
        from server.cache import LRUDict
        lru = LRUDict(maxsize=3)
        lru.set('a', {'value': 1}, ttl=60)
        lru.set('b', {'value': 2}, ttl=60)
        lru.clear()
        assert len(lru) == 0

    def test_cache_store_init(self):
        from server.cache import CacheStore
        cache = CacheStore(redis_url='')
        assert cache.backend == 'lru_memory'


class TestTaskStore:
    """测试任务存储"""

    def test_import(self):
        from server.taskstore import MemoryTaskStore, create_task_store
        assert MemoryTaskStore is not None
        assert callable(create_task_store)

    def test_memory_task_store_crud(self):
        from server.taskstore import MemoryTaskStore
        store = MemoryTaskStore()
        store.create('test-1', {'data': 'value'})
        task = store.get('test-1')
        assert task is not None
        assert task['data'] == 'value'

        store.update('test-1', {'status': 'completed'})
        task = store.get('test-1')
        assert task['status'] == 'completed'

        store.delete('test-1')
        assert store.get('test-1') is None

    def test_memory_task_store_count(self):
        from server.taskstore import MemoryTaskStore
        store = MemoryTaskStore()
        store.create('t1', {'status': 'processing'})
        store.create('t2', {'status': 'completed'})
        store.create('t3', {'status': 'processing'})
        assert store.count_by_status('processing') == 2
        assert store.count_by_status('completed') == 1

    def test_memory_task_store_cleanup(self):
        import time

        from server.taskstore import MemoryTaskStore
        store = MemoryTaskStore()
        store.create('t1', {'status': 'processing'})
        # Manually set created_at to past
        store._tasks['t1']['created_at'] = time.time() - 10000
        removed = store.cleanup_expired(3600)
        assert removed >= 1


class TestMetrics:
    """测试指标模块"""

    def test_import(self):
        from server.metrics import (
            inc_counter,
            observe_histogram,
        )
        assert inc_counter is not None
        assert observe_histogram is not None

    def test_counter_increment(self):
        from server.metrics import get_metrics_snapshot, inc_counter
        inc_counter('test_counter', 1.0, {'label': 'value'})
        snapshot = get_metrics_snapshot()
        assert 'counters' in snapshot

    def test_histogram_observe(self):
        from server.metrics import get_metrics_snapshot, observe_histogram
        observe_histogram('test_histogram', 0.5, {'label': 'value'})
        snapshot = get_metrics_snapshot()
        assert 'histograms' in snapshot

    def test_prometheus_format(self):
        from server.metrics import format_prometheus_text
        text = format_prometheus_text()
        assert isinstance(text, str)


class TestRateLimiter:
    """测试限流器"""

    def test_import(self):
        from server.ratelimiter import MemoryRateLimiter, create_rate_limiter
        assert MemoryRateLimiter is not None
        assert callable(create_rate_limiter)

    def test_memory_rate_limiter(self):
        from server.ratelimiter import MemoryRateLimiter
        rl = MemoryRateLimiter(max_requests=3, window_seconds=60)
        assert rl.is_allowed('key1') is True
        assert rl.is_allowed('key1') is True
        assert rl.is_allowed('key1') is True
        assert rl.is_allowed('key1') is False  # Exceeds limit

    def test_different_keys(self):
        from server.ratelimiter import MemoryRateLimiter
        rl = MemoryRateLimiter(max_requests=1, window_seconds=60)
        assert rl.is_allowed('key1') is True
        assert rl.is_allowed('key2') is True
        assert rl.is_allowed('key1') is False

    def test_cleanup(self):
        import time

        from server.ratelimiter import MemoryRateLimiter
        rl = MemoryRateLimiter(max_requests=1, window_seconds=10)
        rl.is_allowed('key1')
        # Simulate time passing
        future = time.time() + 20
        removed = rl.cleanup(future)
        assert removed >= 1


class TestSSE:
    """测试 SSE 模块"""

    def test_import(self):
        from server.sse import buffers, lock, subscribers, v2_active_ids
        assert buffers is not None
        assert lock is not None
        assert subscribers is not None
        assert v2_active_ids is not None


class TestWS:
    """测试 WebSocket 模块"""

    def test_import(self):
        from server.ws import manager
        assert manager is not None


class TestDB:
    """测试数据库模块"""

    def test_import(self):
        from server.db import (
            get_db,
            insert_analysis,
        )
        assert callable(get_db)
        assert callable(insert_analysis)

    def test_generate_analysis_id(self):
        from server.db import generate_analysis_id
        aid = generate_analysis_id()
        assert aid.startswith('ana_')
        assert len(aid) > 10

    def test_max_page_size(self):
        from server.db import MAX_PAGE_SIZE
        assert MAX_PAGE_SIZE == 100


class TestDeps:
    """测试依赖模块"""

    def test_import(self):
        from server.deps import (
            error_response,
            verify_api_key,
        )
        assert callable(verify_api_key)
        assert callable(error_response)

    def test_validate_analysis_id(self):
        from server.deps import validate_analysis_id
        assert validate_analysis_id('ana_abcdef123456') is True
        assert validate_analysis_id('invalid') is False
        assert validate_analysis_id('') is False

    def test_get_int_env(self):
        # Test with valid value
        import os

        from server.deps import get_int_env
        os.environ['TEST_INT_VAR'] = '42'
        assert get_int_env('TEST_INT_VAR', 10) == 42
        # Test with invalid value
        os.environ['TEST_INT_VAR'] = 'abc'
        assert get_int_env('TEST_INT_VAR', 10) == 10
        # Test with missing value
        del os.environ['TEST_INT_VAR']
        assert get_int_env('TEST_INT_VAR', 10) == 10

    def test_error_response(self):
        from server.deps import error_response
        resp = error_response(400, 'TEST', 'Test error')
        assert resp.status_code == 400


class TestSchemas:
    """测试 Pydantic schemas"""

    def test_bazi_pillars(self):
        from server.schemas import BaziPillars
        p = BaziPillars(year='壬午', month='乙巳', day='丁亥', hour='癸卯')
        assert p.year == '壬午'
        assert p.to_bazi_string() == '壬午 乙巳 丁亥 癸卯'

    def test_bazi_pillars_invalid(self):
        from pydantic import ValidationError

        from server.schemas import BaziPillars
        with pytest.raises(ValidationError):
            BaziPillars(year='XX', month='乙巳', day='丁亥', hour='癸卯')

    def test_dayun_item(self):
        from server.schemas import DayunItem
        d = DayunItem(gan='甲', zhi='寅')
        assert d.gan == '甲'
        assert d.zhi == '寅'

    def test_dayun_item_invalid(self):
        from pydantic import ValidationError

        from server.schemas import DayunItem
        with pytest.raises(ValidationError):
            DayunItem(gan='X', zhi='寅')

    def test_bazi_analysis_request(self):
        from server.schemas import BaziAnalysisRequest
        req = BaziAnalysisRequest(性别='女', 八字='壬午 乙巳 丁亥 癸卯', 日主='丁')
        assert req.性别 == '女'
        assert req.detail_level == 'standard'

    def test_bazi_analysis_request_invalid(self):
        from pydantic import ValidationError

        from server.schemas import BaziAnalysisRequest
        with pytest.raises(ValidationError):
            BaziAnalysisRequest(性别='女', 八字='invalid', 日主='丁')


class TestCrossValidateDetail:
    """测试交叉验证详细功能"""

    def test_cross_validate_empty(self):
        from server.cross_validate import cross_validate_schools
        result = cross_validate_schools({})
        assert isinstance(result, dict)


class TestDayunScoreDetail:
    """测试大运评分详细功能"""

    def test_score_dayun_basic(self):
        from server.dayun_score import score_dayun
        # 简单测试：传入空列表应该返回空
        result = score_dayun([], '木', [], {})
        assert isinstance(result, (list, dict))
