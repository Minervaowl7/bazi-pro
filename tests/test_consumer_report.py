"""消费级报告结构完整性和质量测试"""

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


@pytest.fixture
def consumer_html(sample_vm):
    from bazi_pro.ui.consumer_report import render_consumer_report
    text = SAMPLE.read_text(encoding="utf-8")
    return render_consumer_report(sample_vm, raw_markdown=text)


class TestConsumerReportStructure:

    def test_all_sections_present(self, consumer_html):
        required = [
            'cr-cover', 'cr-guide', 'cr-summary', 'cr-dimensions',
            'cr-advice', 'glossary-section', 'cr-appendix', 'cr-disclaimer',
        ]
        for section in required:
            assert section in consumer_html, f"Missing section: {section}"

    def test_six_dimensions_present(self, consumer_html):
        dims = ['性格底色', '事业方向', '财运模式', '感情婚姻', '健康提示', '近期运势']
        for dim in dims:
            assert dim in consumer_html, f"Missing dimension: {dim}"

    def test_has_viewport_meta(self, consumer_html):
        assert 'viewport' in consumer_html
        assert 'width=device-width' in consumer_html

    def test_has_dark_mode(self, consumer_html):
        assert 'prefers-color-scheme' in consumer_html

    def test_has_progress_bar(self, consumer_html):
        assert 'cr-progress' in consumer_html

    def test_has_reading_guide(self, consumer_html):
        assert '阅读指南' in consumer_html

    def test_appendix_is_collapsible(self, consumer_html):
        assert '<details class="cr-appendix">' in consumer_html

    def test_disclaimer_present(self, consumer_html):
        assert '免责声明' in consumer_html
        assert '不构成任何人生决策的依据' in consumer_html


class TestGlossarySystem:

    def test_glossary_has_entries(self):
        from bazi_pro.ui.glossary import GLOSSARY
        assert len(GLOSSARY) >= 60

    def test_annotate_terms_works(self):
        from bazi_pro.ui.glossary import annotate_terms
        text = '日主身弱，用神为土，食神制杀有力。'
        result, used = annotate_terms(text)
        assert len(used) >= 3
        assert 'term-tip' in result
        assert 'data-tip' in result

    def test_glossary_section_renders(self):
        from bazi_pro.ui.glossary import render_glossary_section
        html = render_glossary_section({'用神', '身弱', '食神'})
        assert '术语小词典' in html
        assert 'gloss-item' in html

    def test_tooltip_css_present(self, consumer_html):
        assert '.term-tip' in consumer_html
        assert 'data-tip' in consumer_html

    def test_glossary_entries_in_report(self, consumer_html):
        assert 'gloss-item' in consumer_html


class TestContentQuality:

    def test_no_banned_words(self, consumer_html):
        banned = ['必死', '必亡', '绝对', '一定会', '注定', '命中注定必须']
        for word in banned:
            assert word not in consumer_html, f"Banned word found: {word}"

    def test_minimum_content_length(self, consumer_html):
        assert len(consumer_html) > 15000, "Report too short"

    def test_no_raw_technical_in_body(self, consumer_html):
        import re
        body_match = re.search(
            r'cr-dimensions.*?(?=glossary-section|cr-appendix)',
            consumer_html, re.DOTALL
        )
        if body_match:
            body = body_match.group()
            assert '层0' not in body
            assert 'BM25' not in body
            assert '├─' not in body


class TestIntegration:

    def test_import_from_ui(self):
        from bazi_pro.ui import render_consumer_report
        assert callable(render_consumer_report)

    def test_generate_report_consumer_mode(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, str(REPO_ROOT / "bazi_pro" / "generate_report.py"),
             "--input", str(SAMPLE), "--theme", "consumer",
             "--format", "html", "--output", str(REPO_ROOT / "consumer_test_ci.html")],
            capture_output=True, text=True, timeout=30
        )
        assert r.returncode == 0, f"exit={r.returncode} stderr={r.stderr}"
        output = REPO_ROOT / "consumer_test_ci.html"
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert '命理解读报告' in content
        output.unlink()

    def test_mode_alias_works(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, str(REPO_ROOT / "bazi_pro" / "generate_report.py"),
             "--input", str(SAMPLE), "--mode", "consumer",
             "--format", "html", "--output", str(REPO_ROOT / "consumer_test_mode.html")],
            capture_output=True, text=True, timeout=30
        )
        assert r.returncode == 0, f"exit={r.returncode} stderr={r.stderr}"
        output = REPO_ROOT / "consumer_test_mode.html"
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert 'cr-cover' in content
        output.unlink()


class TestRobustness:

    def test_empty_vm_does_not_crash(self):
        from bazi_pro.ui.consumer_report import render_consumer_report
        from bazi_pro.view_model import DashboardVM, VerdictVM, WuxingVM
        vm = DashboardVM(
            bazi='', gender='', solar_date='', lunar_date='', zodiac='', day_master='',
            pillars=[], verdict=VerdictVM(
                day_master='', pattern='', decision='', yongshen=[], xishen=[],
                jishen=[], confidence=0.0, summary_line=''
            ),
            wuxing=WuxingVM(wood=20, fire=20, earth=20, metal=20, water=20),
            evidence=[], relations=[], dayun=[],
            pattern_score=0, pattern_score_label=''
        )
        html = render_consumer_report(vm)
        assert '命理解读报告' in html
        assert len(html) > 5000

    def test_partial_vm_fields(self):
        from bazi_pro.ui.consumer_report import render_consumer_report
        from bazi_pro.view_model import DashboardVM, VerdictVM, WuxingVM
        vm = DashboardVM(
            bazi='甲子 乙丑 丙寅 丁卯', gender='男', solar_date='', lunar_date='',
            zodiac='', day_master='丙',
            pillars=[], verdict=VerdictVM(
                day_master='丙火', pattern='正官格', decision='身弱',
                yongshen=['木'], xishen=['水'], jishen=['土'],
                confidence=0.75, summary_line=''
            ),
            wuxing=WuxingVM(wood=25, fire=15, earth=30, metal=10, water=20),
            evidence=[], relations=[], dayun=[],
            pattern_score=65, pattern_score_label='中等'
        )
        html = render_consumer_report(vm)
        assert '正官格' in html
        assert '木' in html

    def test_tooltip_no_nested_html(self, consumer_html):
        import re
        nested = re.findall(r'data-tip="[^"]*<span', consumer_html)
        assert len(nested) == 0, f"Found nested HTML in tooltips: {nested[:3]}"

    def test_technical_mode_unchanged(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, str(REPO_ROOT / "bazi_pro" / "generate_report.py"),
             "--input", str(SAMPLE), "--theme", "report",
             "--format", "html", "--output", str(REPO_ROOT / "tech_test.html")],
            capture_output=True, text=True, timeout=30
        )
        assert r.returncode == 0, f"exit={r.returncode} stderr={r.stderr}"
        output = REPO_ROOT / "tech_test.html"
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        # Technical report should NOT have consumer-specific elements
        assert 'cr-cover' not in content
        assert 'cr-guide' not in content
        assert 'term-tip' not in content
        # But should have traditional report elements
        assert '目录' in content or '八字' in content
        output.unlink()

    def test_appendix_contains_original_content(self, consumer_html):
        assert 'appendix-body' in consumer_html
        assert '第' in consumer_html  # Original step content preserved


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
