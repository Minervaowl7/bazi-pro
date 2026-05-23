#!/usr/bin/env python3
"""
bazi-pro Report Composer v5.0
将原始分析 Markdown 解析为结构化咨询报告
Reader-first: 结论先行，技术步骤进 Appendix
"""

import re
from dataclasses import dataclass, field
from html import escape
from typing import Optional


# ═══════════════════════════════════════════════════════════════════
# Document Model
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ReportSection:
    """报告的一个章节"""
    heading: str = ''         # 章节标题（清洗后）
    level: int = 1            # 1=h1, 2=h2
    content: str = ''         # HTML 内容
    raw_md: str = ''          # 原始 Markdown
    is_technical: bool = False  # 是否技术过程（→ Appendix）
    is_table: bool = False    # 是否以表格为主


@dataclass
class ReportDocument:
    """结构化报告文档"""
    # Reader-first sections (front matter)
    executive_summary: str = ''
    key_verdict: str = ''

    # Main body sections (reader-facing)
    sections: list[ReportSection] = field(default_factory=list)

    # Appendix (technical)
    appendix_sections: list[ReportSection] = field(default_factory=list)

    # Classical evidence
    classical_evidence: list[dict] = field(default_factory=list)

    # Raw data (for reference)
    raw_sections: list[ReportSection] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
# Section Classifier — rule-based, no LLM needed
# ═══════════════════════════════════════════════════════════════════

# Patterns that mark a section as technical (→ Appendix)
TECHNICAL_PATTERNS = [
    r'第[〇零0]步',           # 第〇步
    r'0\.[0-2]',              # 0.0, 0.1, 0.2
    r'双通道',                # 双通道检索
    r'BM\d+',                 # BM25
    r'最高得分',              # 检索得分
    r'粗略预检',              # 快速预检
    r'层\s*0[-−]?[AB]',      # 层 0-A, 层0-A, 层0A
    r'层\s*[1-6]',           # 层1-6
    r'六层筛查',              # 格局六层筛查
    r'0\.2\.\d',              # 0.2.1 双通道结果对比
    r'执行检索',              # 执行检索
    r'结果注入',              # 结果注入
    r'计分说明',              # 量化计分说明
    r'权重说明',              # 权重说明
    r'评分基准锚',            # 评分基准锚
    r'输出格式',              # 输出格式规范
]

# Patterns for reader-facing sections (keep in body)
READER_PATTERNS = [
    r'第[一二三四五六七八九十]步',  # 第一步~第九步
    r'数据校验',              # 数据校验摘要
    r'基本信息',              # 基本信息表
    r'日主旺衰',              # 旺衰判断
    r'格局判定',              # 格局判定
    r'喜用判定',              # 喜用神
    r'五行力量',              # 五行力量
    r'大运流年',              # 大运流年
    r'刑冲合害',              # 刑冲合害
    r'分维度解读',            # 分维度
    r'性格底色',              # 性格
    r'事业方向',              # 事业
    r'财运模式',              # 财运
    r'感情婚姻',              # 感情
    r'健康提示',              # 健康
    r'近年运势',              # 近期运势
    r'历史.*?校准',           # 历史校准
    r'总结',                  # 总结
    r'古籍条文',              # 古籍条文（reader版）
    r'古籍证据',              # 古籍证据
    r'免责声明',              # 免责声明
]


def classify_section(heading: str, content: str = '') -> bool:
    """判断一个章节是否为技术过程（应进 Appendix）"""
    h = heading.strip()
    c = content[:500] if content else ''

    # Check technical patterns
    for pat in TECHNICAL_PATTERNS:
        if re.search(pat, h) or re.search(pat, c):
            return True

    return False


def is_table_heavy(content: str) -> bool:
    """判断内容是否以表格为主（用于后续 card 转换）"""
    lines = content.split('\n')
    table_lines = sum(1 for l in lines if l.strip().startswith('|'))
    return table_lines >= 3 and table_lines > len(lines) * 0.3


# ═══════════════════════════════════════════════════════════════════
# Parser: Markdown → ReportDocument
# ═══════════════════════════════════════════════════════════════════

def parse_markdown_to_document(md_text: str) -> ReportDocument:
    """将分析 Markdown 解析为 ReportDocument"""
    doc = ReportDocument()

    # Split into sections by h1/h2 headings
    raw_sections = _split_by_headings(md_text)

    for sec in raw_sections:
        h = sec.heading
        c = sec.raw_md

        # Extract executive summary
        if _is_executive_summary(h, c):
            doc.executive_summary = _extract_summary_text(c)
            continue

        # Classify
        if classify_section(h, c):
            sec.is_technical = True
            doc.appendix_sections.append(sec)
        else:
            sec.is_technical = False
            sec.is_table = is_table_heavy(c)
            doc.sections.append(sec)

    return doc


