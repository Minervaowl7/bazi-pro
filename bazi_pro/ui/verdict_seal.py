#!/usr/bin/env python3
"""
bazi-pro Verdict Seal v4.5 — 命理裁决朱砂印章（动画升级版）
盖章动画 + 墨迹扩散 + 外圈旋转微动画 + PNG 导出
品牌记忆点：看一眼就知道这是 bazi-pro
"""

import math
from html import escape
from bazi_pro.view_model import DashboardVM, VerdictVM


def render_seal_svg(vm: DashboardVM, size: int = 180, animated: bool = False) -> str:
    """
    生成 Verdict Seal SVG — 中心裁决字 + 外圈五行弧线 + caption

    Args:
        vm: DashboardVM 视图模型
        size: 印章尺寸（像素）
        animated: 是否启用动画（盖章+旋转+墨迹）
    """
    v = vm.verdict
    cx, cy = size / 2, size / 2
    outer_r = size / 2 - 4
    ring_r = outer_r - 14

    main_text = _seal_main_text(v)
    sub_text = _seal_sub_text(v)
    border_dashes = _seal_border_pattern(vm, ring_r, cx, cy)
    caption = _seal_caption_text(v)

    # 动画类名
    anim_class = 'seal-animated' if animated else ''
    rotate_class = 'seal-rotating-border' if animated else ''

    parts = [
        f'<svg class="verdict-seal-svg {anim_class}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">',
        f'<circle cx="{cx}" cy="{cy}" r="{outer_r}" fill="none" stroke="var(--seal-ink, #8a3b2a)" stroke-width="3"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{ring_r}" fill="none" stroke="var(--seal-ink, #8a3b2a)" stroke-width="1.5"/>',
        # 外圈旋转层（动画启用时包裹旋转）
        f'<g class="{rotate_class}" style="transform-origin:{cx}px {cy}px">'
        f'{border_dashes}'
        f'</g>',
        f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" font-size="{_seal_font_size(main_text)}" '
        f'font-weight="900" fill="var(--seal-ink, #8a3b2a)" '
        f'font-family="&quot;Noto Serif SC&quot;, &quot;STSong&quot;, serif" '
        f'letter-spacing="4">{escape(main_text)}</text>',
    ]

    if sub_text:
        parts.append(
            f'<text x="{cx}" y="{cy + 20}" text-anchor="middle" font-size="13" '
            f'font-weight="600" fill="var(--seal-ink, #8a3b2a)" '
            f'font-family="&quot;Noto Serif SC&quot;, &quot;STSong&quot;, serif" '
            f'letter-spacing="2">{escape(sub_text)}</text>'
        )

    parts.append('</svg>')
    svg = '\n'.join(parts)

    # Caption below seal
    if caption:
        svg += f'<div class="seal-caption">{escape(caption)}</div>'

    return svg


def render_seal_with_animation(vm: DashboardVM, size: int = 180) -> str:
    """生成带动画的完整印章组件（含盖章效果+墨迹扩散+PNG导出）

    Args:
        vm: DashboardVM 视图模型
        size: 印章尺寸

    Returns:
        带动画的印章 HTML 片段
    """
    seal_svg = render_seal_svg(vm, size=size, animated=True)

    export_btn = (
        '<button class="seal-export-btn" onclick="exportSealPNG()" '
        'aria-label="导出印章为 PNG 图片" title="导出印章图片">📥 导出 PNG</button>'
    )

    return (
        f'<div class="seal-animated-container">'
        f'<div class="seal-ink-spread"></div>'
        f'<div class="seal-stamp-effect">{seal_svg}</div>'
        f'{export_btn}'
        f'</div>'
    )


