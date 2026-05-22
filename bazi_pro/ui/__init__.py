#!/usr/bin/env python3
"""
bazi-pro UI Renderer v4.3
从 ViewModel 渲染 Dashboard / Report / Replay 三种输出形态
"""

from html import escape
from bazi_pro.view_model import DashboardVM
from bazi_pro.ui.verdict_seal import render_seal_svg, SEAL_CSS
from bazi_pro.ui.report import render_report as _render_report
from bazi_pro.ui.replay import render_replay as _render_replay


def render_dashboard(vm: DashboardVM, *, screenshot_mode: bool = False) -> str:
    """渲染 Dashboard HTML — 命理案卷裁决首页"""
    seal = render_seal_svg(vm, size=180)
    hero = _render_hero(vm, seal)
    pillars = _render_pillars(vm)
    verdict = _render_verdict_row(vm)
    evidence = _render_evidence_dossier(vm, vm.evidence[:3])
    wuxing = _render_wuxing_bars(vm)
    nav = _render_nav()

    share_attr = ' class="share-mode"' if screenshot_mode else ''

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>命理案卷 · {escape(vm.verdict.day_master)}</title>
<style>
{SEAL_CSS}
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#f7f1e8;--surface:#fffaf2;--surface2:#f1e6d6;--ink:#241a14;
  --muted:#7a6a58;--accent:#8a3b2a;--gold:#b99a5b;--wood:#5f8d72;
  --fire:#b85c4a;--water:#4f7896;--seal-ink:#8a3b2a;
  --radius:16px;--shadow:0 8px 28px rgba(54,35,20,0.06);}}
