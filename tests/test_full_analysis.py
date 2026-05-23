from pathlib import Path

from bazi_pro import AnalysisEngine
from bazi_pro.core_rules import full_analysis


GOLDEN_DIR = Path(__file__).resolve().parent / "golden_cases"


class TestFullAnalysisInput:

    def test_missing_bazi_returns_invalid(self):
        result = full_analysis({"日主": "丁"})
        assert result["status"] == "invalid_input"

    def test_missing_day_master_returns_invalid(self):
        result = full_analysis({"八字": "壬午 乙巳 丁亥 癸卯"})
        assert result["status"] == "invalid_input"

    def test_empty_dict_returns_invalid(self):
        result = full_analysis({})
        assert result["status"] == "invalid_input"

    def test_single_pillar_returns_invalid(self):
        result = full_analysis({"八字": "壬午", "日主": "丁"})
        assert result["status"] == "invalid_input"


class TestFullAnalysisOutput:

    @classmethod
    def setup_class(cls):
        cls.result = full_analysis({
            "八字": "壬午 乙巳 丁亥 癸卯",
            "日主": "丁",
        })

    def test_has_required_top_level_keys(self):
        for key in ["deling", "dedi", "deshi", "wangshuai", "element_forces",
                     "relations", "pattern", "yongshen", "pillars"]:
            assert key in self.result, f"Missing key: {key}"

    def test_wangshuai_structure(self):
        ws = self.result["wangshuai"]
        for key in ["verdict", "deling_score", "dedi_score", "deshi_score",
                     "is_weak", "is_strong"]:
            assert key in ws, f"Missing wangshuai key: {key}"

    def test_element_forces_structure(self):
        ef = self.result["element_forces"]
        for key in ["raw", "percent", "total"]:
            assert key in ef, f"Missing element_forces key: {key}"

    def test_pattern_structure(self):
        pat = self.result["pattern"]
        for key in ["pattern", "layer", "type", "confidence", "reason", "candidates"]:
            assert key in pat, f"Missing pattern key: {key}"

    def test_yongshen_structure(self):
        ys = self.result["yongshen"]
        for key in ["yongshen", "yongshen_gan", "jishen", "confidence"]:
            assert key in ys, f"Missing yongshen key: {key}"
        assert isinstance(ys, dict)

    def test_pillars_structure(self):
        pillars = self.result["pillars"]
        assert isinstance(pillars, list)
        assert len(pillars) == 4
        for p in pillars:
            for key in ["position", "gan", "zhi", "wuxing_gan", "wuxing_zhi",
                         "shishen", "canggan"]:
                assert key in p, f"Missing pillar key: {key}"


class TestFullAnalysisEngineConsistency:

    @classmethod
    def setup_class(cls):
        mcp = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "性别": "女"}
        cls.engine_result = AnalysisEngine(corpus_path="").analyze(mcp)
        cls.core_result = full_analysis({"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"})

    def test_core_analysis_status_completed(self):
        core = self.engine_result["core_analysis"]
        assert core["status"] == "completed"

    def test_pattern_exists_and_not_placeholder(self):
        pat = self.engine_result["pattern"]
        assert pat["name"] != ""
        assert pat["name"] != "unknown"
        assert isinstance(pat["name"], str)
        assert len(pat["name"]) > 0

    def test_yongshen_is_structured_dict(self):
        ys = self.engine_result["yongshen"]
        assert isinstance(ys, dict)
        assert "yongshen" in ys
        assert ys["yongshen"] != ""

    def test_strength_wangshuai_exists(self):
        strength = self.engine_result["strength"]
        assert "wangshuai" in strength
        ws = strength["wangshuai"]
        assert "verdict" in ws

    def test_element_forces_exists(self):
        ef = self.engine_result["element_forces"]
        assert "raw" in ef
        assert "percent" in ef
        assert "total" in ef

    def test_core_matches_full_analysis(self):
        core_ws = self.engine_result["core_analysis"]["wangshuai"]["verdict"]
        fa_ws = self.core_result["wangshuai"]["verdict"]
        assert core_ws == fa_ws

        core_pat = self.engine_result["core_analysis"]["pattern"]["pattern"]
        fa_pat = self.core_result["pattern"]["pattern"]
        assert core_pat == fa_pat


