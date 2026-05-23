#!/usr/bin/env python3
"""
bazi-pro 命盘对比视图 v5.0
双列 HTML 布局，并排展示两个命盘的对比结果
"""

from html import escape
from bazi_pro.compare_engine import CompareResult


def render_compare_view(result: CompareResult) -> str:
    """生成命盘对比视图 HTML

    Args:
        result: CompareEngine.compare() 的返回结果

    Returns:
        对比视图 HTML
    """
    pillar_rows = ''
    for d in result.pillar_diff:
        same_class = 'same' if d['same'] else 'diff'
        pillar_rows += (
            f'<tr class="{same_class}">'
            f'<td class="pos-col">{escape(d["position"])}</td>'
            f'<td>{escape(d["chart_a"])}</td>'
            f'<td>{escape(d["chart_b"])}</td>'
            f'<td>{"相同" if d["same"] else "不同"}</td>'
            f'</tr>'
        )

    relations_html = ''
    for r in result.relation_analysis:
        rel_class = 'rel-good' if r['relation'] == '相生' else ('rel-bad' if r['relation'] == '相克' else 'rel-neutral')
        relations_html += (
            f'<div class="relation-card {rel_class}">'
            f'<strong>{escape(r["type"])}</strong>: {escape(r["description"])}'
            f'</div>'
        )

    score_color = '#5f8d72' if result.compatibility_score >= 70 else ('#b98b54' if result.compatibility_score >= 40 else '#c0392b')

    return f'''<div class="compare-view-container">
<style>
.compare-view-container {{ max-width: 960px; margin: 0 auto; padding: 20px; font-family: "Noto Serif SC", serif; }}
.compare-header {{ text-align: center; margin-bottom: 28px; }}
.compare-header h2 {{ color: var(--neo-gold, #c4a86c); font-size: 24px; letter-spacing: 4px; }}
.compare-columns {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
.compare-card {{ background: var(--neo-surface, #1a1a2e); border: 1px solid var(--neo-border, #333);
  border-radius: var(--neo-radius-md, 12px); padding: 20px; }}
.compare-card h3 {{ color: var(--neo-primary, #c4a86c); margin: 0 0 12px 0; font-size: 16px; }}
.compare-card .bazi {{ font-size: 18px; letter-spacing: 6px; text-align: center; }}
.pillar-table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
.pillar-table th {{ background: var(--neo-surface-2, #222); padding: 8px; font-size: 12px; color: var(--neo-muted, #666); }}
.pillar-table td {{ padding: 8px; text-align: center; border-bottom: 1px solid var(--neo-border, #333); }}
.pillar-table .same {{ background: rgba(95,141,114,0.1); }}
.pillar-table .diff {{ background: rgba(192,57,43,0.08); }}
.pos-col {{ font-weight: 600; color: var(--neo-muted, #666); }}
.compat-section {{ text-align: center; margin: 24px 0; }}
.compat-score {{ display: inline-block; font-size: 48px; font-weight: 800; }}
.relation-card {{ padding: 10px 16px; border-radius: 8px; margin: 6px 0; font-size: 14px; }}
.rel-good {{ background: rgba(95,141,114,0.1); border-left: 3px solid #5f8d72; }}
.rel-bad {{ background: rgba(192,57,43,0.08); border-left: 3px solid #c0392b; }}
.rel-neutral {{ background: rgba(185,139,84,0.08); border-left: 3px solid #b98b54; }}
</style>

<div class="compare-header">
<h2>命盘对比分析</h2>
<p style="color:var(--neo-muted,#666);font-size:14px">双命盘并排对比视图</p>
</div>

<div class="compare-columns">
<div class="compare-card">
<h3>命盘 A</h3>
<div class="bazi">{escape(result.chart_a.get("八字", "--"))}</div>
<p style="text-align:center;color:var(--neo-muted,#666);margin-top:8px">
日主: {escape(result.chart_a.get("日主", "?"))} | 性别: {escape(result.chart_a.get("性别", "?"))}
</p>
</div>
<div class="compare-card">
<h3>命盘 B</h3>
<div class="bazi">{escape(result.chart_b.get("八字", "--"))}</div>
<p style="text-align:center;color:var(--neo-muted,#666);margin-top:8px">
日主: {escape(result.chart_b.get("日主", "?"))} | 性别: {escape(result.chart_b.get("性别", "?"))}
</p>
</div>
</div>

<div class="compare-card">
<h3>四柱对比</h3>
<table class="pillar-table">
<tr><th>柱位</th><th>命盘 A</th><th>命盘 B</th><th>状态</th></tr>
{pillar_rows}
</table>
</div>

<div class="compare-card">
<h3>日主合化关系</h3>
{relations_html}
</div>

<div class="compat-section">
<h3 style="color:var(--neo-muted,#666);font-size:12px;letter-spacing:2px">兼容性评估</h3>
<div class="compat-score" style="color:{score_color}">{result.compatibility_score}</div>
<div style="font-size:12px;color:var(--neo-muted,#666)">/ 100</div>
<p style="color:var(--neo-ink-soft,#aaa);font-size:13px">{escape(result.compatibility_note)}</p>
</div>

</div>'''
