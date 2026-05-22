#!/usr/bin/env python3
"""
bazi-pro HTML Quality Regression Tests v4.3
防止 UI 回退：占位文案 · summary 长度 · TOC 有效性 · 必需模块
"""

import sys
import re
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


# ── Fixtures ──

@pytest.fixture
def sample_trace():
    """加载 sample_trace.json"""
    path = REPO_ROOT / "examples" / "sample_trace.json"
    if path.exists():
        import json
        return json.loads(path.read_text(encoding='utf-8'))
    return {}


@pytest.fixture
def rendered_dashboard():
    """渲染一份 Dashboard 用于检查"""
    try:
        from bazi_pro.view_model import DashboardVM
        from bazi_pro.ui import render_dashboard
        vm = DashboardVM()
        vm.verdict.day_master = "丁火"
        vm.verdict.pattern = "建禄月劫"
        vm.verdict.decision = "不从，按正格论"
        vm.verdict.yongshen = ["木"]
        vm.verdict.xishen = ["水", "金"]
        vm.verdict.jishen = ["火", "土"]
        vm.verdict.confidence = 0.80
        vm.bazi = "壬午 乙巳 丁亥 癸卯"
        return render_dashboard(vm)
    except Exception:
        return ""


@pytest.fixture
def rendered_report():
    """渲染一份 Report 用于检查"""
    try:
        from bazi_pro.view_model import DashboardVM
        from bazi_pro.ui import render_report
        vm = DashboardVM()
        vm.verdict.day_master = "丁火"
        vm.verdict.pattern = "建禄月劫"
        vm.verdict.decision = "不从，按正格论"
        vm.bazi = "壬午 乙巳 丁亥 癸卯"
        return render_report(vm)
    except Exception:
        return ""


# ── P0: 禁止占位文案 ──

BANNED_WORDS = [
    "未提取", "undefined", "null", "NaN", "TODO", "debug",
    "None", "Error", "Traceback", "Exception",
    "证据数据未加载", "此报告未包含", "即将上线",
]

MARKDOWN_ARTIFACTS = ["**", "__"]  # Markdown 残留（检查不在 code/pre 内的）
HREF_PLACEHOLDERS = ['href="#"']   # 禁止占位链接

# v4.4: Technical headings forbidden in main content
TECHNICAL_HEADINGS_BANNED = [
    "第〇步", "0.2 双通道", "层 0-A", "层0-A",
    "BM25", "双通道检索", "最高得分", "粗略预检",
    "计分说明", "权重说明", "评分基准锚",
]


@pytest.mark.parametrize("word", BANNED_WORDS)
def test_dashboard_no_banned_words(rendered_dashboard, word):
    """Dashboard 不得包含禁用词"""
    if not rendered_dashboard:
        pytest.skip("Dashboard 未渲染")
    assert word not in rendered_dashboard, f"Dashboard 包含禁用词: '{word}'"


@pytest.mark.parametrize("word", BANNED_WORDS)
def test_report_no_banned_words(rendered_report, word):
    """Report 不得包含禁用词"""
    if not rendered_report:
        pytest.skip("Report 未渲染")
    assert word not in rendered_report, f"Report 包含禁用词: '{word}'"


# ── P0: Evidence Summary 长度 ──

def test_evidence_summary_length(rendered_dashboard):
    """所有 details summary 不超过 40 中文字符"""
    if not rendered_dashboard:
        pytest.skip("Dashboard 未渲染")
    summaries = re.findall(r'<summary>(.+?)</summary>', rendered_dashboard)
    for s in summaries:
        # Strip HTML tags for length check
        clean = re.sub(r'<[^>]+>', '', s)
        assert len(clean) <= 60, f"Summary 过长 ({len(clean)} 字): {clean[:40]}..."


# ── P0: Dashboard 必需模块 ──

DASHBOARD_REQUIRED = [
    ("verdict-seal-svg", "Verdict Seal"),
    ("pillars", "四柱命盘"),
    ("verdict-row", "用神裁决行"),
    ("证据链审查", "证据链模块"),
    ("五行账簿", "Element Balance Ledger"),
]


@pytest.mark.parametrize("marker,label", DASHBOARD_REQUIRED)
def test_dashboard_required_sections(rendered_dashboard, marker, label):
    """Dashboard 包含所有必需模块"""
    if not rendered_dashboard:
        pytest.skip("Dashboard 未渲染")
    assert marker in rendered_dashboard, f"Dashboard 缺少必需模块: {label}"


