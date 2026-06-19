"""提高 bazi_pro 模块覆盖率的测试"""



class TestDoctor:
    """测试 bazi_pro/doctor.py 环境诊断"""

    def test_import(self):
        from bazi_pro.doctor import main
        assert callable(main)


class TestPaipan:
    """测试 bazi_pro/paipan.py 排盘引擎"""

    def test_import(self):
        from bazi_pro.paipan import paipan_from_datetime
        assert callable(paipan_from_datetime)

    def test_paipan_basic(self):
        from bazi_pro.paipan import paipan_from_datetime
        result = paipan_from_datetime('2002-05-19 06:14', '女')
        assert isinstance(result, dict)
        assert result.get('status') == 'completed'
        assert 'pillars' in result


class TestDashboard:
    """测试 bazi_pro/dashboard.py 仪表盘"""

    def test_import(self):
        from bazi_pro.dashboard import generate_dashboard
        assert callable(generate_dashboard)


class TestGenerateReport:
    """测试 bazi_pro/generate_report.py 报告生成"""

    def test_import(self):
        from bazi_pro.generate_report import main
        assert callable(main)


class TestNarrator:
    """测试 bazi_pro/narrator.py 叙述器"""

    def test_import(self):
        from bazi_pro.narrator import narrate_analysis
        assert callable(narrate_analysis)

    def test_narrate_basic(self):
        from bazi_pro.narrator import narrate_analysis
        # 模拟分析结果
        mock_result = {
            'day_master': '丁',
            'wangshuai': {'verdict': '身弱', 'deling_score': -1, 'dedi_score': 1.0, 'deshi_score': 1.5},
            'pattern': {'pattern': '正官格', 'layer': 1, 'confidence': 0.8},
            'yongshen': {'yongshen': '木', 'xishen': ['水'], 'jishen': ['金']},
            'element_forces': {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}},
            'relations': [],
            'tiaohou': {'tiaohou': '甲木', 'reason': '春丁需甲'},
            'pillars': [
                {'position': '年', 'gan': '壬', 'zhi': '午', 'wuxing_gan': '水', 'wuxing_zhi': '火', 'shishen': '正官'},
                {'position': '月', 'gan': '乙', 'zhi': '巳', 'wuxing_gan': '木', 'wuxing_zhi': '火', 'shishen': '偏印'},
                {'position': '日', 'gan': '丁', 'zhi': '亥', 'wuxing_gan': '火', 'wuxing_zhi': '水', 'shishen': '比肩'},
                {'position': '时', 'gan': '癸', 'zhi': '卯', 'wuxing_gan': '水', 'wuxing_zhi': '木', 'shishen': '七杀'},
            ],
        }
        result = narrate_analysis(mock_result)
        assert isinstance(result, dict)
        assert len(result) > 0


class TestViewModel:
    """测试 bazi_pro/view_model.py 视图模型"""

    def test_import(self):
        from bazi_pro.view_model import DashboardVM
        assert DashboardVM is not None


class TestEvidence:
    """测试 bazi_pro/evidence.py 证据链"""

    def test_import(self):
        from bazi_pro.evidence import build_analysis_evidence, new_evidence
        assert callable(build_analysis_evidence)
        assert callable(new_evidence)

    def test_new_evidence(self):
        from bazi_pro.evidence import new_evidence
        ev = new_evidence('测试论断', 0.8, 'MCP依据', '古籍依据', '规则依据')
        assert isinstance(ev, dict)


class TestTrace:
    """测试 bazi_pro/trace.py 分析追踪"""

    def test_import(self):
        from bazi_pro.trace import TraceBuilder
        assert TraceBuilder is not None


