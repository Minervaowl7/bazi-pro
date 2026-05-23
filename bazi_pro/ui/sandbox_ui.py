#!/usr/bin/env python3
"""
bazi-pro 流年沙盒 UI v5.0
年份滑块 + 动态五行可视化 + 关键年份书签
"""

from html import escape
from bazi_pro.liunian_sandbox import LiunianSandbox


def render_sandbox_ui(sandbox: LiunianSandbox) -> str:
    """生成流年沙盒交互界面

    Args:
        sandbox: LiunianSandbox 实例

    Returns:
        沙盒 UI HTML
    """
    start, end = sandbox.year_range
    default_year = (start + end) // 2
    yd = sandbox.get_year_data(default_year)

    # 关键年份标签列表
    key_years = sandbox.mark_key_years()
    bookmark_html = ''
    for yd_k in key_years:
        if yd_k.bookmark:
            icon = '⭐' if '用神' in yd_k.bookmark else '⚠️'
            bookmark_html += (
                f'<span class="bookmark-tag" data-year="{yd_k.year}" '
                f'onclick="jumpToYear({yd_k.year})" title="{escape(yd_k.bookmark)}">'
                f'{icon} {yd_k.year}</span>'
            )

    return f'''<div class="sandbox-container">
<style>
.sandbox-container {{ max-width: 720px; margin: 0 auto; padding: 16px; font-family: "Noto Serif SC", serif; }}
.sandbox-header {{ text-align: center; margin-bottom: 20px; }}
.sandbox-header h3 {{ color: var(--neo-gold, #c4a86c); letter-spacing: 3px; }}
.year-display {{ text-align: center; margin: 16px 0; }}
.year-num {{ font-size: 42px; font-weight: 800; color: var(--neo-primary, #c4a86c); }}
.year-ganzhi {{ font-size: 28px; letter-spacing: 6px; margin: 8px 0; }}
.year-slider {{ width: 100%; margin: 16px 0; -webkit-appearance: none;
  height: 6px; background: var(--neo-border, #333); border-radius: 3px; outline: none; }}
.year-slider::-webkit-slider-thumb {{ -webkit-appearance: none; width: 20px; height: 20px;
  background: var(--neo-primary, #c4a86c); border-radius: 50%; cursor: pointer; }}
.slider-labels {{ display: flex; justify-content: space-between; font-size: 11px; color: var(--neo-muted, #666); }}
.year-details {{ background: var(--neo-surface, #1a1a2e); border: 1px solid var(--neo-border, #333);
  border-radius: var(--neo-radius-md, 12px); padding: 16px; margin: 12px 0; }}
.detail-row {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--neo-border, #333); }}
.detail-row:last-child {{ border-bottom: none; }}
.detail-label {{ color: var(--neo-muted, #666); font-size: 12px; }}
.detail-value {{ color: var(--neo-ink, #ddd); font-size: 13px; font-weight: 500; }}
.bookmarks {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; justify-content: center; }}
.bookmark-tag {{ display: inline-block; padding: 4px 10px; border-radius: 12px;
  font-size: 12px; cursor: pointer; transition: all .2s;
  background: var(--neo-surface-2, #222); border: 1px solid var(--neo-border, #444); }}
.bookmark-tag:hover {{ background: var(--neo-primary, #c4a86c); color: #111; }}
</style>

<div class="sandbox-header">
<h3>流年推演沙盒</h3>
<p style="font-size:12px;color:var(--neo-muted,#666)">拖动滑块查看各年份运势</p>
</div>

<div class="year-display">
<div class="year-num" id="yearNum">{default_year}</div>
<div class="year-ganzhi" id="yearGanzhi">{yd.gan_zhi}</div>
<div style="font-size:11px;color:var(--neo-muted,#666)">
天干: {yd.gan} | 地支: {yd.zhi}
</div>
</div>

<input type="range" class="year-slider" id="yearSlider"
  min="{start}" max="{end}" value="{default_year}"
  oninput="updateYear(this.value)">

<div class="slider-labels">
<span>{start}</span><span>{end}</span>
</div>

<div class="year-details" id="yearDetails">
<div class="detail-row"><span class="detail-label">流年干支</span><span class="detail-value">{yd.gan_zhi}</span></div>
<div class="detail-row"><span class="detail-label">与原局关系</span><span class="detail-value">{len(yd.relations)} 条互动</span></div>
<div class="detail-row"><span class="detail-label">特殊标记</span><span class="detail-value">{yd.bookmark or '—'}</span></div>
</div>

<div class="bookmarks">
<span style="font-size:11px;color:var(--neo-muted,#666)">关键年份: </span>
{bookmark_html}
</div>

<script>
var sandboxData = {{}};
function updateYear(year) {{
    document.getElementById('yearNum').textContent = year;
    // 简化的动态更新（实际需后端计算）
    var yearNum = parseInt(year);
    var ganIdx = (yearNum - 4) % 10;
    var zhiIdx = (yearNum - 4) % 12;
    var gan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'][ganIdx];
    var zhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'][zhiIdx];
    document.getElementById('yearGanzhi').textContent = gan + zhi;
    document.getElementById('yearDetails').querySelectorAll('.detail-value')[0].textContent = gan + zhi;
}}
function jumpToYear(year) {{
    document.getElementById('yearSlider').value = year;
    updateYear(year);
}}
</script>
</div>'''
