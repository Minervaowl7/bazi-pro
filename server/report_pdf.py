"""
八字详批报告 PDF 生成模块
使用 weasyprint 将 HTML 模板转为高质量 PDF
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from html import escape


logger = logging.getLogger("bazi-pro")

# ──────────────────────────────────────────────
# Markdown → HTML 转换（轻量级，无外部依赖）
# ──────────────────────────────────────────────

def _md_to_html(text: str) -> str:
    """简化的 Markdown → HTML 转换"""
    if not text:
        return ""

    lines = text.split("\n")
    out: list[str] = []
    in_code = False

    for line in lines:
        # Code fence
        if line.strip().startswith("```"):
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                out.append("<pre><code>")
                in_code = True
            continue

        if in_code:
            out.append(escape(line))
            continue

        # 空行
        if not line.strip():
            out.append("")
            continue

        # 标题
        m = re.match(r"^(#{1,4})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            title = _inline(m.group(2))
            out.append(f"<h{level}>{title}</h{level}>")
            continue

        # 水平线
        if line.strip() in ("---", "***", "___"):
            out.append("<hr>")
            continue

        # 无序列表
        ul = re.match(r"^[\-\*]\s+(.+)$", line)
        if ul:
            out.append(f"<li>{_inline(ul.group(1))}</li>")
            continue

        # 有序列表
        ol = re.match(r"^\d+\.\s+(.+)$", line)
        if ol:
            out.append(f"<li>{_inline(ol.group(1))}</li>")
            continue

        # 引用
        bq = re.match(r"^>\s?(.*)$", line)
        if bq:
            out.append(f"<blockquote><p>{_inline(bq.group(1))}</p></blockquote>")
            continue

        # 普通段落
        out.append(f"<p>{_inline(line)}</p>")

    if in_code:
        out.append("</code></pre>")

    return "\n".join(out)


def _inline(s: str) -> str:
    """行内格式：粗体、斜体、行内代码"""
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


# ──────────────────────────────────────────────
# 章节结构
# ──────────────────────────────────────────────

CHAPTERS = [
    ("overview", "壹", "命盘总览"),
    ("past_validation", "贰", "过往验证"),
    ("future_luck", "叁", "运势流年"),
    ("career_wealth", "肆", "事业财运"),
    ("marriage_love", "伍", "婚恋感情"),
    ("family", "陆", "家庭六亲"),
    ("health", "柒", "健康提示"),
    ("guidance", "捌", "趋吉避凶"),
]


# ──────────────────────────────────────────────
# CSS 样式
# ──────────────────────────────────────────────

CSS = """
@page {
    size: A4;
    margin: 25mm 20mm 30mm 20mm;
    @top-center {
        content: "详批报告";
        font-size: 9pt;
        color: #999;
        font-family: "Noto Serif CJK SC", "SimSun", "STSong", serif;
    }
    @bottom-center {
        content: counter(page);
        font-size: 9pt;
        color: #999;
    }
}

@page :first {
    @top-center { content: none; }
    @bottom-center { content: none; }
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --ink: #241a14;
    --ink-light: #4a3a2a;
    --accent: #8a3b2a;
    --gold: #b99a5b;
    --bg-page: #f7f1e8;
    --bg-card: #fffaf2;
    --border-light: #e8d9c4;
}

body {
    font-family: "Noto Serif CJK SC", "Source Han Serif SC", "SimSun", "STSong", "Microsoft YaHei", serif;
    font-size: 11pt;
    line-height: 1.8;
    color: var(--ink);
    background: white;
    -webkit-font-smoothing: antialiased;
}

/* ── 封面 ── */
.cover {
    text-align: center;
    padding: 60pt 40pt 40pt;
    page-break-after: always;
    position: relative;
}

.cover::before {
    content: "";
    display: block;
    width: 40pt;
    height: 2pt;
    background: var(--accent);
    margin: 0 auto 30pt;
}

.cover .day-master-circle {
    width: 72pt;
    height: 72pt;
    border-radius: 50%;
    background: linear-gradient(135deg, #c96442, #a04030);
    margin: 0 auto 20pt;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 32pt;
    font-weight: 700;
}

.cover h1 {
    font-size: 24pt;
    font-weight: 700;
    color: var(--ink);
    margin-bottom: 4pt;
    letter-spacing: 0.1em;
}

.cover .subtitle {
    font-size: 11pt;
    color: #999;
    margin-bottom: 24pt;
}

.cover .bazi-line {
    font-size: 16pt;
    font-weight: 600;
    color: var(--ink);
    letter-spacing: 0.15em;
    margin-bottom: 24pt;
}

.cover .info-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8pt;
    max-width: 400pt;
    margin: 0 auto 30pt;
}

