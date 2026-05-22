#!/usr/bin/env python3
"""
bazi-pro Verdict Seal v4.3 — 命理裁决朱砂印章
品牌记忆点：看一眼就知道这是 bazi-pro
"""

import math
from html import escape
from bazi_pro.view_model import DashboardVM, VerdictVM


def render_seal_svg(vm: DashboardVM, size: int = 180) -> str:
    """
    生成 Verdict Seal SVG
    圆形朱砂印章：中心主裁决 + 外圈辅文 + 边框纹样
    """
    v = vm.verdict
    cx, cy = size / 2, size / 2
    outer_r = size / 2 - 4
    ring_r = outer_r - 14
    inner_r = ring_r - 16

    main_text = _seal_main_text(v)
    sub_text = _seal_sub_text(v)
    bottom_text = _seal_bottom_text(v)

    # Pillar-derived border pattern
    border_dashes = _seal_border_pattern(vm, ring_r, cx, cy)

    parts = [
        f'<svg class="verdict-seal-svg" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">',
        # Outer ring
        f'<circle cx="{cx}" cy="{cy}" r="{outer_r}" fill="none" stroke="var(--seal-ink, #8a3b2a)" stroke-width="3"/>',
        # Inner ring
        f'<circle cx="{cx}" cy="{cy}" r="{ring_r}" fill="none" stroke="var(--seal-ink, #8a3b2a)" stroke-width="1.5"/>',
        # Border pattern (pillar-derived dashes)
        border_dashes,
        # Main text (center, large)
        f'<text x="{cx}" y="{cy - 6}" text-anchor="middle" font-size="{_seal_font_size(main_text)}" '
        f'font-weight="900" fill="var(--seal-ink, #8a3b2a)" '
        f'font-family="&quot;Noto Serif SC&quot;, &quot;STSong&quot;, serif" '
        f'letter-spacing="4">{escape(main_text)}</text>',
    ]

    # Sub text below main
    if sub_text:
        parts.append(
            f'<text x="{cx}" y="{cy + 18}" text-anchor="middle" font-size="13" '
            f'font-weight="600" fill="var(--seal-ink, #8a3b2a)" '
            f'font-family="&quot;Noto Serif SC&quot;, &quot;STSong&quot;, serif" '
            f'letter-spacing="2">{escape(sub_text)}</text>'
        )

    # Bottom arc text
    if bottom_text:
        bottom_chars = list(bottom_text)
        if len(bottom_chars) > 14:
            bottom_text = bottom_text[:14]
        radius = outer_r - 10
        start_angle = math.pi * 1.55 if len(bottom_text) > 6 else math.pi * 1.6
        angle_step = (2 * math.pi - start_angle * 2 + math.pi) / max(len(bottom_text) - 1, 1) * 0.55

        for i, ch in enumerate(bottom_text):
            angle = start_angle + i * angle_step
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            parts.append(
                f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-size="11" '
                f'font-weight="500" fill="var(--seal-ink, #8a3b2a)" '
                f'font-family="&quot;Noto Serif SC&quot;, &quot;STSong&quot;, serif">'
                f'{escape(ch)}</text>'
            )

    parts.append('</svg>')
    return '\n'.join(parts)


def _seal_main_text(v: VerdictVM) -> str:
    """主裁决文字 — 印章中心大字"""
    decision = v.decision or ''
    if '从格' in decision or '从强' in decision:
        return '从格'
    elif '不从' in decision or '正格' in decision:
        return '正格'
    elif '化气' in (v.pattern or ''):
        return '化气'
    # Fallback: use first 2 chars from pattern
    if v.pattern:
        return v.pattern[:2]
    return '八字'


def _seal_sub_text(v: VerdictVM) -> str:
    """副裁决文字"""
    decision = v.decision or ''
    if '不从' in decision:
        return '不从'
    if '假从' in decision:
        return '假从'
    return ''


def _seal_bottom_text(v: VerdictVM) -> str:
    """底部弧文：用神 · 喜神"""
    parts = []
    if v.yongshen:
        parts.append(f'用{"·".join(v.yongshen[:2])}')
    if v.xishen:
        parts.append(f'喜{"·".join(v.xishen[:2])}')
    return ' · '.join(parts) if parts else ''


def _seal_font_size(text: str) -> int:
    """根据文字长度动态调整字号"""
    n = len(text)
    if n <= 2: return 48
    if n <= 3: return 36
    if n <= 4: return 28
    return 22


def _seal_border_pattern(vm: DashboardVM, radius: float, cx: float, cy: float) -> str:
    """
    从四柱天干生成环形边框纹样
    每柱的天干五行 → 对应颜色的弧线段
    """
    pillars = vm.pillars
    if len(pillars) < 4:
        return ''

    colors = {
        '木': '#5f8d72', '火': '#b85c4a',
        '土': '#b98b54', '金': '#b7aa8b', '水': '#4f7896',
    }

    parts = []
    segment_angle = 2 * math.pi / 4  # 4 segments for 4 pillars

    for i, p in enumerate(pillars):
        wx = p.wuxing_gan or ''
        color = colors.get(wx, '#8a3b2a')
        start_a = -math.pi / 2 + i * segment_angle + 0.25
        end_a = start_a + segment_angle - 0.5
        x1 = cx + radius * math.cos(start_a)
        y1 = cy + radius * math.sin(start_a)
        x2 = cx + radius * math.cos(end_a)
        y2 = cy + radius * math.sin(end_a)
        large = 1 if end_a - start_a > math.pi else 0
        parts.append(
            f'<path d="M {x1:.1f} {y1:.1f} A {radius:.0f} {radius:.0f} 0 {large} 1 {x2:.1f} {y2:.1f}" '
            f'fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" opacity="0.6"/>'
        )

    return '\n'.join(parts)


# ── CSS for the seal ──

SEAL_CSS = '''
/* ── Verdict Seal ── */
.verdict-seal-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 16px 0;
}
.verdict-seal-svg {
    width: 140px;
    height: 140px;
    filter: drop-shadow(0 4px 12px rgba(60, 30, 10, 0.12));
    transition: transform 0.3s ease;
}
.verdict-seal-svg:hover {
    transform: scale(1.05);
}
@media (prefers-color-scheme: dark) {
    :root { --seal-ink: #c46a4a; }
    .verdict-seal-svg {
        filter: drop-shadow(0 4px 16px rgba(0, 0, 0, 0.3));
    }
}
@media (prefers-color-scheme: light) {
    :root { --seal-ink: #8a3b2a; }
}

/* ── Screenshot mode ── */
body.share-mode .theme-btn,
body.share-mode .dashboard-nav,
body.share-mode .analysis-toggle,
body.share-mode .analysis-content,
body.share-mode .footer { display: none !important; }
body.share-mode .container { max-width: 1080px; padding: 40px 60px; }
body.share-mode .hero { padding: 30px 0 16px; }
'''
