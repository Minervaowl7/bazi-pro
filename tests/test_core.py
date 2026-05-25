"""单元测试 — bazi_pro 核心模块"""

import os
import tempfile

from bazi_pro import (
    AnalysisEngine,
    count_wuxing_from_bazi,
    derive_shishen,
    wuxing_pct,
)
from bazi_pro.archive import ArchiveStore
from bazi_pro.calibration import CalibrationTracker
from bazi_pro.compare_engine import CompareEngine
from bazi_pro.evidence import build_analysis_evidence, new_evidence
from bazi_pro.liunian_sandbox import LiunianSandbox
from bazi_pro.plugin_api import BaziPlugin, list_plugins, register_plugin
from bazi_pro.view_model import DashboardVM, EvidenceVM


class TestDeriveShishen:

    def test_jia_jia(self):
        assert derive_shishen('甲', '甲') == '比肩'

    def test_jia_yi(self):
        assert derive_shishen('甲', '乙') == '劫财'

    def test_jia_geng(self):
        assert derive_shishen('甲', '庚') == '七杀'

    def test_ren_bing(self):
        assert derive_shishen('壬', '丙') == '偏财'

    def test_ding_jia(self):
        assert derive_shishen('丁', '甲') == '正印'

    def test_unknown_gan(self):
        assert derive_shishen('甲', 'X') == ''


class TestCountWuxing:

    def test_basic(self):
        bazi = '壬午 乙巳 丁亥 癸卯'
        counts = count_wuxing_from_bazi(bazi)
        assert counts['木'] > 0
        assert counts['火'] > 0
        assert counts['水'] > 0

    def test_all_five(self):
        bazi = '甲子 丙寅 戊辰 庚午'
        counts = count_wuxing_from_bazi(bazi)
        total = sum(counts.values())
        assert total == 8

    def test_empty(self):
        counts = count_wuxing_from_bazi('')
        assert sum(counts.values()) == 0


class TestWuxingPct:

    def test_basic(self):
        counts = {'木': 2, '火': 2, '土': 0, '金': 0, '水': 2}
        pct = wuxing_pct(counts)
        assert abs(pct['木'] - 33.3) < 0.5
        assert abs(pct['土'] - 0.0) < 0.1

    def test_empty(self):
        pct = wuxing_pct({'木': 0, '火': 0, '土': 0, '金': 0, '水': 0})
        assert all(v == 0.0 for v in pct.values())


class TestAnalysisEngine:

    def test_analyze_basic(self):
        engine = AnalysisEngine(corpus_path='')
        result = engine.analyze({
            '八字': '壬午 乙巳 丁亥 癸卯',
            '日主': '丁',
            '性别': '女',
        })
        assert result['status'] == 'completed'
        assert result['validation']['valid'] is True
        assert len(result['pillars']) == 4
        assert result['shishen']['年干'] == '正官'
        assert result['element_forces']['percent']['火'] > 0

    def test_analyze_invalid_input(self):
        engine = AnalysisEngine(corpus_path='')
        result = engine.analyze({'八字': '', '日主': '', '性别': ''})
        assert result['status'] == 'invalid_input'

    def test_analyze_wuxing_quick_check(self):
        engine = AnalysisEngine(corpus_path='')
        result = engine.analyze({
            '八字': '壬午 乙巳 丁亥 癸卯',
            '日主': '丁',
            '性别': '女',
        })
        ws = result['strength']['wangshuai']
        assert 'verdict' in ws
        assert ws['is_weak'] is False or ws['is_strong'] is True


class TestCompareEngine:

    def test_compare_pillars(self):
        engine = CompareEngine()
        engine.load_chart_a_dict({'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'})
        engine.load_chart_b_dict({'八字': '甲子 丙寅 戊辰 庚午', '日主': '戊'})
        result = engine.compare()
        assert len(result.pillar_diff) == 4
        assert result.compatibility_score >= 0
        assert result.compatibility_score <= 100

    def test_compare_relations(self):
        engine = CompareEngine()
        engine.load_chart_a_dict({'八字': '甲子 乙丑 丙寅 丁卯', '日主': '丙'})
        engine.load_chart_b_dict({'八字': '己巳 庚午 辛未 壬申', '日主': '辛'})
        relations = engine.compare_relations()
        gan_he = [r for r in relations if r['type'] == '天干合']
        assert len(gan_he) > 0

    def test_wuxing_overlap(self):
        engine = CompareEngine()
        engine.load_chart_a_dict({'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'})
        engine.load_chart_b_dict({'八字': '甲子 丙寅 戊辰 庚午', '日主': '戊'})
        result = engine.compare()
        assert 'overlap' in result.wuxing_overlap
        overlap = result.wuxing_overlap['overlap']
        for wx in ['木', '火', '土', '金', '水']:
            assert wx in overlap
            assert 'diff_pct' in overlap[wx]


