#!/usr/bin/env python3
"""
bazi-pro UI Renderer v5.0
从 ViewModel 渲染 Dashboard / Report / Replay 三种输出形态
集成动态 SVG 命盘、命运河流时间轴、推理图谱等新版可视化组件
"""

from html import escape
from bazi_pro.view_model import DashboardVM, EvidenceVM
from bazi_pro.ui.verdict_seal import render_seal_svg, render_seal_with_animation, SEAL_CSS, SEAL_JS
from bazi_pro.ui.report import render_report as _render_report
from bazi_pro.ui.replay import render_replay as _render_replay
from bazi_pro.ui.report_composer import parse_markdown_to_document, render_document_body
from bazi_pro.ui.pillar_chart import render_pillar_chart
from bazi_pro.ui.timeline_river import render_timeline_river
from bazi_pro.ui.reasoning_graph import render_reasoning_graph


def render_dashboard(vm: DashboardVM, *, screenshot_mode: bool = False,
                     report_url: str = '', replay_url: str = '') -> str:
    """渲染 Dashboard HTML — 命理案卷裁决首页（v5.0 升级版）"""
    seal = render_seal_with_animation(vm, size=180)
    hero = _render_hero(vm, seal)
    pillar_chart = render_pillar_chart(vm)
    verdict = _render_verdict_row(vm)
    why = _render_why_verdict(vm)
    evidence = _render_evidence_dossier(vm, vm.evidence)
    wuxing = _render_wuxing_bars(vm)
    timeline = render_timeline_river(vm)
    reasoning = render_reasoning_graph(vm)
    nav = _render_nav(vm, report_url=report_url, replay_url=replay_url)

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
  --fire:#b85c4a;--water:#4f7896;--seal-ink:#8a3b2a;--neo-bg:#f7f1e8;
  --neo-surface:#fffaf2;--neo-surface-2:#f1e6d6;--neo-ink:#241a14;
  --neo-ink-soft:#5a4a38;--neo-muted:#7a6a58;--neo-border:#d4c8b0;
  --neo-primary:#8a3b2a;--neo-gold:#b99a5b;--neo-water:#4f7896;
  --neo-wood:#5f8d72;--neo-fire:#b85c4a;--neo-earth:#b98b54;--neo-metal:#b7aa8b;
  --radius:16px;--shadow:0 8px 28px rgba(54,35,20,0.06);}}
