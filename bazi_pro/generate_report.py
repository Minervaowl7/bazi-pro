#!/usr/bin/env python3
"""
八字命理分析报告生成器 v1.1
用法: python3 generate_report.py --input <analysis.md> --output <report.html>
     python3 generate_report.py --input <analysis.md> --output <report.html> --pdf
     cat analysis.md | python3 generate_report.py > report.html
"""

import sys
import os
import re
import json
import argparse
import textwrap
from datetime import datetime
from html import escape
from pathlib import Path
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bazi_pro.dashboard import generate_dashboard


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

def extract_meta_from_text(text: str) -> dict:
    """从分析文本的第一步基本信息表中提取元数据"""
    meta = {}
    patterns = {
        'gender': r'\|\s*性别\s*\|\s*(.+?)\s*\|',
        'solar_date': r'\|\s*阳历\s*\|\s*(.+?)\s*\|',
        'lunar_date': r'\|\s*农历\s*\|\s*(.+?)\s*\|',
        'bazi': r'\|\s*八字\s*\|\s*(.+?)\s*\|',
        'day_master': r'\|\s*日主\s*\|\s*(.+?)\s*\|',
        'zodiac': r'\|\s*生肖\s*\|\s*(.+?)\s*\|',
        'nayin': r'\|\s*纳音\s*\|\s*(.+?)\s*\|',
        'minggong': r'\|\s*命宫\s*\|\s*(.+?)\s*\|',
        'taiyuan': r'\|\s*胎元\s*\|\s*(.+?)\s*\|',
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, text)
        if m:
            val = m.group(1).strip()
            if val and val != 'MCP 未返回':
                meta[key] = val
    return meta


