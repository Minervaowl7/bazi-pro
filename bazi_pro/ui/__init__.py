#!/usr/bin/env python3
"""
bazi-pro UI Renderer v4.3
从 ViewModel 渲染 Dashboard / Report / Replay 三种输出形态
过渡期：模板内联，最终迁移到 Jinja2
"""

from html import escape
from bazi_pro.view_model import DashboardVM


def render_dashboard(vm: DashboardVM) -> str:
    """渲染 Dashboard HTML — 命理案卷裁决首页"""
    hero = _render_hero(vm)
    pillars = _render_pillars(vm)
    evidence = _render_evidence(vm)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>命理案卷 · {escape(vm.verdict.day_master)}</title></head>
<body>
{hero}
{pillars}
{evidence}
</body>
</html>'''


def render_report(vm: DashboardVM) -> str:
    """渲染 Report HTML — 咨询报告"""
    return f'<html><body><h1>Report: {escape(vm.verdict.day_master)}</h1></body></html>'


def render_replay(vm: DashboardVM) -> str:
    """渲染 Replay HTML — 裁决回放"""
    stages_html = ''
    for s in vm.trace_stages:
        stages_html += f'<li>{escape(s.title)} — {escape(s.summary)}</li>'
    return f'<html><body><h1>Verdict Replay</h1><ul>{stages_html}</ul></body></html>'


# ── Components ──

def _render_hero(vm: DashboardVM) -> str:
    v = vm.verdict
    return f'''<div class="hero">
    <div class="bazi">{escape(vm.bazi)}</div>
    <div class="day-master">{escape(v.day_master)}</div>
    <div class="verdict-seal">
        <span class="seal-main">{escape(v.decision or '正格')}</span>
    </div>
    <div class="pattern">{escape(v.pattern)}</div>
    <div class="verdict-row">
        <span>用神：{"、".join(v.yongshen) if v.yongshen else "—"}</span>
        <span>喜神：{"、".join(v.xishen) if v.xishen else "—"}</span>
        <span>忌神：{"、".join(v.jishen) if v.jishen else "—"}</span>
    </div>
    <div class="confidence">置信度 {v.confidence:.0%}</div>
</div>'''


def _render_pillars(vm: DashboardVM) -> str:
    cards = ''
    for p in vm.pillars:
        cards += f'<div class="pillar"><span>{p.gan}</span><span>{p.zhi}</span></div>'
    return f'<div class="pillars">{cards}</div>'


def _render_evidence(vm: DashboardVM) -> str:
    cards = ''
    for e in vm.evidence[:3]:
        cards += f'<details><summary>{escape(e.title)}</summary><p>{escape(e.claim)}</p></details>'
    return f'<div class="evidence">{cards}</div>'