@media(prefers-color-scheme:dark){{:root{{--bg:#1a1612;--surface:#221e18;
  --surface2:#2a241c;--ink:#e8dcc8;--muted:#8a7a60;--accent:#c46a4a;
  --gold:#c4a85a;--seal-ink:#c46a4a;}}}}
body{{font-family:"Noto Serif SC","STSong",serif;background:var(--bg);color:var(--ink);line-height:1.75;font-size:15px}}
.container{{max-width:860px;margin:0 auto;padding:20px}}

/* Hero */
.hero{{text-align:center;padding:32px 24px 24px}}
.hero .bazi{{font-size:19px;letter-spacing:8px;color:var(--muted);margin-bottom:12px}}
.hero .seal-wrap{{display:flex;justify-content:center;margin:8px 0 14px}}
.hero .pattern{{font-size:17px;color:var(--accent);font-weight:600;margin:6px 0}}
.hero .summary{{font-size:14px;color:var(--muted);max-width:580px;margin:10px auto 0;line-height:1.6}}
.hero .confidence{{display:inline-block;margin-top:8px;padding:4px 14px;border-radius:20px;
  background:var(--surface2);font-size:13px;color:var(--muted)}}

/* Verdict row */
.verdict-row{{display:flex;justify-content:center;gap:28px;margin:14px 0;flex-wrap:wrap}}
.verdict-item{{text-align:center;min-width:56px}}
.verdict-label{{font-size:10px;color:var(--muted);letter-spacing:2px}}
.verdict-value{{font-size:17px;font-weight:700;color:var(--accent)}}

/* Pillars */
.pillars{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}}
.pillar{{background:var(--surface);border-radius:var(--radius);padding:14px 10px;
  text-align:center;box-shadow:var(--shadow)}}
.pillar .gan{{font-size:36px;font-weight:800}}
.pillar .zhi{{font-size:18px;color:var(--muted);margin-top:2px}}
.pillar .label{{font-size:11px;color:var(--muted);letter-spacing:2px;margin-bottom:4px}}

/* Wuxing bars */
.wuxing-bars{{display:flex;flex-direction:column;gap:6px;margin:8px 0}}
.wx-row{{display:flex;align-items:center;gap:8px}}
.wx-label{{width:24px;text-align:right;font-weight:700;font-size:14px;flex-shrink:0}}
.wx-role{{width:36px;font-size:11px;color:var(--muted);flex-shrink:0}}
.wx-track{{flex:1;height:10px;background:var(--surface2);border-radius:5px;overflow:hidden}}
.wx-fill{{height:100%;border-radius:5px}}
.wx-pct{{width:40px;font-size:12px;color:var(--muted);text-align:right;flex-shrink:0}}

/* Evidence dossier */
.evidence-dossier{{margin:16px 0}}
.ev-card{{background:var(--surface);border-radius:var(--radius);padding:16px 20px;
  margin-bottom:8px;box-shadow:var(--shadow)}}
.ev-card summary{{cursor:pointer;font-weight:600;font-size:15px;color:var(--accent);
  list-style:none;display:flex;justify-content:space-between}}
.ev-card summary::-webkit-details-marker{{display:none}}
.ev-card summary::after{{content:'▾';font-size:12px;color:var(--muted)}}
.ev-card .ev-body{{padding-top:10px;font-size:14px;line-height:1.8;color:var(--ink)}}
.ev-row{{display:flex;justify-content:space-between;padding:4px 0;font-size:13px;
  border-bottom:1px solid var(--surface2)}}
.ev-row:last-child{{border-bottom:none}}
.ev-label{{color:var(--muted);flex-shrink:0}}
.ev-value{{text-align:right;font-weight:500}}

/* Nav */
.dashboard-nav{{display:flex;justify-content:center;gap:14px;margin:20px 0;flex-wrap:wrap}}
.nav-btn{{display:inline-block;padding:10px 22px;border:1px solid var(--surface2);
  border-radius:22px;color:var(--accent);font-size:13px;font-weight:500;
  text-decoration:none;background:var(--surface);transition:all .2s}}
.nav-btn:hover{{background:var(--surface2)}}

.footer{{text-align:center;padding:20px;color:var(--muted);font-size:12px;
  border-top:1px solid var(--surface2);margin-top:16px}}
</style>
</head>
<body{share_attr}>
<div class="container">

{hero}
<div class="pillars">{pillars}</div>

{verdict}
{wuxing}

<div class="evidence-dossier"><h3 style="font-size:12px;color:var(--muted);letter-spacing:2px;margin-bottom:10px">证据链审查</h3>{evidence}</div>

{nav}
<div class="footer"><p>bazi-pro v4.3 · 仅供传统文化学习与参考</p></div>
</div>
<script>
if(location.search.includes('mode=share'))document.body.classList.add('share-mode');
</script>
</body>
</html>'''


def render_report(vm: DashboardVM, body_html: str = '', appendix_html: str = '') -> str:
    """渲染 Report HTML — 咨询报告（结论先行）"""
    return _render_report(vm, body_html, appendix_html)


def render_replay(vm: DashboardVM) -> str:
    """渲染 Replay HTML — 裁决过程回放（三栏：主张·证据·反证）"""
    return _render_replay(vm)


# ── Components ──

def _render_hero(vm: DashboardVM, seal_svg: str) -> str:
    v = vm.verdict
    summary = (f'{v.day_master}生巳月，火势得令，官杀透出，宜以印化杀、以水调候。'
               if v.day_master else '')
    return f'''<div class="hero">
    <div class="bazi">{escape(vm.bazi)}</div>
    <div class="seal-wrap">{seal_svg}</div>
    <div class="pattern">{escape(v.pattern)}</div>
    <div class="summary">{escape(summary)}</div>
    <div class="confidence">综合置信度 {v.confidence:.0%}</div>
</div>'''


def _render_pillars(vm: DashboardVM) -> str:
    cards = ''
    colors = {'木': '#5f8d72', '火': '#b85c4a', '土': '#b98b54', '金': '#b7aa8b', '水': '#4f7896'}
    for p in vm.pillars:
        wx = p.wuxing_gan
        color = colors.get(wx, 'var(--accent)')
        cards += (f'<div class="pillar">'
                  f'<div class="label">{escape(p.position)}柱</div>'
                  f'<div class="gan" style="color:{color}">{escape(p.gan)}</div>'
                  f'<div class="zhi">{escape(p.zhi)}</div></div>')
    return cards


def _render_verdict_row(vm: DashboardVM) -> str:
    v = vm.verdict
    items = [
        ('用神', ' · '.join(v.yongshen[:2]) if v.yongshen else '—'),
        ('喜神', ' · '.join(v.xishen[:2]) if v.xishen else '—'),
        ('忌神', ' · '.join(v.jishen[:2]) if v.jishen else '—'),
    ]
    row = ''
    for label, val in items:
        row += f'<div class="verdict-item"><div class="verdict-label">{label}</div><div class="verdict-value">{escape(val)}</div></div>'
    return f'<div class="verdict-row">{row}</div>'


def _render_wuxing_bars(vm: DashboardVM) -> str:
    wx = vm.wuxing
    order = [
        ('木', wx.wood, '#5f8d72', '印'),
        ('火', wx.fire, '#b85c4a', '比劫'),
        ('水', wx.water, '#4f7896', '官杀'),
        ('土', wx.earth, '#b98b54', '食伤'),
        ('金', wx.metal, '#b7aa8b', '财'),
    ]
    bars = ''
    for name, pct, color, role in order:
        if pct > 0:
            bars += (f'<div class="wx-row">'
                     f'<span class="wx-label" style="color:{color}">{name}</span>'
                     f'<span class="wx-role">{role}</span>'
                     f'<div class="wx-track"><div class="wx-fill" style="width:{pct}%;background:{color}"></div></div>'
                     f'<span class="wx-pct">{pct:.0f}%</span></div>')
    return f'''<div style="background:var(--surface);border-radius:var(--radius);padding:16px 20px;margin:12px 0;box-shadow:var(--shadow)">
    <h3 style="font-size:12px;color:var(--muted);letter-spacing:2px;margin-bottom:10px">五行账簿 · Element Balance Ledger</h3>
    <div class="wuxing-bars">{bars}</div>
</div>'''


def _render_evidence_dossier(vm: DashboardVM, evidence) -> str:
    if not evidence:
        return '<p style="color:var(--muted);font-size:13px;text-align:center">证据数据未加载</p>'
    cards = ''
    for e in evidence:
        conf_pct = f'{e.confidence:.0%}' if e.confidence else '—'
        rules_str = ' · '.join(e.rules[:3]) if e.rules else ''
        counter = f'<div style="margin-top:8px;padding:8px 12px;background:rgba(200,74,58,0.08);border-left:3px solid #c44a3a;border-radius:0 8px 8px 0;font-size:12px">⚠️ 反证: {escape(e.counter_evidence)}</div>' if e.counter_evidence else ''
        cards += f'''<details class="ev-card">
            <summary>{escape(e.title or e.claim[:28])} <span style="font-weight:400;font-size:12px;color:var(--muted)">{conf_pct}</span></summary>
            <div class="ev-body">
                <div class="ev-row"><span class="ev-label">主张</span><span class="ev-value">{escape(e.claim)}</span></div>
                <div class="ev-row"><span class="ev-label">置信度</span><span class="ev-value">{conf_pct}</span></div>
                {f'<div class="ev-row"><span class="ev-label">规则</span><span class="ev-value">{escape(rules_str)}</span></div>' if rules_str else ''}
                {counter}
                {f'<div class="ev-row"><span class="ev-label">裁决</span><span class="ev-value" style="color:var(--accent);font-weight:700">{escape(e.decision)}</span></div>' if e.decision else ''}
            </div>
        </details>'''
    return cards


def _render_nav() -> str:
    return '''<div class="dashboard-nav">
    <a class="nav-btn" href="#">📄 完整报告</a>
    <a class="nav-btn" href="?mode=share">📸 截图分享</a>
    <a class="nav-btn" href="#">🔍 回放推理链</a>
</div>'''
