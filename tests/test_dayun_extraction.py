"""大运提取正则修复验证测试"""

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


class TestDayunExtraction:

    def test_dayun_not_empty(self, sample_vm):
        assert len(sample_vm.dayun) > 0, "dayun should not be empty"

    def test_dayun_count(self, sample_vm):
        assert len(sample_vm.dayun) == 11

    def test_age_range_format(self, sample_vm):
        for d in sample_vm.dayun:
            assert '-' in d.age_range or '~' in d.age_range

    def test_ganzhi_valid(self, sample_vm):
        gans = set('甲乙丙丁戊己庚辛壬癸')
        zhis = set('子丑寅卯辰巳午未申酉戌亥')
        for d in sample_vm.dayun:
            assert len(d.gan_zhi) == 2
            assert d.gan_zhi[0] in gans
            assert d.gan_zhi[1] in zhis

    def test_assessment_values(self, sample_vm):
        valid = {'大吉', '吉', '平', '凶', '大凶', '平偏吉', '平偏凶'}
        for d in sample_vm.dayun:
            assert d.assessment in valid, f"Invalid assessment: {d.assessment}"

    def test_bold_ganzhi_extracted(self, sample_vm):
        """干支列带 **粗体** 标记时仍能正确提取"""
        assert any(d.gan_zhi == '癸亥' for d in sample_vm.dayun)
        assert any(d.gan_zhi == '丙寅' for d in sample_vm.dayun)

    def test_emoji_assessment_stripped(self, sample_vm):
        """吉凶列带 emoji 标记时仍能正确提取"""
        gui_hai = next(d for d in sample_vm.dayun if d.gan_zhi == '癸亥')
        assert gui_hai.assessment == '凶'
        bing_yin = next(d for d in sample_vm.dayun if d.gan_zhi == '丙寅')
        assert bing_yin.assessment == '大吉'

    def test_qiyun_age(self, sample_vm):
        assert sample_vm.qiyun_age == '9'

    def test_shishen_populated(self, sample_vm):
        """十神字段应有内容"""
        non_empty = [d for d in sample_vm.dayun if d.shishen]
        assert len(non_empty) >= 8


class TestDayunFiveColumnFormat:
    """测试 5 列格式的大运表兼容性"""

    def test_five_column_table(self):
        from bazi_pro.view_model import build_vm_from_analysis_text
        text = """
## 第六步：大运逐运分析

### 6.1 大运总览

| 大运 | 年龄 | 干支 | 十神 | 吉凶 |
|------|------|------|------|------|
| 第1步 | 9-18 | 癸亥 | 正官 | 凶 |
| 第2步 | 19-28 | 甲子 | 偏印 | 吉 |
| 第3步 | 29-38 | 乙丑 | 正印 | 大吉 |
"""
        vm = build_vm_from_analysis_text(text)
        assert len(vm.dayun) == 3
        assert vm.dayun[0].gan_zhi == '癸亥'
        assert vm.dayun[0].assessment == '凶'
        assert vm.dayun[2].assessment == '大吉'

    def test_six_column_with_bold_and_emoji(self):
        from bazi_pro.view_model import build_vm_from_analysis_text
        text = """
### 6.1 大运总览（9岁起运）

| 大运 | 年龄 | 干支 | 天干 | 地支 | 吉凶 |
|------|------|------|------|------|------|
| 起运前 | 0-8 | 壬戌(月柱) | 七杀 | 食神 | 平偏凶 |
| 第1步 | 9-18 | **癸亥** | 正官 | 七杀+偏印 | **凶** ⚠️ |
| 第2步 | 19-28 | **甲子** | 偏印 | 正官 | 平偏吉 |
| 第3步 | 29~38 | **乙丑** | 正印 | 伤官 | **大吉** ⭐ |
"""
        vm = build_vm_from_analysis_text(text)
        assert len(vm.dayun) == 4
        assert vm.dayun[0].gan_zhi == '壬戌'
        assert vm.dayun[0].assessment == '平偏凶'
        assert vm.dayun[1].gan_zhi == '癸亥'
        assert vm.dayun[1].assessment == '凶'
        assert vm.dayun[2].age_range == '19-28'
        assert vm.dayun[3].age_range == '29~38'
        assert vm.dayun[3].assessment == '大吉'


class TestConsumerReportWithDayun:
    """修复后 consumer 报告时间轴和叙事应正常渲染"""

    def test_timeline_renders(self, sample_vm):
        from bazi_pro.ui.consumer_report import _render_timeline
        html = _render_timeline(sample_vm)
        assert html != '', "Timeline should not be empty when dayun exists"
        assert 'tl-track' in html
        assert '人生节奏' in html

    def test_timeline_has_items(self, sample_vm):
        from bazi_pro.ui.consumer_report import _render_timeline
        html = _render_timeline(sample_vm)
        assert 'tl-item' in html
        assert '39-48' in html  # 大吉运应出现

    def test_career_narrative_has_timing(self, sample_vm):
        from bazi_pro.ui.consumer_report import _narrative_career
        html = _narrative_career(sample_vm)
        assert '大运' in html or '黄金期' in html

    def test_current_narrative_uses_dayun(self, sample_vm):
        from bazi_pro.ui.consumer_report import _narrative_current
        html = _narrative_current(sample_vm)
        assert '壬戌' in html or '0-8' in html

    def test_full_consumer_report_has_timeline(self, sample_vm):
        from bazi_pro.ui.consumer_report import render_consumer_report
        text = SAMPLE.read_text(encoding="utf-8")
        html = render_consumer_report(sample_vm, raw_markdown=text)
        assert 'cr-timeline' in html
        assert 'tl-track' in html


class TestReportModeUnchanged:
    """确认 report 模式不受影响"""

    def test_technical_report_still_works(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, str(REPO_ROOT / "bazi_pro" / "generate_report.py"),
             "--input", str(SAMPLE), "--theme", "report",
             "--format", "html", "--output", str(REPO_ROOT / "dayun_test_report.html")],
            capture_output=True, text=True, timeout=30
        )
        assert r.returncode == 0, f"exit={r.returncode} stderr={r.stderr}"
        output = REPO_ROOT / "dayun_test_report.html"
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert 'cr-timeline' not in content
        output.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