.cover .info-item {
    padding: 10pt 8pt;
    border: 1pt solid var(--border-light);
    border-radius: 4pt;
    text-align: center;
}

.cover .info-label {
    font-size: 8pt;
    color: #999;
    margin-bottom: 4pt;
}

.cover .info-value {
    font-size: 10pt;
    font-weight: 600;
    color: var(--accent);
}

.cover .disclaimer {
    font-size: 8pt;
    color: #bbb;
    margin-top: 20pt;
}

/* ── 目录 ── */
.toc {
    page-break-after: always;
    padding: 20pt 0;
}

.toc h2 {
    font-size: 16pt;
    color: var(--ink);
    margin-bottom: 20pt;
    padding-bottom: 8pt;
    border-bottom: 2pt solid var(--accent);
}

.toc ol {
    list-style: none;
    padding: 0;
}

.toc li {
    padding: 8pt 0;
    border-bottom: 1pt dotted var(--border-light);
    font-size: 11pt;
    display: flex;
    align-items: baseline;
}

.toc .num {
    display: inline-block;
    width: 24pt;
    font-weight: 700;
    color: var(--accent);
    font-family: "Noto Serif CJK SC", serif;
}

/* ── 章节 ── */
.chapter {
    page-break-before: always;
}

.chapter:first-of-type {
    page-break-before: avoid;
}

.chapter-header {
    display: flex;
    align-items: center;
    gap: 12pt;
    margin-bottom: 16pt;
    padding-bottom: 10pt;
    border-bottom: 2pt solid var(--accent);
}

.chapter-num {
    width: 28pt;
    height: 28pt;
    border: 2pt solid var(--accent);
    border-radius: 3pt;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11pt;
    font-weight: 700;
    color: var(--accent);
    font-family: "Noto Serif CJK SC", serif;
    flex-shrink: 0;
}

.chapter-title {
    font-size: 14pt;
    font-weight: 700;
    color: var(--ink);
    font-family: "Noto Serif CJK SC", serif;
    letter-spacing: 0.05em;
}

/* ── 正文 ── */
.content p {
    margin-bottom: 10pt;
    text-indent: 2em;
    text-align: justify;
}

.content p:first-child {
    text-indent: 0;
}

.content strong {
    display: block;
    font-size: 11pt;
    font-weight: 700;
    color: var(--ink);
    margin-top: 14pt;
    margin-bottom: 6pt;
    text-indent: 0;
}

.content strong:first-child {
    margin-top: 0;
}

.content em {
    color: var(--accent);
    font-style: normal;
}

.content blockquote {
    border-left: 3pt solid var(--accent);
    padding-left: 10pt;
    margin: 10pt 0;
    opacity: 0.9;
    font-style: italic;
    text-indent: 0;
}

.content blockquote p {
    text-indent: 0;
}

.content ul, .content ol {
    padding-left: 20pt;
    margin: 6pt 0;
}

.content li {
    margin: 4pt 0;
}

.content code {
    background: #f5f0e8;
    padding: 1pt 4pt;
    border-radius: 2pt;
    font-size: 9pt;
}

.content pre {
    background: #f5f0e8;
    padding: 10pt;
    border-radius: 4pt;
    margin: 10pt 0;
    overflow-x: auto;
    page-break-inside: avoid;
}

.content pre code {
    background: none;
    padding: 0;
}

/* ── 引用 ── */
.citation {
    margin-top: 14pt;
    padding: 8pt 12pt;
    border-left: 3pt solid var(--gold);
    background: rgba(185, 154, 91, 0.06);
    border-radius: 0 4pt 4pt 0;
    page-break-inside: avoid;
}

.citation-label {
    font-size: 8pt;
    font-weight: 600;
    color: var(--gold);
    margin-bottom: 4pt;
    letter-spacing: 0.05em;
}

.citation-text {
    font-size: 9pt;
    color: #999;
    line-height: 1.6;
}

/* ── 尾页 ── */
.footer-page {
    page-break-before: always;
    text-align: center;
    padding-top: 60pt;
}

.footer-page .line {
    width: 40pt;
    height: 2pt;
    background: var(--accent);
    margin: 0 auto 20pt;
}

.footer-page p {
    font-size: 9pt;
    color: #999;
    line-height: 1.8;
    text-indent: 0;
    margin-bottom: 6pt;
}