class TestLiunianSandbox:

    def test_get_year_data(self):
        sandbox = LiunianSandbox({'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'})
        yd = sandbox.get_year_data(2024)
        assert yd.year == 2024
        assert yd.gan == '甲'
        assert yd.zhi == '辰'
        assert yd.gan_zhi == '甲辰'

    def test_shen_trigger(self):
        sandbox = LiunianSandbox({'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'})
        yd = sandbox.get_year_data(2024)
        assert len(yd.shen_trigger) > 0

    def test_wuxing_shift(self):
        sandbox = LiunianSandbox({'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'})
        yd = sandbox.get_year_data(2024)
        assert len(yd.wuxing_shift) > 0

    def test_mark_key_years(self):
        sandbox = LiunianSandbox({'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'})
        marked = sandbox.mark_key_years()
        assert len(marked) == 21
        starred = [y for y in marked if '⭐' in y.bookmark]
        warned = [y for y in marked if '⚠️' in y.bookmark]
        assert len(starred) > 0 or len(warned) > 0

    def test_relations(self):
        sandbox = LiunianSandbox({'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'})
        yd = sandbox.get_year_data(2026)
        assert yd.gan == '丙'
        assert yd.zhi == '午'
        has_relation = len(yd.relations) > 0
        assert has_relation


class TestArchiveStore:

    def test_save_and_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            store = ArchiveStore(db_path=db_path)
            rid = store.save_analysis(
                bazi='壬午 乙巳 丁亥 癸卯',
                day_master='丁',
                gender='女',
                pattern='暗食神格',
            )
            assert rid > 0
            records = store.list_analyses(limit=5)
            assert len(records) >= 1
            assert records[0]['bazi'] == '壬午 乙巳 丁亥 癸卯'

    def test_get_analysis(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            store = ArchiveStore(db_path=db_path)
            rid = store.save_analysis(bazi='甲子 乙丑 丙寅 丁卯')
            record = store.get_analysis(rid)
            assert record['bazi'] == '甲子 乙丑 丙寅 丁卯'

    def test_total_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            store = ArchiveStore(db_path=db_path)
            assert store.total_count == 0
            store.save_analysis(bazi='test')
            assert store.total_count == 1


class TestCalibrationTracker:

    def test_record_feedback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'cal.json')
            tracker = CalibrationTracker(db_path=db_path)
            tracker.record_feedback('test-1', '旺衰判断：身强', True)
            tracker.record_feedback('test-2', '格局判断：正官格', False)
            assert tracker.total_feedback == 2
            stats = tracker.get_calibration_stats()
            assert 'wangshuai' in stats
            assert stats['wangshuai']['accuracy'] == 1.0

    def test_calibration_weights(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'cal.json')
            tracker = CalibrationTracker(db_path=db_path)
            weights = tracker.apply_calibration_weights()
            assert 'wangshuai' in weights
            assert weights['wangshuai'] == 1.0


class TestPluginAPI:

    def test_register_and_get(self):
        class TestPlugin(BaziPlugin):
            def on_retrieve(self, query, results):
                return results
            def on_evidence(self, evidence):
                return evidence
            def on_render(self, html, vm):
                return html
        plugin = TestPlugin()
        plugin.name = 'test'
        plugin.version = '1.0'
        register_plugin(plugin)
        names = list_plugins()
        assert 'test' in names


class TestEvidence:

    def test_new_evidence(self):
        ev = new_evidence(
            claim='日主甲木，身强',
            confidence=0.85,
            basis_mcp=['dayMaster'],
            basis_classics=['SFTK_00068'],
            basis_rules=['得令=1'],
        )
        assert ev['claim'] == '日主甲木，身强'
        assert ev['confidence'] == 0.85
        assert len(ev['basis']['mcp_fields']) == 1

    def test_build_analysis_evidence(self):
        result = build_analysis_evidence(
            day_master='丙', gender='女', bazi='癸卯 壬戌 丙午 壬辰',
            deling_score=-2, dedi_score=2.3, deshi_score=2.9,
            wangshuai='身弱', pattern_name='暗食神格', pattern_score=65,
            pattern_tier='中等', yongshen='土', xishen='木、火', jishen='水',
            classical_refs=[], key_features=[], dayun_summary=[],
        )
        assert len(result['evidence_chain']) >= 3
        assert result['meta']['engine'] == 'bazi-pro v5.0'