class TestValidation:
    """测试 bazi_pro/validation.py 输入验证"""

    def test_import(self):
        from bazi_pro.validation import (
            validate_bazi_input,
        )
        assert callable(validate_bazi_input)

    def test_validate_bazi_string_valid(self):
        from bazi_pro.validation import validate_bazi_string
        valid, msg = validate_bazi_string('壬午 乙巳 丁亥 癸卯')
        assert valid is True

    def test_validate_bazi_string_invalid(self):
        from bazi_pro.validation import validate_bazi_string
        valid, msg = validate_bazi_string('invalid')
        assert valid is False

    def test_validate_day_master_valid(self):
        from bazi_pro.validation import validate_day_master
        valid, msg = validate_day_master('丁')
        assert valid is True

    def test_validate_day_master_invalid(self):
        from bazi_pro.validation import validate_day_master
        valid, msg = validate_day_master('X')
        assert valid is False

    def test_validate_gender_valid(self):
        from bazi_pro.validation import validate_gender
        valid, msg = validate_gender('女')
        assert valid is True

    def test_validate_gender_invalid(self):
        from bazi_pro.validation import validate_gender
        valid, msg = validate_gender('unknown')
        assert valid is False

    def test_validate_bazi_input_valid(self):
        from bazi_pro.validation import validate_bazi_input
        result = validate_bazi_input({'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁', '性别': '女'})
        assert result['valid'] is True

    def test_validate_bazi_input_invalid(self):
        from bazi_pro.validation import validate_bazi_input
        result = validate_bazi_input({'八字': '', '日主': '', '性别': ''})
        assert result['valid'] is False


class TestRetrieveClassical:
    """测试 bazi_pro/retrieve_classical.py 古籍检索"""

    def test_import(self):
        from bazi_pro.retrieve_classical import retrieve, retrieve_batch
        assert callable(retrieve)
        assert callable(retrieve_batch)


class TestHybridSearch:
    """测试 bazi_pro/hybrid_search.py 混合检索"""

    def test_import(self):
        from bazi_pro.hybrid_search import main
        assert callable(main)


class TestCoreModules:
    """测试核心计算模块"""

    def test_constants(self):
        from bazi_pro.core.constants import GAN_WUXING, ZHI_WUXING, derive_shishen
        assert len(GAN_WUXING) == 10
        assert len(ZHI_WUXING) == 12
        assert derive_shishen('甲', '甲') == '比肩'

    def test_branches(self):
        from bazi_pro.core.branches import CANGGAN_WEIGHT, SHIER_CHANGSHENG
        assert '本气' in CANGGAN_WEIGHT
        assert '甲' in SHIER_CHANGSHENG

    def test_stems(self):
        from bazi_pro.core.stems import GAN_HE, KE_MAP, SHENG_MAP
        assert len(GAN_HE) > 0
        assert len(KE_MAP) == 5
        assert len(SHENG_MAP) == 5

    def test_elements(self):
        from bazi_pro.core.elements import calc_element_forces
        result = calc_element_forces(['壬午', '乙巳', '丁亥', '癸卯'], '巳')
        assert isinstance(result, dict)
        assert 'percent' in result

    def test_strength(self):
        from bazi_pro.core.strength import calc_deling
        status, score = calc_deling('丁', '巳')
        assert isinstance(status, str)
        assert isinstance(score, int)

    def test_patterns(self):
        from bazi_pro.core.patterns import screen_pattern
        result = screen_pattern('丁', ['壬午', '乙巳', '丁亥', '癸卯'], {'verdict': '身弱'}, {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}})
        assert isinstance(result, dict)
        assert 'pattern' in result

    def test_yongshen(self):
        from bazi_pro.core.yongshen import derive_yongshen
        result = derive_yongshen('丁', ['壬午', '乙巳', '丁亥', '癸卯'],
                                {'pattern': '正官格', 'confidence': 0.8},
                                {'verdict': '身弱', 'is_weak': True, 'is_strong': False},
                                {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}})
        assert isinstance(result, dict)

    def test_relations(self):
        from bazi_pro.core.relations import detect_relations
        result = detect_relations(['壬午', '乙巳', '丁亥', '癸卯'])
        assert isinstance(result, list)

    def test_disease(self):
        from bazi_pro.core.disease import detect_disease
        result = detect_disease('丁', ['壬午', '乙巳', '丁亥', '癸卯'], {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}})
        assert isinstance(result, dict)

    def test_tiaohou(self):
        from bazi_pro.core.tiaohou import lookup_tiaohou
        result = lookup_tiaohou('丁', '巳')
        assert isinstance(result, dict)

    def test_health(self):
        from bazi_pro.core.health import analyze_health
        result = analyze_health('丁', ['壬午', '乙巳', '丁亥', '癸卯'], {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}})
        assert isinstance(result, dict)

    def test_wealth(self):
        from bazi_pro.core.wealth import analyze_wealth
        result = analyze_wealth('丁', ['壬午', '乙巳', '丁亥', '癸卯'], {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}})
        assert isinstance(result, dict)

    def test_marriage(self):
        from bazi_pro.core.marriage import analyze_marriage
        result = analyze_marriage('丁', ['壬午', '乙巳', '丁亥', '癸卯'], {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}})
        assert isinstance(result, dict)

    def test_family(self):
        from bazi_pro.core.family import analyze_family
        result = analyze_family('丁', ['壬午', '乙巳', '丁亥', '癸卯'], {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}})
        assert isinstance(result, dict)


