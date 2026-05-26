"""VM 数据提取质量测试 — pattern/decision/score"""

import sys
from pathlib import Path

try:
    import pytest
except ImportError:
    print("pytest not installed. Skipping tests.", file=sys.stderr)
    sys.exit(0)

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE = REPO_ROOT / "examples" / "sample_analysis.md"


@pytest.fixture
def sample_vm():
    from bazi_pro.view_model import build_vm_from_analysis_text
    text = SAMPLE.read_text(encoding="utf-8")
    return build_vm_from_analysis_text(text)


class TestPatternExtraction:

    def test_pattern_not_garbage(self, sample_vm):
        """格局不应包含树形符号或层级标记"""
        p = sample_vm.verdict.pattern
        assert '├' not in p
        assert '层' not in p
        assert '不成立' not in p

    def test_pattern_is_known(self, sample_vm):
        assert sample_vm.verdict.pattern == '暗食神格'

    def test_pattern_from_tree_format(self):
        from bazi_pro.view_model import build_vm_from_analysis_text
        text = """
### 格局判定
├─ 层0 特殊格局：不成立
├─ 层1 月令本气：戊土食神→不透
├─ 层3 正官格（月令中气辛金正官透出）
├─ 层5 成败：成格
"""
        vm = build_vm_from_analysis_text(text)
        assert vm.verdict.pattern == '正官格'

    def test_pattern_from_definitive_statement(self):
        from bazi_pro.view_model import build_vm_from_analysis_text
        text = """
按《子平真诠》论，实质是 **建禄格**，透官杀混杂。
"""
        vm = build_vm_from_analysis_text(text)
        assert vm.verdict.pattern == '建禄格'

    def test_pattern_fallback_to_line(self):
        from bazi_pro.view_model import build_vm_from_analysis_text
        text = """
综合格局：从强格
用神：火
"""
        vm = build_vm_from_analysis_text(text)
        assert vm.verdict.pattern == '从强格'

    def test_pattern_skip_section_header(self):
        from bazi_pro.view_model import build_vm_from_analysis_text
        text = """
## 第三步：格局判定（六层筛查）

这是正文内容，没有明确格局名。
"""
        vm = build_vm_from_analysis_text(text)
        assert '筛查' not in vm.verdict.pattern

    def test_pattern_prefers_specific_over_generic(self):
        """暗食神格 should be preferred over 食神格"""
        from bazi_pro.view_model import build_vm_from_analysis_text
        text = """
├─ 层3 暗食神格（戌中戊土食神，暗格成立）
实质是 **七杀格混官**。
"""
        vm = build_vm_from_analysis_text(text)
        assert vm.verdict.pattern == '暗食神格'


class TestDecisionExtraction:

    def test_decision_extracted(self, sample_vm):
        assert sample_vm.verdict.decision == '身弱'

    def test_decision_from_table(self):
        from bazi_pro.view_model import build_vm_from_analysis_text
        text = """
| 维度 | 得分 | 判定 |
|------|------|------|
| 得令 | -2 | 失令 |
| **综合** | **得令-2 + 得地偏** | **身旺** |
"""
        vm = build_vm_from_analysis_text(text)
        assert vm.verdict.decision == '身旺'

    def test_decision_extreme(self):
        from bazi_pro.view_model import build_vm_from_analysis_text
        text = """
| **综合** | **全面得势** | **极旺** |
"""
        vm = build_vm_from_analysis_text(text)
        assert vm.verdict.decision == '极旺'

    def test_decision_empty_when_no_table(self):
        from bazi_pro.view_model import build_vm_from_analysis_text
        text = "这是一段没有旺衰表格的文本。"
        vm = build_vm_from_analysis_text(text)
        assert vm.verdict.decision == ''


class TestPatternScore:

    def test_score_extracted(self, sample_vm):
        assert sample_vm.pattern_score == 65

    def test_score_label(self, sample_vm):
        assert sample_vm.pattern_score_label == '中等'

    def test_score_various_labels(self):
        from bazi_pro.view_model import build_vm_from_analysis_text
        cases = [
            ("评分：85/100 上等", 85, '上等'),
            ("评分：45/100 下等", 45, '下等'),
            ("评分：72/100 中上等", 72, '中上等'),
            ("评分：55/100 中下等", 55, '中下等'),
            ("评分：65/100 中等", 65, '中等'),
        ]
        for text, expected_score, expected_label in cases:
            vm = build_vm_from_analysis_text(text)
            assert vm.pattern_score == expected_score, f"Failed for: {text}"
            assert vm.pattern_score_label == expected_label, f"Failed for: {text}"


class TestConsumerReportPersonalization:
    """验证提取修复后 consumer 报告的个性化程度"""

    def test_cover_shows_pattern(self, sample_vm):
        from bazi_pro.ui.consumer_report import render_consumer_report
        text = SAMPLE.read_text(encoding="utf-8")
        html = render_consumer_report(sample_vm, raw_markdown=text)
        assert '暗食神格' in html

    def test_summary_shows_pattern(self, sample_vm):
        from bazi_pro.ui.consumer_report import render_consumer_report
        text = SAMPLE.read_text(encoding="utf-8")
        html = render_consumer_report(sample_vm, raw_markdown=text)
        assert '暗食神格' in html
        assert '正格' not in html or '暗食神格' in html

    def test_narrative_uses_correct_strength(self, sample_vm):
        from bazi_pro.ui.consumer_report import _narrative_personality
        html = _narrative_personality(sample_vm)
        assert '合作' in html or '借力' in html or '偏柔' in html

    def test_narrative_uses_pattern_branch(self, sample_vm):
        from bazi_pro.ui.consumer_report import _narrative_personality
        html = _narrative_personality(sample_vm)
        assert '才华' in html or '创造力' in html

    def test_description_not_truncated_mid_word(self, sample_vm):
        from bazi_pro.ui.consumer_report import render_consumer_report
        text = SAMPLE.read_text(encoding="utf-8")
        html = render_consumer_report(sample_vm, raw_markdown=text)
        import re
        # Only match cr-id-desc divs in the body (after </style>)
        body = html.split('</style>')[-1] if '</style>' in html else html
        descs = re.findall(r'class="cr-id-desc">([^<]+)', body)
        for desc in descs:
            if len(desc) > 10:
                last_char = desc[-1]
                assert last_char in '。，、；）' or len(desc) < 50, \
                    f"Description may be truncated mid-sentence: ...{desc[-10:]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