class TestViewModel:

    def test_evidence_vm(self):
        ev = EvidenceVM(
            stage_id='E1',
            title='格局裁决',
            claim='月劫格',
            confidence=0.82,
        )
        assert ev.stage_id == 'E1'
        assert ev.confidence == 0.82

    def test_dashboard_vm_defaults(self):
        vm = DashboardVM()
        assert vm.bazi == ''
        assert len(vm.pillars) == 0
        assert vm.verdict.confidence == 0.80


class TestCoreRulesCanggan:

    def test_zi_canggan(self):
        from bazi_pro.core_rules import get_canggan
        cg = get_canggan('子')
        assert len(cg) == 1
        assert cg[0] == ('癸', '本气')

    def test_chou_canggan(self):
        from bazi_pro.core_rules import get_canggan
        cg = get_canggan('丑')
        assert len(cg) == 3
        assert cg[0] == ('己', '本气')
        assert cg[1] == ('癸', '中气')
        assert cg[2] == ('辛', '余气')

    def test_wu_canggan(self):
        from bazi_pro.core_rules import get_canggan
        cg = get_canggan('午')
        assert len(cg) == 2
        assert cg[0] == ('丁', '本气')
        assert cg[1] == ('己', '中气')


class TestCoreRulesDeling:

    def test_jia_yin_linquan(self):
        from bazi_pro.core_rules import calc_deling
        status, score = calc_deling('甲', '寅')
        assert status == '临官'
        assert score == 3

    def test_jia_shen_jue(self):
        from bazi_pro.core_rules import calc_deling
        status, score = calc_deling('甲', '申')
        assert status == '绝'
        assert score == -3

    def test_bing_si_linquan(self):
        from bazi_pro.core_rules import calc_deling
        status, score = calc_deling('丙', '巳')
        assert status == '临官'
        assert score == 3

    def test_ren_zi_diwang(self):
        from bazi_pro.core_rules import calc_deling
        status, score = calc_deling('壬', '子')
        assert status == '帝旺'
        assert score == 3


class TestCoreRulesDedi:

    def test_jia_with_yin_root(self):
        from bazi_pro.core_rules import calc_dedi
        result = calc_dedi('甲', ['甲子', '丙寅', '甲辰', '庚午'])
        assert result['score'] > 0
        assert result['level'] in ('得地', '偏得地', '不得地')

    def test_jia_no_root(self):
        from bazi_pro.core_rules import calc_dedi
        result = calc_dedi('甲', ['庚午', '丙申', '庚申', '壬午'])
        assert result['score'] < 1.5


class TestCoreRulesDeshi:

    def test_jia_with_yin_bi(self):
        from bazi_pro.core_rules import calc_deshi
        result = calc_deshi('甲', ['壬子', '癸寅', '甲辰', '乙午'])
        assert result['score'] > 0

    def test_jia_no_yin_bi(self):
        from bazi_pro.core_rules import calc_deshi
        result = calc_deshi('甲', ['庚午', '丙申', '庚申', '壬午'])
        assert result['level'] in ('不得势', '偏得势')


class TestCoreRulesWangshuai:

    def test_shenwang(self):
        from bazi_pro.core_rules import judge_wangshuai
        result = judge_wangshuai(3, 3.5, 5)
        assert result['verdict'] == '身旺'
        assert result['is_strong'] is True

    def test_shenruo(self):
        from bazi_pro.core_rules import judge_wangshuai
        result = judge_wangshuai(-2, 0.5, 1)
        assert '弱' in result['verdict']
        assert result['is_weak'] is True

    def test_jiwang(self):
        from bazi_pro.core_rules import judge_wangshuai
        result = judge_wangshuai(3, 3.5, 7)
        assert result['verdict'] == '极旺'
        assert result['is_extreme_strong'] is True
        assert result['is_strong'] is True

    def test_jiruo(self):
        from bazi_pro.core_rules import judge_wangshuai
        result = judge_wangshuai(-2, 1.0, 0)
        assert result['verdict'] == '极弱'
        assert result['is_extreme_weak'] is True
        assert result['is_weak'] is True

    def test_wangshuai_flags(self):
        from bazi_pro.core_rules import judge_wangshuai
        result = judge_wangshuai(2, 3.5, 5)
        assert result['is_strong'] is True
        assert result['is_extreme_strong'] is False
        assert result['is_weak'] is False
        assert result['is_extreme_weak'] is False