.footer-page .generated-at {
    font-size: 8pt;
    color: #bbb;
    margin-top: 30pt;
}
"""


# ──────────────────────────────────────────────
# HTML 模板生成
# ──────────────────────────────────────────────

def build_report_html(
    report_data: dict,
    analysis_data: dict,
    name: str = "",
) -> str:
    """生成完整的 HTML 报告"""

    # 提取分析数据
    result = analysis_data.get("full_result") or analysis_data.get("result") or {}
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except Exception:
            result = {}

    validation = result.get("validation") or {}
    pattern = result.get("pattern") or {}
    yongshen = result.get("yongshen") or {}
    strength = result.get("strength") or {}
    wangshuai = strength.get("wangshuai") or {}

    day_master = validation.get("day_master") or analysis_data.get("day_master") or ""
    bazi = validation.get("bazi") or ""
    zodiac = validation.get("zodiac") or ""
    pattern_str = pattern.get("pattern") or analysis_data.get("pattern") or ""
    yongshen_str = yongshen.get("yongshen") or analysis_data.get("yongshen") or ""
    wangshuai_str = wangshuai.get("verdict") or ""

    display_name = name or "命主"
    now_str = datetime.now().strftime("%Y年%m月%d日")

    # 提取报告章节
    sections = report_data.get("sections") or {}
    citations = report_data.get("citations") or {}

    # ── 封面 ──
    cover_html = f"""
    <div class="cover">
        <div class="day-master-circle">{escape(day_master)}</div>
        <h1>{escape(display_name)}</h1>
        <div class="subtitle">详批报告 · {now_str}</div>
        <div class="bazi-line">{escape(bazi)}</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">格局</div>
                <div class="info-value">{escape(pattern_str)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">用神</div>
                <div class="info-value">{escape(yongshen_str)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">旺衰</div>
                <div class="info-value">{escape(wangshuai_str)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">生肖</div>
                <div class="info-value">{escape(zodiac)}</div>
            </div>
        </div>
        <div class="disclaimer">本报告专为 {escape(display_name)} 生成 · 基于确定性命理计算</div>
    </div>
    """

    # ── 目录 ──
    toc_items = []
    for key, num, title in CHAPTERS:
        if sections.get(key):
            toc_items.append(f'<li><span class="num">{num}</span> {escape(title)}</li>')
    toc_html = f"""
    <div class="toc">
        <h2>目录</h2>
        <ol>{"".join(toc_items)}</ol>
    </div>
    """

    # ── 章节 ──
    chapters_html = ""
    for key, num, title in CHAPTERS:
        content = sections.get(key)
        if not content:
            continue
        citation = citations.get(key) or ""
        content_html = _md_to_html(content)
        citation_html = ""
        if citation.strip():
            citation_html = f"""
            <div class="citation">
                <div class="citation-label">典籍引证</div>
                <div class="citation-text">{escape(citation)}</div>
            </div>
            """
        chapters_html += f"""
        <div class="chapter">
            <div class="chapter-header">
                <div class="chapter-num">{num}</div>
                <div class="chapter-title">{escape(title)}</div>
            </div>
            <div class="content">
                {content_html}
                {citation_html}
            </div>
        </div>
        """

    # ── 尾页 ──
    footer_html = f"""
    <div class="footer-page">
        <div class="line"></div>
        <p>本报告基于确定性命理计算生成，仅供参考，不构成任何决策依据</p>
        <p>报告内容由 AI 辅助生成，已通过数据验证层确保准确性</p>
        <p class="generated-at">生成时间：{now_str}</p>
    </div>
    """

    # ── 组装 ──
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>详批报告 - {escape(display_name)}</title>
    <style>{CSS}</style>
</head>
<body>
    {cover_html}
    {toc_html}
    {chapters_html}
    {footer_html}
</body>
</html>"""


# ──────────────────────────────────────────────
# PDF 生成
# ──────────────────────────────────────────────

def generate_report_pdf(
    report_data: dict,
    analysis_data: dict,
    name: str = "",
) -> bytes:
    """生成 PDF 报告，返回二进制数据"""

    html_content = build_report_html(report_data, analysis_data, name)

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except ImportError:
        logger.warning("weasyprint 未安装，尝试使用 pdfkit")
        try:
            import pdfkit
            pdf_bytes = pdfkit.from_string(html_content, False)
            return pdf_bytes
        except Exception as e:
            raise RuntimeError(
                f"PDF 生成失败：需要安装 weasyprint 或 pdfkit。"
                f"请运行 pip install weasyprint（需要 GTK+）或 pip install pdfkit（需要 wkhtmltopdf）。"
                f"原始错误：{e}"
            )