def load_meta_json(path: str) -> dict:
    """从 JSON 文件加载元数据"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_metadata(cli_meta: dict, file_meta: dict, extracted_meta: dict) -> dict:
    """合并元数据，优先级: CLI > 文件 > 提取"""
    result = {}
    result.update(extracted_meta)
    result.update(file_meta)
    result.update({k: v for k, v in cli_meta.items() if v is not None})
    return result


# ---------------------------------------------------------------------------
# Content processing: section extraction + TOC
# ---------------------------------------------------------------------------

def extract_sections(text: str) -> list[dict]:
    """从 Markdown 标题提取章节树"""
    sections = []
    seen_anchors = {}
    for m in re.finditer(r'^(#{1,4})\s+(.+?)$', text, re.MULTILINE):
        level = len(m.group(1))
        title = m.group(2).strip()
        base = re.sub(r'[^\w一-鿿]', '-', title).strip('-').lower()
        if not base:
            base = 'section'
        if base in seen_anchors:
            seen_anchors[base] += 1
            anchor = f'{base}-{seen_anchors[base]}'
        else:
            seen_anchors[base] = 0
            anchor = base
        sections.append({
            'level': level,
            'title': title,
            'anchor': anchor,
            'pos': m.start()
        })
    return sections


def build_toc_html(sections: list[dict]) -> str:
    """生成带编号的目录 HTML"""
    if not sections:
        return ''
    lines = ['<nav class="toc">', '<h2>目录</h2>', '<ol class="toc-list">']
    stack = [0]
    counter = [0, 0, 0, 0, 0]

    for sec in sections:
        level = sec['level']
        # Close deeper levels
        while stack[-1] >= level:
            lines.append('</ol></li>')
            stack.pop()
        # Open new level
        while stack[-1] < level - 1:
            counter[stack[-1] + 1] = 0
            lines.append('<ol>')
            stack.append(stack[-1] + 1)
        # Add item at current level
        counter[level - 1] += 1
        parts = [str(counter[i]) for i in range(level) if counter[i] > 0]
        num = '.'.join(parts)
        lines.append(
            f'<li><a href="#{sec["anchor"]}">'
            f'<span class="toc-num">{num}</span> '
            f'{escape(sec["title"])}</a></li>'
        )
        stack.append(level)

    while len(stack) > 1:
        lines.append('</ol></li>')
        stack.pop()
    lines.append('</ol>')
    lines.append('</nav>')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Markdown to HTML (stdlib fallback, no external deps required)
# ---------------------------------------------------------------------------

_HAS_MARKDOWN_LIB = False
try:
    import markdown as md_lib
    _HAS_MARKDOWN_LIB = True
except ImportError:
    pass


def simple_md_to_html(text: str) -> str:
    """纯 stdlib 的 Markdown→HTML 转换，覆盖 SKILL.md 输出的所有格式"""
    lines = text.split('\n')
    out = []
    in_table_head = False
    in_table_body = False
    in_code = False
    in_ul = False
    in_ol = False
    in_blockquote = False
    pending_blank = False
    code_lang = ''

    def flush_inlines(s: str) -> str:
        """行内格式：粗体、斜体、行内代码、链接、删除线"""
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', s)
        s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
        s = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', s)
        s = re.sub(r'~~(.+?)~~', r'<del>\1</del>', s)
        return s

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ol:
            out.append('</ol>')
            in_ol = False
        if in_ul:
            out.append('</ul>')
            in_ul = False

    def close_table():
        nonlocal in_table_head, in_table_body
        if in_table_body:
            out.append('</tbody>')
            in_table_body = False
        if in_table_head:
            out.append('</thead>')
            in_table_head = False
        if in_table_body or in_table_head:
            out.append('</table></div>')
        in_table_head = False
        in_table_body = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code fence
        if line.strip().startswith('```'):
            if in_code:
                out.append('</code></pre>')
                in_code = False
            else:
                close_lists()
                close_table()
                code_lang = line.strip()[3:].strip()
                cls = f' class="language-{code_lang}"' if code_lang else ''
                out.append(f'<pre><code{cls}>')
                in_code = True
            i += 1
            continue

        if in_code:
            out.append(escape(line))
            i += 1
            continue

        # Blockquote
        bq = re.match(r'^>\s?(.*)$', line)
        if bq:
            close_lists()
            close_table()
            if not in_blockquote:
                out.append('<blockquote>')
                in_blockquote = True
            out.append(f'<p>{flush_inlines(bq.group(1))}</p>')
            i += 1
            continue
        elif in_blockquote:
            out.append('</blockquote>')
            in_blockquote = False

        # Table
        if '|' in line and line.strip().startswith('|'):
            close_lists()
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            is_sep = bool(re.match(r'^[\s\-:]+$', cells[0])) if cells else False
            if is_sep:
                i += 1
                continue

            if not in_table_head and not in_table_body:
                out.append('<div class="table-wrapper"><table>')
                # Check if next line is separator → this row is header
                if i + 1 < len(lines) and re.match(r'^\|[\s\-:]+\|', lines[i + 1].strip()):
                    out.append('<thead>')
                    in_table_head = True
                else:
                    out.append('<tbody>')
                    in_table_body = True
            elif in_table_head and i > 0 and not re.match(r'^\|[\s\-:]+\|', lines[i - 1].strip()):
                # transition from head to body
                out.append('</thead><tbody>')
                in_table_head = False
                in_table_body = True

            tag = 'th' if in_table_head else 'td'
            out.append('<tr>')
            for c in cells:
                out.append(f'<{tag}>{flush_inlines(c)}</{tag}>')
            out.append('</tr>')
            i += 1

            # Peek ahead: if next line is NOT a table row, close table
            if i >= len(lines) or not (lines[i].strip().startswith('|') or
                                       re.match(r'^\|[\s\-:]+\|', lines[i].strip())):
                if in_table_body:
                    out.append('</tbody>')
                if in_table_head:
                    out.append('</thead>')
                out.append('</table></div>')
                in_table_head = False
                in_table_body = False
            continue
        else:
            close_table()

        # Heading
        m = re.match(r'^(#{1,4})\s+(.+?)$', line)
        if m:
            close_lists()
            level = len(m.group(1))
            title = m.group(2).strip()
            base = re.sub(r'[^\w\u4e00-\u9fff]', '-', title).strip('-').lower() or 'section'
            base = re.sub(r'-{2,}', '-', base)  # collapse multiple dashes
            out.append(f'<h{level} id="{base}">{flush_inlines(title)}</h{level}>')
            i += 1
            continue

        # Horizontal rule
        if line.strip() == '---' or line.strip() == '***':
            close_lists()
            out.append('<hr>')
            i += 1
            continue

        # Unordered list
        ul = re.match(r'^(\s*)[\-*]\s+(.+)$', line)
        if ul:
            if in_ol:
                out.append('</ol>')
                in_ol = False
            if not in_ul:
                out.append('<ul>')
                in_ul = True
            out.append(f'<li>{flush_inlines(ul.group(2))}</li>')
            i += 1
            # Peek ahead
            if i >= len(lines) or not re.match(r'^(\s*)[\-*]\s+', lines[i]):
                out.append('</ul>')
                in_ul = False
            continue

        # Ordered list
        ol = re.match(r'^(\s*)\d+[\.\)]\s+(.+)$', line)
        if ol:
            if in_ul:
                out.append('</ul>')
                in_ul = False
            if not in_ol:
                out.append('<ol>')
                in_ol = True
            out.append(f'<li>{flush_inlines(ol.group(2))}</li>')
            i += 1
            if i >= len(lines) or not re.match(r'^(\s*)\d+[\.\)]\s+', lines[i]):
                out.append('</ol>')
                in_ol = False
            continue

        # ASCII art and box-drawing lines
        if re.search(r'[█├└│┌┤─┬┴┼╔╗╚╝║═]', line):
            close_lists()
            out.append(f'<pre class="ascii-art">{escape(line)}</pre>')
            i += 1
            continue

        # Blank line
        if not line.strip():
            close_lists()
            pending_blank = True
            i += 1
            continue

        # Regular paragraph
        close_lists()
        out.append(f'<p>{flush_inlines(line)}</p>')
        i += 1

    # Final cleanup
    if in_blockquote:
        out.append('</blockquote>')
    close_lists()
    close_table()
    if in_code:
        out.append('</code></pre>')

    return '\n'.join(out)


def markdown_to_html(text: str) -> str:
    """最佳可用方法转换 Markdown → HTML"""
    if _HAS_MARKDOWN_LIB:
        return md_lib.markdown(
            text,
            extensions=['toc', 'tables', 'fenced_code', 'sane_lists']
        )
    return simple_md_to_html(text)


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

def generate_html_report(meta: dict, body_text: str,
                         report_title: str, report_date: str) -> str:
    """生成完整 HTML5 报告（内嵌 CSS + 中国传统美学排版）"""

    sections = extract_sections(body_text)
    toc_html = build_toc_html(sections)
    body_html = markdown_to_html(body_text)

    # Cover metadata table
    meta_rows = []
    meta_fields = [
        ('gender', '性别'), ('solar_date', '阳历'), ('lunar_date', '农历'),
        ('bazi', '八字'), ('day_master', '日主'), ('zodiac', '生肖'),
        ('nayin', '纳音'), ('minggong', '命宫'), ('taiyuan', '胎元'),
    ]
    for key, label in meta_fields:
        if key in meta and meta[key]:
            meta_rows.append(
                f'<tr><td class="meta-label">{label}</td>'
                f'<td>{escape(meta[key])}</td></tr>'
            )
    meta_table_html = '\n'.join(meta_rows) if meta_rows else ''

    css = CSS_TRADITIONAL if not globals().get('_use_modern', False) else CSS_MODERN

    return HTML_TEMPLATE.format(
        title=escape(report_title),
        css=css,
        report_title=escape(report_title),
        report_date=escape(report_date),
        meta_table=meta_table_html,
        decoration='<div class="decoration"></div>' if meta_table_html else '',
        toc=toc_html,
        body=body_html,
    )


CSS_TRADITIONAL = '''
/* ==== Font face for emoji ==== */
@font-face {
    font-family: "Noto Color Emoji";
    src: local("Noto Color Emoji");
    font-display: swap;
}

/* ==== Reset & Base ==== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --ink: #2c1810;
    --ink-light: #5a3a1a;
    --accent: #8b2500;
    --accent-soft: #a0522d;
    --gold: #b8860b;
    --bg-page: #f5f0e8;
    --bg-card: #fffdf7;
    --bg-warm: #fdfaf3;
    --bg-cream: #fdf5e6;
    --border-light: #e8d5c4;
    --border-soft: #e0d0c0;
    --shadow: 0 2px 32px rgba(44,24,16,0.07);
}

body {
    font-family: "Noto Serif CJK SC", "DejaVu Serif", "Noto Color Emoji", "SimSun", "STSong", "Microsoft YaHei", serif;
    font-size: 15px; line-height: 1.9; color: var(--ink); background: var(--bg-page);
    -webkit-font-smoothing: antialiased;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ==== Page container ==== */
.page {
    max-width: 780px; margin: 24px auto 48px;
    background: var(--bg-card); box-shadow: var(--shadow);
    border-radius: 2px;
}

/* ==== Cover ==== */
.cover {
    text-align: center; padding: 72px 64px 56px;
    border-bottom: 1px solid var(--border-light);
    background: linear-gradient(180deg, #fffdf7 0%, #fef9f0 40%, #fdf5e8 100%);
    position: relative;
}
.cover::before {
    content: "";
    display: block; width: 48px; height: 2px;
    background: var(--accent); margin: 0 auto 36px;
}
.cover h1 {
    font-size: 30px; font-weight: 700; color: var(--accent);
    letter-spacing: 6px; margin-bottom: 12px; line-height: 1.3;
}
.cover .subtitle {
    font-size: 15px; color: var(--accent-soft); margin-bottom: 28px;
    letter-spacing: 2px;
}
.cover .date {
    font-size: 13px; color: #999; margin-bottom: 28px;
}
.cover .meta-table {
    margin: 20px auto 0; border-collapse: collapse;
    display: inline-table;
}
.cover .meta-table td {
    padding: 5px 18px; font-size: 14px; text-align: left;
    border-bottom: 1px dotted var(--border-soft);
}
.cover .meta-table .meta-label {
    color: var(--accent-soft); font-weight: 600;
    text-align: right; white-space: nowrap; padding-right: 8px;
}
.cover .decoration {
    margin: 36px auto 0; width: 48px; height: 1px; background: var(--gold);
}

/* ==== TOC ==== */
.toc {
    margin: 0 64px 48px; padding: 28px 36px;
    background: var(--bg-warm);
    border-left: 3px solid var(--accent);
    border-radius: 0 2px 2px 0;
}
.toc h2 {
    font-size: 18px; color: var(--accent); margin-bottom: 14px;
    font-weight: 600; letter-spacing: 2px;
}
.toc-list { list-style: none; }
.toc-list ol { padding-left: 20px; }
.toc-list li { margin: 6px 0; font-size: 14px; line-height: 1.5; }
.toc-list li a { color: var(--ink-light); }
.toc-list li a:hover { color: var(--accent); }
.toc-num { color: var(--accent-soft); font-weight: 600; margin-right: 4px; }

/* ==== Content ==== */
.content { padding: 0 64px 56px; }

.content h1 {
    font-size: 24px; color: var(--accent); margin: 44px 0 14px;
    padding-bottom: 10px; border-bottom: 1px solid var(--border-light);
    font-weight: 700; letter-spacing: 2px; line-height: 1.3;
}
.content h2 {
    font-size: 20px; color: var(--accent-soft); margin: 36px 0 12px;
    font-weight: 600; letter-spacing: 1px;
}
.content h3 {
    font-size: 17px; color: #4a3020; margin: 28px 0 10px;
    font-weight: 600;
}
.content h4 {
    font-size: 15px; color: #666; margin: 20px 0 8px;
    font-weight: 600;
}
.content p {
    margin: 12px 0; text-align: justify; text-indent: 2em;
    line-height: 1.9;
}
.content p:first-of-type { text-indent: 0; }
.content strong { color: var(--accent); font-weight: 700; }
.content a { color: var(--accent); }

/* ==== Tables ==== */
.table-wrapper {
    overflow-x: auto; margin: 18px 0;
    border: 1px solid var(--border-soft); border-radius: 2px;
}
.content table {
    width: 100%; border-collapse: collapse;
    font-size: 13.5px; margin: 0;
}
.content table thead th, .content table th {
    background: linear-gradient(180deg, #f5e6d3 0%, #eedcc8 100%);
    color: var(--ink-light); font-weight: 700;
    padding: 10px 11px; border-bottom: 2px solid var(--accent-soft);
    text-align: center; white-space: nowrap;
    font-size: 13px; letter-spacing: 0.5px;
}
.content table td {
    padding: 8px 11px; border-bottom: 1px solid var(--border-soft);
    text-align: center; vertical-align: middle;
}
.content table tr:last-child td { border-bottom: none; }
.content table tr:nth-child(even) td { background: var(--bg-warm); }
.content table tr:nth-child(odd) td { background: var(--bg-card); }
.content table td:first-child { text-align: left; font-weight: 500; }

/* ==== Code & ASCII Art ==== */
.content code {
    background: #f5e6d3; padding: 2px 7px; border-radius: 2px;
    font-family: "DejaVu Sans Mono", "Noto Sans Mono", "Courier New", monospace;
    font-size: 13px; color: #8b4513; font-weight: 500;
}
.content pre {
    background: #2d2416; color: #e8d5a0; padding: 18px 22px;
    border-radius: 3px; overflow-x: auto;
    font-family: "DejaVu Sans Mono", "Noto Sans Mono", "Courier New", monospace;
    font-size: 12.5px; line-height: 1.55; margin: 18px 0;
    border: 1px solid #3d3426;
}
.content pre.ascii-art {
    background: #1a1a2e; color: #a0d468;
    border: 1px solid #2a2a3e;
}

/* ==== Blockquote (classical citations) ==== */
.content blockquote {
    margin: 18px 0; padding: 14px 22px;
    background: linear-gradient(90deg, var(--bg-cream) 0%, var(--bg-card) 100%);
    border-left: 3px solid var(--gold);
    color: #5a4a3a; font-style: italic; line-height: 1.8;
    border-radius: 0 3px 3px 0;
}
.content blockquote p { text-indent: 0; }

/* ==== HR (section divider) ==== */
.content hr {
    border: none; border-top: 1px solid var(--border-light);
    margin: 36px 0; width: 40%; margin-left: auto; margin-right: auto;
}

/* ==== List styling ==== */
.content ul, .content ol { margin: 12px 0; padding-left: 24px; }
.content li { margin: 5px 0; line-height: 1.7; }

/* ==== Disclaimer ==== */
.disclaimer {
    margin: 48px 64px 0; padding: 28px 0 48px;
    border-top: 1px solid var(--border-light);
    font-size: 11.5px; color: #aaa; line-height: 1.8;
    text-align: justify;
}
.disclaimer strong { color: #888; }
.disclaimer p { margin: 6px 0; text-indent: 0; }

/* ==== Navbar ==== */
.navbar {
    position: fixed; top: 0; left: 0; right: 0; height: 40px;
    background: rgba(255,253,247,0.94); border-bottom: 1px solid var(--border-light);
    padding: 0 24px; font-size: 13px; z-index: 100;
    display: flex; align-items: center; gap: 20px;
    backdrop-filter: blur(6px);
}
.navbar a { color: var(--accent-soft); cursor: pointer; font-weight: 500; }
.navbar span { color: #999; flex: 1; }

/* ==== Print ==== */
@media print {
    body { background: white; font-size: 11px; }
    .page { max-width: none; box-shadow: none; margin: 0; border-radius: 0; }
    .cover { padding: 20px 36px 16px; }
    .cover::before { margin-bottom: 20px; }
    .cover h1 { font-size: 24px; letter-spacing: 4px; }
    .content { padding: 0 36px 24px; }
    .content h1 { font-size: 18px; margin: 28px 0 10px; page-break-before: always; }
    .content h1:first-of-type, .cover + * h1 { page-break-before: avoid; }
    .content h2 { font-size: 16px; }
    .content h3 { font-size: 14px; }
    .content p { text-indent: 1.5em; font-size: 10.5px; }
    .content table { font-size: 10px; }
    .content table th, .content table td { padding: 5px 8px; }
    .toc { margin: 0 36px 16px; page-break-after: always; padding: 16px 24px; }
    .navbar { display: none; }
    .disclaimer { margin: 30px 36px 0; padding: 16px 0; }
    a { color: inherit; text-decoration: none; }
    .content pre { background: #f8f8f8; color: #333; border: 1px solid #ddd; }
    .content pre.ascii-art { background: #f8f8f8; color: #333; }
    .content table th { background: #f0f0f0; }
    .content table tr:nth-child(even) td { background: #fafafa; }
    @page {
        margin: 16mm 15mm;
        @bottom-center { content: counter(page); font-size: 9px; color: #999; }
    }
}

/* ==== Responsive ==== */
@media (max-width: 640px) {
    .page { margin: 0; }
    .cover { padding: 40px 24px 28px; }
    .cover h1 { font-size: 22px; letter-spacing: 3px; }
    .content { padding: 0 24px 30px; }
    .content p { text-indent: 1.5em; }
    .toc { margin: 0 24px 20px; padding: 16px 20px; }
    .disclaimer { margin: 32px 24px 0; }
    .table-wrapper { font-size: 11px; }
}
'''

CSS_MODERN = CSS_TRADITIONAL  # single theme for now


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="generator" content="bazi-pro report generator">
<title>{title}</title>
<style>{css}</style>
</head>
<body>

<nav class="navbar">
  <span>{report_title}</span>
  <a href="#toc-top">目录</a>
  <a href="#" onclick="window.print(); return false;">打印 / 保存为PDF</a>
</nav>

<div class="page">

<section class="cover">
  <h1>{report_title}</h1>
  <p class="subtitle">专业命理解读报告</p>
  <p class="date">{report_date}</p>
  <table class="meta-table">
    {meta_table}
  </table>
  {decoration}
</section>

<div class="toc" id="toc-top">
  {toc}
</div>

<div class="content">
  {body}
</div>

<div class="disclaimer">
  <p><strong>免责声明</strong></p>
  <p>本报告基于 Bazi MCP 排盘数据和传统命理学理论（参酌《穷通宝鉴》《子平真诠》《三命通会》《滴天髓》《神峰通考》等经典），仅供传统文化学习与参考，不构成任何决策依据。命理学属于传统文化范畴，涉及健康和财务的判断请以专业诊断为准。人生在于自身的努力和选择，命理仅为认知自我的辅助工具。</p>
  <br>
  <p>报告生成时间：{report_date} &nbsp;|&nbsp; bazi-pro v4.1 &nbsp;|&nbsp; 生成工具: scripts/generate_report.py</p>
</div>

</div>

</body>
</html>'''


# ---------------------------------------------------------------------------
# PDF generation (optional, graceful degradation)
# ---------------------------------------------------------------------------

# Emoji → text fallback for PDF (weasyprint may not render color emoji glyphs)
_EMOJI_FALLBACK = {
    '🔮': '★', '⭐': '★', '🌟': '★',
    '⚠️': '⚠', '⚠': '⚠',
    '🔴': '●', '🟢': '●', '🟡': '●',
    '✅': '✓', '✔️': '✓', '✔': '✓',
    '❌': '✗', '✖️': '✗', '✖': '✗',
    '🌊': '≈', '🔥': '!', '💧': '≈',
    '🌱': '·', '📈': '↑', '🚀': '↑↑',
    '📊': '=', '📌': '·', '🔑': '#',
    '🩺': '+', '⏳': '~', '⛔': '⊗',
    '☯': '☯', '🏠': '[家]', '💰': '[财]',
    '❤️': '[心]', '💀': '[危]',
}

def strip_emoji_for_pdf(html: str) -> str:
    """Remove variation selectors and replace emoji with text glyphs for PDF."""
    # First, strip VS16 (U+FE0F) which forces emoji presentation
    html = html.replace('\ufe0f', '')
    # Then apply explicit fallbacks
    for emoji, text in _EMOJI_FALLBACK.items():
        html = html.replace(emoji, text)
    return html

def try_generate_pdf(html_content: str, output_path: str) -> tuple:
    """尝试生成 PDF，返回 (success, message)"""
    pdf_path = output_path.rsplit('.', 1)[0] + '.pdf'

    # Strip emoji for reliable PDF rendering (weasyprint color emoji support is limited)
    pdf_html = strip_emoji_for_pdf(html_content)

    # Attempt 1: weasyprint (best quality)
    try:
        from weasyprint import HTML
        HTML(string=pdf_html).write_pdf(pdf_path)
        return True, f'PDF 已保存至: {pdf_path}'
    except ImportError:
        pass
    except Exception as e:
        print(f'  [weasyprint] 渲染异常: {e}', file=sys.stderr)

    # Attempt 2: pdfkit (wkhtmltopdf)
    try:
        import pdfkit
        pdfkit.from_string(pdf_html, pdf_path)
        return True, f'PDF 已保存至: {pdf_path}'
    except ImportError:
        pass
    except Exception:
        pass

    # Neither available
    return False, (
        'PDF 生成需要安装额外依赖，以下任选其一:\n'
        '  推荐: pip install weasyprint     (高质量 HTML→PDF，Windows 需 GTK+)\n'
        '  备选: pip install pdfkit         (需额外安装 wkhtmltopdf)\n'
        '  零依赖: 在浏览器打开 HTML → 打印 → 另存为 PDF（效果等同）\n'
        f'HTML 报告已保存至: {output_path}'
    )


# ---------------------------------------------------------------------------
# Enhanced Markdown output
# ---------------------------------------------------------------------------

def generate_enhanced_markdown(meta: dict, body_text: str,
                               report_title: str, report_date: str) -> str:
    """生成增强版 Markdown 报告（含元数据头和页脚）"""
    lines = [
        f'# {report_title}',
        f'',
        f'*专业命理解读报告 — {report_date}*',
        f'',
    ]

    if meta:
        lines.append('## 基本信息')
        lines.append('')
        for key, label in [
            ('gender', '性别'), ('solar_date', '阳历'), ('lunar_date', '农历'),
            ('bazi', '八字'), ('day_master', '日主'), ('zodiac', '生肖'),
            ('nayin', '纳音'), ('minggong', '命宫'), ('taiyuan', '胎元'),
        ]:
            if key in meta and meta[key]:
                lines.append(f'- **{label}**：{meta[key]}')
        lines.append('')
        lines.append('---')
        lines.append('')

    lines.append(body_text)
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append(f'*报告生成时间：{report_date} | bazi-pro v4.1 | generate_report.py*')
    lines.append('')
    lines.append(
        '> **免责声明**：本报告基于传统命理学理论，仅供传统文化学习与参考，'
        '不构成任何决策依据。'
    )

    return '\n'.join(lines) + '\n'


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='八字命理分析报告生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
示例:
  python3 generate_report.py --input analysis.md --output report.html
  python3 generate_report.py --input analysis.md --output report.html --pdf
  cat analysis.md | python3 generate_report.py > report.html
  python3 generate_report.py --input analysis.md --format md --output report.md
        '''))
    parser.add_argument('--input', '-i', help='输入分析文件路径（默认: stdin）')
    parser.add_argument('--output', '-o', help='输出文件路径（默认: 自动生成）')
    parser.add_argument('--title', default='八字命理分析报告', help='报告标题')
    parser.add_argument('--meta', help='元数据 JSON 文件路径')
    parser.add_argument('--pdf', action='store_true', help='同时生成 PDF')
    parser.add_argument('--format', choices=['html', 'md', 'both'], default='md',
                        help='输出格式（默认: md）')
    parser.add_argument('--style', choices=['traditional', 'modern'], default='traditional',
                        help='样式主题（默认: traditional）')
    parser.add_argument('--theme', choices=['report', 'dashboard'], default='report',
                        help='呈现主题: report(传统报告) / dashboard(交互仪表盘)')
    parser.add_argument('--gender', help='性别（覆盖自动提取）')
    parser.add_argument('--birth', help='出生日期（覆盖自动提取）')
    parser.add_argument('--name', help='姓名/称呼')

    args = parser.parse_args()

    # --- Read input ---
    if args.input:
        if not os.path.exists(args.input):
            print(f'错误: 输入文件不存在: {args.input}', file=sys.stderr)
            sys.exit(1)
        with open(args.input, 'r', encoding='utf-8') as f:
            analysis_text = f.read()
    elif not sys.stdin.isatty():
        analysis_text = sys.stdin.read()
    else:
        print('错误: 请提供输入文件 (--input) 或通过管道输入', file=sys.stderr)
        sys.exit(1)

    if not analysis_text.strip():
        print('错误: 输入内容为空', file=sys.stderr)
        sys.exit(1)

    # --- Metadata ---
    cli_meta = {}
    if args.gender:
        cli_meta['gender'] = args.gender
    if args.birth:
        cli_meta['solar_date'] = args.birth
    if args.name:
        cli_meta['name'] = args.name

    file_meta = {}
    if args.meta:
        if not os.path.exists(args.meta):
            print(f'错误: 元数据文件不存在: {args.meta}', file=sys.stderr)
            sys.exit(1)
        file_meta = load_meta_json(args.meta)

    extracted_meta = extract_meta_from_text(analysis_text)
    meta = merge_metadata(cli_meta, file_meta, extracted_meta)

    report_date = datetime.now().strftime('%Y年%m月%d日 %H:%M')

    # Set global style flag (bit of a hack, but keeps things simple)
    if args.style == 'modern':
        globals()['_use_modern'] = True

    # --- Determine output path ---
    if args.output:
        output_base = args.output
    else:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = '.html' if args.format == 'html' else '.md'
        output_base = os.path.join(os.getcwd(), f'bazi_report_{ts}{ext}')

    # --- Generate ---
    if args.format in ('html', 'both') or args.theme == 'dashboard':
        if args.theme == 'dashboard':
            html_content = generate_dashboard(meta, analysis_text, args.title, report_date, simple_md_to_html)
        else:
            html_content = generate_html_report(meta, analysis_text, args.title, report_date)
        html_path = output_base if args.format in ('html', 'both') else (
            output_base.rsplit('.', 1)[0] + '.html'
        )
        if args.theme == 'dashboard':
            if not html_path.endswith('_dashboard.html'):
                html_path = html_path.replace('.html', '_dashboard.html') if '.html' in html_path else html_path + '_dashboard.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        label = '仪表盘' if args.theme == 'dashboard' else 'HTML 报告'
        print(f'{label}已保存至: {html_path}')

        if args.pdf:
            success, msg = try_generate_pdf(html_content, html_path)
            print(msg)

    if args.format in ('md', 'both'):
        md_content = generate_enhanced_markdown(meta, analysis_text, args.title, report_date)
        md_path = output_base if args.format == 'md' else (
            output_base.rsplit('.', 1)[0] + '.md'
        )
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f'Markdown 报告已保存至: {md_path}')


if __name__ == '__main__':
    main()