def _split_by_headings(text: str) -> list[ReportSection]:
    """按 h1/h2 标题切分 Markdown"""
    sections = []
    pattern = re.compile(r'^(#{1,2})\s+(.+?)$', re.MULTILINE)

    matches = list(pattern.finditer(text))
    if not matches:
        return [ReportSection(heading='正文', raw_md=text)]

    for i, m in enumerate(matches):
        level = len(m.group(1))
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        sections.append(ReportSection(
            heading=heading,
            level=level,
            raw_md=content,
        ))

    return sections


def _is_executive_summary(heading: str, content: str) -> bool:
    return bool(re.search(r'(总结|Executive\s*Summary)', heading))


def _extract_summary_text(content: str) -> str:
    """从总结/摘要段落提取纯文本"""
    # Remove markdown formatting
    text = re.sub(r'\*{1,3}', '', content)
    text = re.sub(r'#{1,4}\s+', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Take first 300 chars
    return text.strip()[:300]


# ═══════════════════════════════════════════════════════════════════
# Renderer: ReportDocument → HTML body
# ═══════════════════════════════════════════════════════════════════

def render_document_body(doc: ReportDocument,
                         md_to_html=None) -> str:
    """
    渲染报告正文：reader sections → appendix
    md_to_html: Markdown→HTML 转换函数
    """
    if md_to_html is None:
        md_to_html = _simple_md_to_html

    parts = []

    # Reader sections
    parts.append('<div class="content-main">')

    for sec in doc.sections:
        htag = f'h{min(sec.level + 1, 3)}'  # bump level for report nesting
        anchor = re.sub(r'[^\w\u4e00-\u9fff]', '-', sec.heading).strip('-').lower()
        html = md_to_html(sec.raw_md)

        # If table-heavy, add collapse wrapper
        if sec.is_table:
            html = _wrap_table_section(html)

        parts.append(f'<section id="{anchor}">')
        parts.append(f'<{htag}>{escape(sec.heading)}</{htag}>')
        parts.append(html)
        parts.append('</section>')

    parts.append('</div>')

    # Appendix
    if doc.appendix_sections:
        parts.append('<div class="appendix">')
        parts.append('<h2>附录：技术推理过程</h2>')

        for sec in doc.appendix_sections:
            anchor = re.sub(r'[^\w\u4e00-\u9fff]', '-', sec.heading).strip('-').lower()
            html = md_to_html(sec.raw_md)
            if is_table_heavy(sec.raw_md):
                html = _wrap_table_section(html, collapsed=True)

            parts.append(f'<section id="appendix-{anchor}">')
            parts.append(f'<h3>{escape(sec.heading)}</h3>')
            parts.append(html)
            parts.append('</section>')

        parts.append('</div>')

    return '\n'.join(parts)


def _wrap_table_section(html: str, collapsed: bool = False) -> str:
    """给表格区块加 wrapper 和折叠按钮"""
    cls = 'table-section collapsed' if collapsed else 'table-section'
    btn = ('<button class="table-expand-btn" onclick="this.parentElement.classList.toggle(\'collapsed\')">'
           '展开完整表格</button>') if collapsed else ''
    return f'<div class="{cls}">{btn}{html}</div>'


def _simple_md_to_html(text: str) -> str:
    """极简 Markdown→HTML fallback"""
    lines = text.split('\n')
    out = []
    in_table = False
    in_code = False

    for line in lines:
        s = line.strip()

        # Code fence
        if s.startswith('```'):
            out.append('</code></pre>' if in_code else '<pre><code>')
            in_code = not in_code
            continue

        if in_code:
            out.append(escape(line))
            continue

        # Table
        if '|' in s and s.startswith('|'):
            if not in_table:
                out.append('<div class="table-wrapper"><table>')
                in_table = True
            cells = [c.strip() for c in s.strip('|').split('|')]
            tag = 'th' if re.match(r'^[\s\-:]+$', cells[0]) else 'td'
            if tag == 'th':  # skip separator rows
                continue
            out.append('<tr>' + ''.join(f'<td>{_inline_md(escape(c))}</td>' for c in cells) + '</tr>')
            continue
        elif in_table:
            out.append('</table></div>')
            in_table = False

        # Heading
        m = re.match(r'^(#{1,4})\s+(.+)$', line)
        if m:
            lv = len(m.group(1))
            out.append(f'<h{lv}>{escape(m.group(2).strip())}</h{lv}>')
            continue

        # Blockquote
        if s.startswith('>'):
            out.append(f'<blockquote><p>{escape(s[1:].strip())}</p></blockquote>')
            continue

        # HR
        if s in ('---', '***'):
            out.append('<hr>')
            continue

        # List
        if re.match(r'^[\-\*]\s+', s):
            out.append(f'<li>{_inline_md(escape(s[2:].strip()))}</li>')
            continue

        # Paragraph
        if s:
            out.append(f'<p>{_inline_md(escape(s))}</p>')

    if in_table:
        out.append('</table></div>')
    if in_code:
        out.append('</code></pre>')

    return '\n'.join(out)


def _inline_md(text: str) -> str:
    """行内 markdown → HTML"""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text