class TestFullAnalysisBoundary:

    def test_all_same_wuxing(self):
        result = full_analysis({"八字": "庚申 辛酉 庚申 辛酉", "日主": "庚"})
        assert result["status"] == "completed"
        assert result["wangshuai"]["is_strong"] is True
        pct = result["element_forces"]["percent"]
        assert pct.get("金", 0) > 50

    def test_extreme_strong(self):
        result = full_analysis({"八字": "壬子 壬子 壬子 壬子", "日主": "壬"})
        assert result["status"] == "completed"
        assert result["wangshuai"]["is_extreme_strong"] is True
        assert result["deling"]["score"] == 3

    def test_extreme_weak(self):
        result = full_analysis({"八字": "庚午 壬申 甲寅 丙午", "日主": "甲"})
        assert result["status"] == "completed"
        assert result["deling"]["score"] <= 0

    def test_pattern_unknown_case(self):
        result = full_analysis({"八字": "甲子 丙寅 戊辰 庚午", "日主": "戊"})
        assert result["status"] == "completed"
        assert result["pattern"]["pattern"] != ""
        assert result["pattern"]["confidence"] > 0

    def test_congqiang_pattern(self):
        result = full_analysis({"八字": "壬子 壬子 壬子 壬子", "日主": "壬"})
        assert result["status"] == "completed"
        assert result["wangshuai"]["is_extreme_strong"] is True
        pat = result["pattern"]["pattern"]
        assert '从强' in pat or '专旺' in pat or '润下' in pat

    def test_congcai_or_congsha_pattern(self):
        result = full_analysis({"八字": "庚午 丙戌 甲申 壬申", "日主": "甲"})
        assert result["status"] == "completed"
        if result["wangshuai"]["is_extreme_weak"]:
            pat = result["pattern"]["pattern"]
            assert '从' in pat or '七杀' in pat


class TestAnalysisEngineReturnContract:

    EXPECTED_TOP_LEVEL_KEYS = {
        'status', 'detail_level', 'validation', 'core_analysis',
        'pillars', 'shishen', 'deling', 'dedi', 'deshi',
        'strength', 'pattern', 'yongshen', 'element_forces',
        'elements', 'quick_element_counts', 'quick_element_pct',
        'relations', 'retrieval', 'note',
    }

    @classmethod
    def setup_class(cls):
        cls.result = AnalysisEngine(corpus_path='').analyze({
            '八字': '壬午 乙巳 丁亥 癸卯', '日主': '丁', '性别': '女',
        })

    def test_top_level_keys_stable(self):
        actual_keys = set(self.result.keys())
        missing = self.EXPECTED_TOP_LEVEL_KEYS - actual_keys
        extra = actual_keys - self.EXPECTED_TOP_LEVEL_KEYS
        assert not missing, f"Missing keys: {missing}"
        assert not extra, f"Unexpected extra keys: {extra}"

    def test_backward_compat_elements_counts(self):
        assert self.result['elements']['counts'] == self.result['quick_element_counts']['counts']

    def test_backward_compat_elements_percent(self):
        assert self.result['elements']['percent'] == self.result['quick_element_pct']['percent']

    def test_backward_compat_strength_wuxing_quick(self):
        wq = self.result['strength']['wuxing_quick']
        assert 'counts' in wq
        assert 'percent' in wq
        assert wq['counts'] == self.result['quick_element_counts']['counts']

    def test_retrieval_has_warnings_field(self):
        assert 'warnings' in self.result['retrieval']