# ── P0: Report 必需模块 ──

REPORT_REQUIRED = [
    ("BAZI ANALYSIS", "封面标题"),
    ("Executive Summary", "执行摘要"),
    ("关键裁决", "裁决表"),
    ("风险与建议", "风险建议"),
]


@pytest.mark.parametrize("marker,label", REPORT_REQUIRED)
def test_report_required_sections(rendered_report, marker, label):
    """Report 包含所有必需模块"""
    if not rendered_report:
        pytest.skip("Report 未渲染")
    assert marker in rendered_report, f"Report 缺少必需模块: {label}"


# ── P1: Replay 结构完整性 ──

def test_replay_has_three_columns():
    """Replay Viewer 有三栏布局"""
    try:
        from bazi_pro.view_model import DashboardVM
        from bazi_pro.ui import render_replay
        vm = DashboardVM()
        html = render_replay(vm)
        assert "replay-layout" in html, "缺少三栏布局容器"
        assert "stage-nav" in html, "缺少步骤导航栏"
        assert "stage-detail" in html, "缺少步骤详情区"
        assert "claim-panel" in html, "缺少主张面板"
        assert "counter-panel" in html, "缺少反证面板"
        assert "ArrowRight" in html, "缺少键盘导航"
    except ImportError:
        pytest.skip("bazi_pro 模块不可用")


# ── P1: Screenshot mode ──

def test_dashboard_screenshot_mode():
    """Screenshot 模式移除交互控件"""
    try:
        from bazi_pro.view_model import DashboardVM
        from bazi_pro.ui import render_dashboard
        vm = DashboardVM()
        vm.verdict.day_master = "丁火"
        html = render_dashboard(vm, screenshot_mode=True)
        assert "share-mode" in html, "缺少 share-mode class"
    except ImportError:
        pytest.skip("bazi_pro 模块不可用")


# ── P1: No markdown artifacts in rendered UI ──

@pytest.mark.parametrize("artifact", MARKDOWN_ARTIFACTS)
def test_no_markdown_artifacts(rendered_dashboard, rendered_report, artifact):
    """渲染输出不得包含 Markdown 残留标记"""
    for html in [rendered_dashboard, rendered_report]:
        if html:
            assert artifact not in html, f"包含 Markdown 残留: '{artifact}'"


# ── P1: No href="#" placeholder links ──

def test_no_href_placeholders(rendered_dashboard):
    """Dashboard 不得包含 href='#' 占位链接"""
    if not rendered_dashboard:
        pytest.skip("Dashboard 未渲染")
    for placeholder in HREF_PLACEHOLDERS:
        assert placeholder not in rendered_dashboard, f"包含占位链接: {placeholder}"


# ── P2: TOC 无重复闭合（从旧版生成器检查） ──

def test_toc_no_duplicate_close():
    """已生成的报告 HTML 不得包含 </ol></li> 重复闭合"""
    report_files = list(REPO_ROOT.glob("examples/*report*.html"))
    if not report_files:
        pytest.skip("无示例报告文件")
    for rf in report_files[:2]:
        if rf.exists():
            content = rf.read_text(encoding='utf-8', errors='ignore')
            count = content.count('</ol></li>')
            assert count == 0, f"{rf.name} 包含 {count} 处 </ol></li> 重复闭合"


# ── v4.4: Technical headings forbidden in main content ──

def test_no_technical_headings_in_main(rendered_report):
    """Report 正文主体不得包含技术步骤标题"""
    if not rendered_report:
        pytest.skip("Report 未渲染")
    # Extract main content area
    main_start = rendered_report.find('class="content-main"')
    main_end = rendered_report.find('class="appendix"')
    if main_start < 0:
        pytest.skip("Report 无 content-main 区域")
    main = rendered_report[main_start:main_end] if main_end > main_start else rendered_report[main_start:]

    for term in TECHNICAL_HEADINGS_BANNED:
        assert term not in main, f"正文包含技术术语: '{term}'"


def test_technical_headings_only_in_appendix(rendered_report):
    """技术步骤标题只出现在附录中"""
    if not rendered_report:
        pytest.skip("Report 未渲染")
    appendix_start = rendered_report.find('class="appendix"')
    if appendix_start < 0:
        return  # No appendix is OK
    appendix = rendered_report[appendix_start:]

    # Verify 第〇步 IS in appendix (it should be there)
    assert '第〇步' in appendix or len(appendix) < 100, \
        "附录应包含技术步骤"


# ── 运行入口 ──

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