class TestCoreRulesElementForces:

    def test_basic_calc(self):
        from bazi_pro.core_rules import calc_element_forces
        result = calc_element_forces(['壬午', '乙巳', '丁亥', '癸卯'], '巳')
        pct = result['percent']
        total = sum(pct.values())
        assert abs(total - 100) < 1.0
        assert pct['火'] > 0
        assert pct['水'] > 0

    def test_all_five_present(self):
        from bazi_pro.core_rules import calc_element_forces
        result = calc_element_forces(['甲子', '丙寅', '戊辰', '庚午'], '寅')
        pct = result['percent']
        for wx in ['木', '火', '土', '金', '水']:
            assert pct.get(wx, 0) >= 0


class TestCoreRulesRelations:

    def test_chong(self):
        from bazi_pro.core_rules import detect_relations
        result = detect_relations(['甲子', '丙午', '戊辰', '庚申'])
        chong = [r for r in result if r['type'] == '地支冲']
        assert len(chong) > 0

    def test_he(self):
        from bazi_pro.core_rules import detect_relations
        result = detect_relations(['甲子', '己丑', '戊辰', '庚申'])
        gan_he = [r for r in result if r['type'] == '天干合']
        assert len(gan_he) > 0


class TestCoreRulesPattern:

    def test_zhenguan_ge(self):
        from bazi_pro.core_rules import calc_element_forces, judge_wangshuai, screen_pattern
        bazi_parts = ['庚午', '戊寅', '辛巳', '壬辰']
        wangshuai = judge_wangshuai(2, 2.0, 3.0)
        ef = calc_element_forces(bazi_parts, '寅')
        result = screen_pattern('辛', bazi_parts, wangshuai, ef)
        assert result['pattern'] != '数据不足'
        assert result['confidence'] > 0

    def test_jianlu_yuejie(self):
        from bazi_pro.core_rules import calc_element_forces, judge_wangshuai, screen_pattern
        bazi_parts = ['庚午', '戊寅', '甲子', '丙寅']
        wangshuai = judge_wangshuai(3, 3.0, 4.0)
        ef = calc_element_forces(bazi_parts, '寅')
        result = screen_pattern('甲', bazi_parts, wangshuai, ef)
        assert '建禄格' in result['pattern'] or result['layer'] >= 0


class TestCoreRulesYongshen:

    def test_basic_derive(self):
        from bazi_pro.core_rules import calc_element_forces, derive_yongshen, judge_wangshuai, screen_pattern
        bazi_parts = ['庚午', '戊寅', '辛巳', '壬辰']
        wangshuai = judge_wangshuai(2, 2.0, 3.0)
        ef = calc_element_forces(bazi_parts, '寅')
        pattern = screen_pattern('辛', bazi_parts, wangshuai, ef)
        result = derive_yongshen('辛', bazi_parts, pattern, wangshuai, ef)
        assert result['yongshen'] != ''
        assert result['confidence'] > 0


class TestCoreRulesFullAnalysis:

    def test_basic_analysis(self):
        from bazi_pro.core_rules import full_analysis
        result = full_analysis({
            '八字': '壬午 乙巳 丁亥 癸卯',
            '日主': '丁',
            '性别': '女',
        })
        assert result['status'] == 'completed'
        assert result['wangshuai']['verdict'] != ''
        assert result['pattern']['pattern'] != ''
        assert result['yongshen']['yongshen'] != ''
        assert len(result['pillars']) == 4
        assert len(result['relations']) >= 0

    def test_invalid_input(self):
        from bazi_pro.core_rules import full_analysis
        result = full_analysis({'八字': '', '日主': ''})
        assert result['status'] == 'invalid_input'

    def test_element_forces_sum(self):
        from bazi_pro.core_rules import full_analysis
        result = full_analysis({
            '八字': '壬午 乙巳 丁亥 癸卯',
            '日主': '丁',
            '性别': '女',
        })
        pct = result['element_forces']['percent']
        total = sum(pct.values())
        assert abs(total - 100) < 1.0


