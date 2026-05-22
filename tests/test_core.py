"""单元测试 — bazi_pro 核心模块"""

import json
import os
import tempfile
from pathlib import Path

from bazi_pro import (
    AnalysisEngine, GAN_WUXING, ZHI_WUXING, GAN_SHISHEN_MAP,
    derive_shishen, count_wuxing_from_bazi, wuxing_pct,
)
from bazi_pro.compare_engine import CompareEngine, GAN_HE, ZHI_CHONG, ZHI_HE, ZHI_HAI, ZHI_XING
from bazi_pro.liunian_sandbox import LiunianSandbox, GAN, ZHI
from bazi_pro.archive import ArchiveStore
from bazi_pro.calibration import CalibrationTracker
from bazi_pro.plugin_api import BaziPlugin, register_plugin, list_plugins
from bazi_pro.evidence import new_evidence, build_analysis_evidence
from bazi_pro.view_model import DashboardVM, EvidenceVM, PillarVM, VerdictVM


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
        assert result['elements']['counts']['火'] > 0

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
        wq = result['strength']['wuxing_quick']
        assert 'tendency' in wq
        assert 'yin_bi_pct' in wq
        assert wq['day_master_wuxing'] == '火'


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
            claim='建禄月劫',
            confidence=0.82,
        )
        assert ev.stage_id == 'E1'
        assert ev.confidence == 0.82

    def test_dashboard_vm_defaults(self):
        vm = DashboardVM()
        assert vm.bazi == ''
        assert len(vm.pillars) == 0
        assert vm.verdict.confidence == 0.80