def _seal_caption_text(v: VerdictVM) -> str:
    """印章下方 caption"""
    parts = []
    if v.yongshen:
        parts.append('用' + '、'.join(v.yongshen[:2]))
    if v.xishen:
        parts.append('喜' + '、'.join(v.xishen[:2]))
    return ' · '.join(parts) if parts else ''


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
    """底部弧文：短标签，最多 10 字"""
    parts = []
    if v.yongshen:
        parts.append('用' + ''.join(v.yongshen[:2]))
    if v.xishen:
        parts.append('喜' + ''.join(v.xishen[:2]))
    result = ' · '.join(parts)
    return result[:14]  # hard cap


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

/* ── 动画版印章容器 ── */
.seal-animated-container {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 16px 0;
}
.seal-stamp-effect {
    position: relative;
    z-index: 2;
}

/* 盖章动画 */
.seal-animated {
    animation: seal-stamp 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}
@keyframes seal-stamp {
    0% { transform: scale(1.8) rotate(-5deg); opacity: 0; }
    50% { transform: scale(0.92) rotate(2deg); opacity: 0.9; }
    70% { transform: scale(1.03) rotate(-1deg); opacity: 1; }
    100% { transform: scale(1) rotate(0deg); opacity: 1; }
}

/* 墨迹扩散 */
.seal-ink-spread {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 160px;
    height: 160px;
    border-radius: 50%;
    transform: translate(-50%, -50%) scale(0);
    background: radial-gradient(circle, var(--seal-ink, #8a3b2a) 0%, transparent 70%);
    opacity: 0;
    z-index: 1;
    pointer-events: none;
}
.seal-animated-container .seal-ink-spread {
    animation: ink-spread 1.2s ease-out both;
}
@keyframes ink-spread {
    0% { transform: translate(-50%, -50%) scale(0.3); opacity: 0.25; }
    40% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.12; }
    100% { transform: translate(-50%, -50%) scale(1.4); opacity: 0; }
}

/* 外圈五行弧线旋转 */
.seal-rotating-border {
    animation: slow-rotate 40s linear infinite;
}
@keyframes slow-rotate {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 导出按钮 */
.seal-export-btn {
    margin-top: 10px;
    padding: 4px 12px;
    border: 1px solid var(--neo-border, #444);
    border-radius: var(--neo-radius-sm, 6px);
    background: var(--neo-surface, #1a1a2e);
    color: var(--neo-ink-soft, #ccc);
    cursor: pointer;
    font-size: 11px;
    transition: all 0.2s ease;
}
.seal-export-btn:hover {
    background: var(--neo-surface-2, #2a2a3e);
    border-color: var(--seal-ink, #c46a4a);
    color: var(--seal-ink, #c46a4a);
}

.seal-caption {
    text-align: center;
    font-size: 13px;
    color: var(--seal-ink, #8a3b2a);
    font-weight: 600;
    letter-spacing: 2px;
    margin-top: 8px;
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

# ── 印章导出 JS ──
SEAL_JS = '''
(function() {
    window.exportSealPNG = function() {
        var svg = document.querySelector('.verdict-seal-svg');
        if (!svg) return;
        var clone = svg.cloneNode(true);
        clone.querySelectorAll('animate,animateMotion').forEach(function(el) { el.remove(); });
        clone.classList.remove('seal-animated');
        var data = new XMLSerializer().serializeToString(clone);
        var blob = new Blob(['<?xml version="1.0" encoding="UTF-8"?>' + data],
                           {type: 'image/svg+xml;charset=utf-8'});
        var url = URL.createObjectURL(blob);
        var img = new Image();
        img.onload = function() {
            var canvas = document.createElement('canvas');
            var scale = 3;
            canvas.width = 180 * scale;
            canvas.height = 180 * scale;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            canvas.toBlob(function(pngBlob) {
                var pngUrl = URL.createObjectURL(pngBlob);
                var a = document.createElement('a');
                a.href = pngUrl;
                a.download = 'bazi-verdict-seal.png';
                a.click();
                URL.revokeObjectURL(pngUrl);
            }, 'image/png');
        };
        img.src = url;
    };
})();
'''