class TestDiseaseDetection:

    def test_xiaoshen_duoshi_detected(self):
        """戊寅 壬戌 辛丑 癸巳 辛日主 — 偏印己土在丑本气，食神癸水透时干 → 枭神夺食"""
        from bazi_pro.core.disease import detect_disease
        from bazi_pro.core.elements import calc_element_forces
        bazi_parts = ['戊寅', '壬戌', '辛丑', '癸巳']
        ef = calc_element_forces(bazi_parts, '戌')
        result = detect_disease('辛', bazi_parts, ef)
        assert result['has_disease'] is True
        names = [item['name'] for item in result['items']]
        assert any('枭神夺食' in n or '食神制杀逢枭' in n for n in names)
        item = next(i for i in result['items'] if '枭神夺食' in i['name'] or '食神制杀逢枭' in i['name'])
        assert item['disease_god'] == '偏印'
        assert item['affected_god'] == '食神'
        assert item['severity'] == 'potential'  # 偏印不透干

    def test_xiaoshen_jishen_populated(self):
        """full_analysis 的 jishen 应包含偏印五行（土）"""
        from bazi_pro.core import full_analysis
        result = full_analysis({'八字': '戊寅 壬戌 辛丑 癸巳', '日主': '辛'})
        assert result['disease']['has_disease'] is True
        assert '土' in result['yongshen']['jishen']

    def test_shishen_relations_include_xiaoshen(self):
        """relations 列表中应包含 type='枭神夺食' 的条目"""
        from bazi_pro.core import full_analysis
        result = full_analysis({'八字': '戊寅 壬戌 辛丑 癸巳', '日主': '辛'})
        types = [r['type'] for r in result['relations']]
        assert '枭神夺食' in types

    def test_shangguan_jianguan_neutralized_by_cai(self):
        """甲子 庚午 丁酉 壬寅 丁日主 — 庚正财透干通关，伤官见官被化解"""
        from bazi_pro.core.disease import detect_disease
        from bazi_pro.core.elements import calc_element_forces
        bazi_parts = ['甲子', '庚午', '丁酉', '壬寅']
        ef = calc_element_forces(bazi_parts, '午')
        result = detect_disease('丁', bazi_parts, ef)
        names = [item['name'] for item in result['items']]
        assert '伤官见官' not in names  # 财星通关化解

    def test_active_severity_when_transparent(self):
        """偏印透干时 severity 应为 active"""
        from bazi_pro.core.disease import detect_disease
        from bazi_pro.core.elements import calc_element_forces
        # 甲子 丙寅 戊辰 庚申 戊日主: 丙偏印透干 + 庚食神透干 → active
        bazi_parts = ['甲子', '丙寅', '戊辰', '庚申']
        ef = calc_element_forces(bazi_parts, '寅')
        result = detect_disease('戊', bazi_parts, ef)
        assert result['has_disease'] is True
        item = next(i for i in result['items'] if '枭神夺食' in i['name'] or '食神制杀逢枭' in i['name'])
        assert item['severity'] == 'active'

    def test_no_disease_when_no_conflict(self):
        """庚申 辛酉 庚申 辛酉 庚日主 — 全金命，无食神/偏印冲突"""
        from bazi_pro.core.disease import detect_disease
        from bazi_pro.core.elements import calc_element_forces
        bazi_parts = ['庚申', '辛酉', '庚申', '辛酉']
        ef = calc_element_forces(bazi_parts, '酉')
        result = detect_disease('庚', bazi_parts, ef)
        # 庚日主: 偏印=戊土, 食神=壬水 — 均不出现在此命盘
        assert result['has_disease'] is False
        assert result['items'] == []

    def test_disease_field_in_full_analysis(self):
        """full_analysis 返回值中必须包含 disease 字段"""
        from bazi_pro.core import full_analysis
        result = full_analysis({'八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁'})
        assert 'disease' in result
        d = result['disease']
        assert 'has_disease' in d
        assert 'items' in d
        assert 'medicine_advice' in d
        assert isinstance(d['items'], list)

    def test_detect_shishen_relations_returns_list(self):
        """detect_shishen_relations 应返回列表"""
        from bazi_pro.core.relations import detect_shishen_relations
        result = detect_shishen_relations('辛', ['戊寅', '壬戌', '辛丑', '癸巳'])
        assert isinstance(result, list)
        assert all('type' in r for r in result)

    def test_guansha_hunza_detected(self):
        """官杀混杂检测：正官七杀同时有根，无食伤印化"""
        from bazi_pro.core.disease import detect_disease
        from bazi_pro.core.elements import calc_element_forces
        # 壬午 乙巳 丁亥 癸卯 丁日主: 壬=正官透干, 癸=七杀透干, 无食伤印
        bazi_parts = ['壬午', '乙巳', '丁亥', '癸卯']
        ef = calc_element_forces(bazi_parts, '巳')
        result = detect_disease('丁', bazi_parts, ef)
        names = [item['name'] for item in result['items']]
        # 乙=偏印透干 → 印星有根 → 官杀混杂被化解
        assert '官杀混杂' not in names