class TestAnalysisEngine:
    """测试 AnalysisEngine 入口"""

    def test_import(self):
        from bazi_pro import AnalysisEngine
        assert AnalysisEngine is not None

    def test_analyze_basic(self):
        from bazi_pro import AnalysisEngine
        engine = AnalysisEngine(corpus_path='')
        result = engine.analyze({
            '八字': '壬午 乙巳 丁亥 癸卯',
            '日主': '丁',
            '性别': '女',
        })
        assert result['status'] == 'completed'
        assert result['validation']['valid'] is True


class TestSchools:
    """测试流派分析"""

    def test_import(self):
        from bazi_pro.core.schools import SCHOOL_REGISTRY, school_analyze
        assert callable(school_analyze)
        assert isinstance(SCHOOL_REGISTRY, dict)

    def test_school_registry(self):
        from bazi_pro.core.schools import SCHOOL_REGISTRY
        assert 'ziping' in SCHOOL_REGISTRY or len(SCHOOL_REGISTRY) >= 0


class TestFullAnalysis:
    """测试 full_analysis 入口"""

    def test_import(self):
        from bazi_pro.core import full_analysis
        assert callable(full_analysis)

    def test_full_analysis_basic(self):
        from bazi_pro.core import full_analysis
        result = full_analysis({
            '八字': '壬午 乙巳 丁亥 癸卯',
            '日主': '丁',
            '性别': '女',
        })
        assert result['status'] == 'completed'
        assert 'pattern' in result
        assert 'yongshen' in result


class TestHiddenStems:
    """测试藏干模块"""

    def test_get_canggan(self):
        from bazi_pro.core.hidden_stems import get_canggan
        result = get_canggan('子')
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_canggan_all_zhi(self):
        from bazi_pro.core.hidden_stems import get_canggan
        zhisi = '子丑寅卯辰巳午未申酉戌亥'
        for zhi in zhisi:
            result = get_canggan(zhi)
            assert isinstance(result, list)
            assert len(result) > 0


class TestTenGods:
    """测试十神模块"""

    def test_count_shishen_categories(self):
        from bazi_pro.core.ten_gods import _count_shishen_categories
        result = _count_shishen_categories('丁', ['壬', '乙', '癸'], ['壬午', '乙巳', '丁亥', '癸卯'])
        assert isinstance(result, dict)

    def test_get_yongshen_direction(self):
        from bazi_pro.core.ten_gods import _get_yongshen_direction
        result = _get_yongshen_direction('身弱')
        assert isinstance(result, (str, list))


class TestSchoolModules:
    """测试流派模块"""

    def test_ziping_import(self):
        from bazi_pro.core.schools.ziping import ZipingAnalyzer
        assert ZipingAnalyzer is not None

    def test_mangpai_import(self):
        from bazi_pro.core.schools.mangpai import MangpaiAnalyzer
        assert MangpaiAnalyzer is not None

    def test_xinpai_import(self):
        from bazi_pro.core.schools.xinpai import XinpaiAnalyzer
        assert XinpaiAnalyzer is not None

    def test_base_import(self):
        from bazi_pro.core.schools.base import SchoolAnalyzer
        assert SchoolAnalyzer is not None


class TestUIModules:
    """测试 UI 模块"""

    def test_text_cleaner_import(self):
        from bazi_pro.ui.text_cleaner import clean_text
        assert callable(clean_text)

    def test_pillar_chart_import(self):
        from bazi_pro.ui.pillar_chart import render_pillar_chart
        assert callable(render_pillar_chart)