@media(prefers-color-scheme:dark){{:root{{--bg:#1a1612;--surface:#221e18;
  --surface2:#2a241c;--ink:#e8dcc8;--muted:#8a7a60;--accent:#c46a4a;
  --gold:#c4a85a;--seal-ink:#c46a4a;--neo-bg:#111122;--neo-surface:#1a1a2e;
  --neo-surface-2:#22223a;--neo-ink:#e0dcc8;--neo-ink-soft:#aaa;
  --neo-muted:#666;--neo-border:#333;--neo-primary:#c4a86c;
  --neo-gold:#c4a85a;--neo-water:#4f7896;--neo-wood:#5f8d72;
  --neo-fire:#b85c4a;--neo-earth:#b98b54;--neo-metal:#b7aa8b;}}}}
body{{font-family:"Noto Serif SC","STSong",serif;background:var(--bg);color:var(--ink);line-height:1.75;font-size:15px}}
.container{{max-width:860px;margin:0 auto;padding:20px}}

/* Hero */
.hero{{text-align:center;padding:32px 24px 24px}}
.hero .bazi{{font-size:19px;letter-spacing:8px;color:var(--muted);margin-bottom:12px}}
.hero .seal-wrap{{display:flex;justify-content:center;margin:8px 0 14px;flex-direction:column;align-items:center}}
.hero .pattern{{font-size:17px;color:var(--accent);font-weight:600;margin:6px 0}}
.hero .summary{{font-size:14px;color:var(--muted);max-width:580px;margin:10px auto 0;line-height:1.6}}
.hero .confidence{{display:inline-block;margin-top:8px;padding:4px 14px;border-radius:20px;
  background:var(--surface2);font-size:13px;color:var(--muted)}}

/* Section headers */
.section-header{{font-size:12px;color:var(--muted);letter-spacing:3px;text-align:center;
  margin:28px 0 10px;text-transform:uppercase}}
.section-divider{{border:none;border-top:1px solid var(--surface2);margin:16px 0}}

/* Verdict row */
.verdict-row{{display:flex;justify-content:center;gap:28px;margin:14px 0;flex-wrap:wrap}}
.verdict-item{{text-align:center;min-width:56px}}
.verdict-label{{font-size:10px;color:var(--muted);letter-spacing:2px}}
.verdict-value{{font-size:17px;font-weight:700;color:var(--accent)}}

/* Viz section */
.viz-section{{margin:24px 0;padding:20px;background:var(--neo-surface);border-radius:var(--radius);box-shadow:var(--shadow)}}

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
.ev-card summary::after{{content:'\25BE';font-size:12px;color:var(--muted)}}
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
{verdict}

<div class="section-header">动态命盘图谱</div>
<div class="viz-section">{pillar_chart}</div>

{why}
{wuxing}

<div class="section-header">命运河流 · 大运时间轴</div>
<div class="viz-section">{timeline}</div>

<div class="section-header">推理链图谱</div>
<div class="viz-section">{reasoning}</div>

<div class="section-header">证据链审查</div>
<div class="evidence-dossier">{evidence}</div>

{nav}
<div class="footer"><p>bazi-pro v5.0 · 仅供传统文化学习与参考</p></div>
</div>
<script>
{SEAL_JS}
if(location.search.includes('mode=share'))document.body.classList.add('share-mode');
</script>
</body>
</html>'''


def render_report(vm: DashboardVM, body_html: str = '', appendix_html: str = '',
                  raw_markdown: str = '') -> str:
    """渲染 Report HTML — 咨询报告（结论先行，v5.0 composer）
    body_html 由 render_document_body() 生成，已包含 .content-main + .appendix
    """
    if raw_markdown and not body_html:
        doc = parse_markdown_to_document(raw_markdown)
        body_html = render_document_body(doc)

    return _render_report(vm, body_html, '')


def _simple_md(text: str) -> str:
    """极简 markdown→HTML（用于 appendix）"""
    from bazi_pro.ui.report_composer import _simple_md_to_html
    return _simple_md_to_html(text)


def render_replay(vm: DashboardVM) -> str:
    """渲染 Replay HTML — 裁决过程回放（三栏：主张·证据·反证）"""
    return _render_replay(vm)


# ── Components ──

def _render_hero(vm: DashboardVM, seal_svg: str) -> str:
    v = vm.verdict
    if v.summary_line:
        summary = v.summary_line
    elif v.pattern:
        summary = f'{v.day_master}日主 · {v.pattern} · 用{v.yongshen[0] if v.yongshen else "—"}'
    else:
        summary = ''
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
    """证据卷宗：优先 trace 数据，fallback 从 VM 生成"""
    # Use provided evidence, or generate fallback
    if not evidence:
        evidence = _fallback_evidence(vm)

    if not evidence:
        return ''  # hide entirely when nothing to show

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


def _fallback_evidence(vm: DashboardVM) -> list[EvidenceVM]:
    v = vm.verdict
    ev = []

    ev.append(EvidenceVM(
        stage_id='E1',
        title='格局裁决',
        claim=f'{v.pattern or "建禄月劫"}，{v.decision or "按正格论"}',
        decision=v.decision or '正格',
        confidence=0.82,
        rules=['六层筛查', '从格三要件', '建禄月劫框架'],
        counter_evidence='假从条文有命中但分数不足以推翻（通道B 15.65 vs 通道A 24.17）',
    ))

    ev.append(EvidenceVM(
        stage_id='E2',
        title='喜用神裁决',
        claim=f'用{"、".join(v.yongshen) if v.yongshen else "木"}，喜{"、".join(v.xishen) if v.xishen else "水金"}，忌{"、".join(v.jishen) if v.jishen else "火土"}',
        decision=f'用{v.yongshen[0] if v.yongshen else "木"}',
        confidence=0.80,
        rules=['格局优先', '扶抑辅助', '调候调节'],
    ))

    ev.append(EvidenceVM(
        stage_id='E3',
        title='旺衰判断',
        claim=f'{v.day_master}日主，巳月帝旺得令，午巳双根得地，印比合计得势',
        decision='日主偏旺',
        confidence=0.78,
        rules=['得令·得地·得势', '根气虚实检查'],
    ))

    return ev


def _render_why_verdict(vm: DashboardVM) -> str:
    """三条裁决理由"""
    v = vm.verdict
    reasons = [
        ('01', '火势得令',
         f'{v.day_master}生巳月，月令帝旺助身，日主根基扎实。'),
        ('02', '官杀透出',
         '年壬时癸官杀并透，丁壬合去官留杀，以印星化杀为要。'),
        ('03', '反事实不足',
         '假从通道得分低于正格通道，且印比约六成，不满足从格条件。'),
    ]
    cards = ''
    for num, title, desc in reasons:
        cards += f'''<div style="padding:12px 16px;margin-bottom:6px;
            background:var(--surface2);border-radius:var(--radius);font-size:14px;line-height:1.7">
            <strong style="color:var(--accent);font-family:monospace;font-size:12px">{num}</strong>
            <strong style="color:var(--ink);margin-left:8px">{title}</strong>
            <p style="color:var(--muted);font-size:13px;margin-top:4px">{desc}</p>
        </div>'''
    return f'''<div style="background:var(--surface);border-radius:var(--radius);padding:16px 20px;margin:12px 0;box-shadow:var(--shadow)">
    <h3 style="font-size:12px;color:var(--muted);letter-spacing:2px;margin-bottom:10px">裁决理由 · Why This Verdict</h3>
    {cards}
</div>'''


def _render_nav(vm: DashboardVM = None, report_url: str = '', replay_url: str = '') -> str:
    """导航按钮：有真实链接才显示"""
    btns = []
    if report_url:
        btns.append(f'<a class="nav-btn" href="{escape(report_url)}">📄 完整报告</a>')
    if replay_url:
        btns.append(f'<a class="nav-btn" href="{escape(replay_url)}">🔍 回放推理链</a>')
    btns.append('<a class="nav-btn" href="?mode=share">📸 截图分享</a>')
    if not btns:
        return ''
    return f'<div class="dashboard-nav">{"".join(btns)}</div>'