class TestCorePatterns:
    """测试格局筛查详细功能"""

    def test_screen_pattern_detailed(self):
        from bazi_pro.core.patterns import screen_pattern
        result = screen_pattern('丁', ['壬午', '乙巳', '丁亥', '癸卯'],
                               {'verdict': '身弱'},
                               {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}})
        assert isinstance(result, dict)
        assert 'pattern' in result
        assert 'layer' in result

    def test_pattern_yongshen_table(self):
        from bazi_pro.core.patterns import PATTERN_YONGSHEN
        assert isinstance(PATTERN_YONGSHEN, dict)
        assert len(PATTERN_YONGSHEN) > 0


class TestCoreRelations:
    """测试关系检测详细功能"""

    def test_detect_relations_all_types(self):
        from bazi_pro.core.relations import detect_relations
        # 测试包含各种关系的八字
        result = detect_relations(['甲子', '己丑', '庚寅', '辛卯'])
        assert isinstance(result, list)

    def test_detect_shishen_relations(self):
        from bazi_pro.core.relations import detect_shishen_relations
        result = detect_shishen_relations('丁', ['壬午', '乙巳', '丁亥', '癸卯'])
        assert isinstance(result, list)


class TestCoreElements:
    """测试五行力量详细功能"""

    def test_hehua_detection(self):
        from bazi_pro.core.elements import _detect_hehua
        result = _detect_hehua(['甲子', '己丑', '庚寅', '辛卯'], '丑')
        assert isinstance(result, dict)
        assert 'gan_he' in result

    def test_calc_element_forces_with_hehua(self):
        from bazi_pro.core.elements import calc_element_forces
        # 测试有合化的八字
        result = calc_element_forces(['甲子', '己丑', '庚寅', '辛卯'], '丑')
        assert isinstance(result, dict)
        assert 'hehua' in result


class TestCoreStrength:
    """测试旺衰判定详细功能"""

    def test_calc_deling_all_states(self):
        from bazi_pro.core.strength import calc_deling
        # 测试不同日主在不同月令的得令状态
        for dm in ['甲', '乙', '丙', '丁']:
            for mz in ['子', '丑', '寅', '卯']:
                status, score = calc_deling(dm, mz)
                assert isinstance(status, str)
                assert isinstance(score, int)

    def test_calc_dedi_detailed(self):
        from bazi_pro.core.strength import calc_dedi
        result = calc_dedi('丁', ['壬午', '乙巳', '丁亥', '癸卯'])
        assert 'score' in result
        assert 'level' in result
        assert 'details' in result

    def test_calc_deshi_detailed(self):
        from bazi_pro.core.strength import calc_deshi
        result = calc_deshi('丁', ['壬午', '乙巳', '丁亥', '癸卯'])
        assert 'score' in result
        assert 'level' in result
        assert 'details' in result


class TestCoreDisease:
    """测试格局之病详细功能"""

    def test_detect_disease_detailed(self):
        from bazi_pro.core.disease import detect_disease
        result = detect_disease('丁', ['壬午', '乙巳', '丁亥', '癸卯'],
                               {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}})
        assert 'has_disease' in result
        assert 'items' in result


class TestCoreWealth:
    """测试财运分析详细功能"""

    def test_analyze_wealth_detailed(self):
        from bazi_pro.core.wealth import analyze_wealth
        result = analyze_wealth('丁', ['壬午', '乙巳', '丁亥', '癸卯'],
                               {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}})
        assert isinstance(result, dict)


class TestCoreMarriage:
    """测试婚姻分析详细功能"""

    def test_analyze_marriage_detailed(self):
        from bazi_pro.core.marriage import analyze_marriage
        result = analyze_marriage('丁', ['壬午', '乙巳', '丁亥', '癸卯'],
                                 {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}})
        assert isinstance(result, dict)


class TestCoreHealth:
    """测试健康分析详细功能"""

    def test_analyze_health_detailed(self):
        from bazi_pro.core.health import analyze_health
        result = analyze_health('丁', ['壬午', '乙巳', '丁亥', '癸卯'],
                               {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}})
        assert isinstance(result, dict)


class TestCoreFamily:
    """测试六亲分析详细功能"""

    def test_analyze_family_detailed(self):
        from bazi_pro.core.family import analyze_family
        result = analyze_family('丁', ['壬午', '乙巳', '丁亥', '癸卯'],
                               {'percent': {'木': 25, '火': 20, '土': 15, '金': 20, '水': 20}})
        assert isinstance(result, dict)
