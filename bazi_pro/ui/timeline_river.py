#!/usr/bin/env python3
"""
bazi-pro 命运河流时间轴 v4.5 — SVG 曲线大运时间轴 + 波峰波谷吉凶表达
纯 CSS/SVG 实现，支持键盘导航和色温渐变
"""

import json
from bazi_pro.view_model import DashboardVM, DayunVM

# 当前年份（用于光标定位）
CURRENT_YEAR = 2026

# 大运吉凶映射颜色
LUCK_COLORS = {
    '大吉': '#5f8d72',
    '吉': '#7fbfa0',
    '平': '#b98b54',
    '凶': '#c0392b',
    '大凶': '#8b1a1a',
}

LUCK_WARMTH = {
    '大吉': 'warm-strong',
    '吉': 'warm',
    '平': 'neutral',
    '凶': 'cool',
    '大凶': 'cool-strong',
}


def _luck_to_y(luck: str, base_y: float) -> float:
    """将吉凶映射为 Y 轴波峰/波谷"""
    offset_map = {
        '大吉': -55, '吉': -30, '平': 0,
        '凶': 30, '大凶': 55,
    }
    return base_y + offset_map.get(luck, 0)


def _generate_river_path(dayun_list: list, base_y: float, x_step: float) -> str:
    """生成命运河流的 SVG 贝塞尔曲线路径"""
    if not dayun_list:
        return ''

    points = []
    for i, dy in enumerate(dayun_list):
        x = 100 + i * x_step
        y = _luck_to_y(dy.assessment, base_y)
        points.append((x, y))

    if len(points) == 1:
        x, y = points[0]
        return f'M{x - 20},{base_y} Q{x},{y} {x + 20},{base_y}'

    # 使用 Catmull-Rom 风格的三次贝塞尔
    path_parts = [f'M{points[0][0]},{points[0][1]}']
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        cx1 = x1 + (x2 - x1) * 0.4
        cx2 = x1 + (x2 - x1) * 0.6
        path_parts.append(f'C{cx1},{y1} {cx2},{y2} {x2},{y2}')

    # 底部闭合（填充区域）
    last_x = points[-1][0]
    first_x = points[0][0]
    path_parts.append(f'L{last_x},{base_y + 80}')
    path_parts.append(f'L{first_x},{base_y + 80}Z')

    return ' '.join(path_parts)


def _generate_flow_line(dayun_list: list, base_y: float, x_step: float) -> str:
    """生成不填充的流动曲线（用于描边）"""
    if not dayun_list:
        return ''

    points = []
    for i, dy in enumerate(dayun_list):
        x = 100 + i * x_step
        y = _luck_to_y(dy.assessment, base_y)
        points.append((x, y))

    path_parts = [f'M{points[0][0]},{points[0][1]}']
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        cx1 = x1 + (x2 - x1) * 0.4
        cx2 = x1 + (x2 - x1) * 0.6
        path_parts.append(f'C{cx1},{y1} {cx2},{y2} {x2},{y2}')

    return ' '.join(path_parts)


def render_timeline_river(vm: 'DashboardVM') -> str:
    """生成命运河流时间轴 HTML

    使用 SVG 曲线表达大运吉凶起伏，支持交互浏览

    Args:
        vm: DashboardVM 视图模型

    Returns:
        完整的命运河流时间轴 HTML
    """
    dayun = vm.dayun
    qiyun_age = vm.qiyun_age or '?'

    if not dayun:
        return '<p class="empty-timeline-placeholder">⚠️ 大运数据未加载，无法渲染时间轴</p>'

    # 计算参数
    base_y = 220
    x_step = 130
    total_width = 100 + len(dayun) * x_step + 80
    viewbox_w = max(total_width, 800)
    viewbox_h = 480

    # 生成路径
    fill_path = _generate_river_path(dayun, base_y, x_step)
    line_path = _generate_flow_line(dayun, base_y, x_step)

    svg_parts = [
        f'<svg class="timeline-river-svg" viewBox="0 0 {viewbox_w} {viewbox_h}" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="大运命运河流时间轴">',
        '<title>大运命运河流时间轴</title>',
        '<desc>以河流曲线形式展示各步大运的吉凶起伏趋势</desc>',
    ]

    # 定义渐变
    svg_parts.append('<defs>')
    # 河流填充渐变
    svg_parts.append(
        '<linearGradient id="riverGrad" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0%" stop-color="var(--neo-water, #4f7896)" stop-opacity="0.12"/>'
        '<stop offset="50%" stop-color="var(--neo-water, #4f7896)" stop-opacity="0.25"/>'
        '<stop offset="100%" stop-color="var(--neo-water, #4f7896)" stop-opacity="0.12"/>'
        '</linearGradient>'
    )
    # 河流描边渐变
    svg_parts.append(
        '<linearGradient id="riverStroke" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0%" stop-color="var(--neo-water, #4f7896)" stop-opacity="0.5"/>'
        '<stop offset="50%" stop-color="var(--neo-water, #7aa8c4)" stop-opacity="0.9"/>'
        '<stop offset="100%" stop-color="var(--neo-water, #4f7896)" stop-opacity="0.5"/>'
        '</linearGradient>'
    )
    # 暖色渐变（吉运高亮）
    svg_parts.append(
        '<radialGradient id="warmGlow">'
        '<stop offset="0%" stop-color="#c4a86c" stop-opacity="0.3"/>'
        '<stop offset="100%" stop-color="#c4a86c" stop-opacity="0"/>'
        '</radialGradient>'
    )
    # 冷色渐变（凶运高亮）
    svg_parts.append(
        '<radialGradient id="coolGlow">'
        '<stop offset="0%" stop-color="#4f7896" stop-opacity="0.3"/>'
        '<stop offset="100%" stop-color="#4f7896" stop-opacity="0"/>'
        '</radialGradient>'
    )
    svg_parts.append('</defs>')

    # 基准线（虚线）
    svg_parts.append(
        f'<line x1="80" y1="{base_y}" x2="{viewbox_w - 40}" y2="{base_y}" '
        'stroke="var(--neo-border, #444)" stroke-width="1" '
        'stroke-dasharray="6,6" opacity="0.3"/>'
    )

    # 河流填充区域
    if fill_path:
        svg_parts.append(
            f'<path d="{fill_path}" fill="url(#riverGrad)" class="river-fill">'
            '<animate attributeName="opacity" values="0.7;1;0.7" dur="8s" repeatCount="indefinite"/>'
            '</path>'
        )

    # 河流曲线
    if line_path:
        svg_parts.append(
            f'<path d="{line_path}" fill="none" stroke="url(#riverStroke)" '
            'stroke-width="3" stroke-linecap="round" class="river-line"/>'
        )

    # 大运节点
    for i, dy in enumerate(dayun):
        x = 100 + i * x_step
        y = _luck_to_y(dy.assessment, base_y)
        color = LUCK_COLORS.get(dy.assessment, '#b98b54')
        warmth = LUCK_WARMTH.get(dy.assessment, 'neutral')
        is_current = _is_current_dayun(i, len(dayun), int(qiyun_age) if qiyun_age.isdigit() else 0)

        # 光晕（吉运暖色 / 凶运冷色）
        glow_url = 'warmGlow' if warmth.startswith('warm') else 'coolGlow'
        svg_parts.append(
            f'<circle cx="{x}" cy="{y}" r="28" fill="url(#{glow_url})" '
            f'class="node-glow node-glow-{warmth}" data-luck="{warmth}"/>'
        )

        # 节点圆
        svg_parts.append(
            f'<circle cx="{x}" cy="{y}" r="14" fill="var(--neo-surface, #1a1a2e)" '
            f'stroke="{color}" stroke-width="2.5" class="dayun-node" '
            f'data-index="{i}" data-luck="{dy.assessment}" tabindex="0" '
            f'role="button" aria-label="第{i+1}步大运 {dy.gan_zhi} {dy.assessment}">'
            f'<title>第{i+1}步大运: {dy.gan_zhi} ({dy.assessment})</title>'
            f'</circle>'
        )

        # 当前运标记
        if is_current:
            svg_parts.append(
                f'<circle cx="{x}" cy="{y}" r="18" fill="none" stroke="{color}" '
                'stroke-width="1.5" stroke-dasharray="3,3" class="current-marker">'
                '<animate attributeName="stroke-opacity" values="1;0.3;1" '
                'dur="1.5s" repeatCount="indefinite"/>'
                '</circle>'
            )
            svg_parts.append(
                f'<text x="{x}" y="{y - 38}" text-anchor="middle" '
                f'fill="{color}" font-size="10" font-weight="700" class="current-label">'
                '● 当前</text>'
            )

        # 标注文字：干支
        svg_parts.append(
            f'<text x="{x}" y="{y + 32}" text-anchor="middle" '
            f'fill="var(--neo-ink-soft, #ccc)" font-size="13" font-weight="600" '
            f'class="dayun-ganzhi">{dy.gan_zhi}</text>'
        )

        # 标注文字：年龄段
        svg_parts.append(
            f'<text x="{x}" y="{y + 48}" text-anchor="middle" '
            f'fill="var(--neo-muted, #666)" font-size="10" class="dayun-age">'
            f'{dy.age_range}岁</text>'
        )

        # 标注文字：评估
        luck_color = LUCK_COLORS.get(dy.assessment, '#999')
        svg_parts.append(
            f'<text x="{x}" y="{y - 42}" text-anchor="middle" '
            f'fill="{luck_color}" font-size="11" font-weight="700" class="dayun-assessment">'
            f'{dy.assessment}</text>'
        )

    # 起运年龄标注
    svg_parts.append(
        f'<text x="60" y="{base_y + 50}" text-anchor="start" '
        f'fill="var(--neo-muted, #666)" font-size="10">起运: {qiyun_age}岁</text>'
    )

    svg_parts.append('</svg>')

    svg_html = '\n'.join(svg_parts)

    # 图例和操作按钮
    legend_ctrl = (
        '<div class="timeline-legend">'
        '<span class="legend-dot" style="background:#5f8d72"></span>大吉 '
        '<span class="legend-dot" style="background:#7fbfa0"></span>吉 '
        '<span class="legend-dot" style="background:#b98b54"></span>平 '
        '<span class="legend-dot" style="background:#c0392b"></span>凶 '
        '<span class="legend-dot" style="background:#8b1a1a"></span>大凶 '
        '<span style="margin-left:10px;font-size:10px;color:var(--neo-muted)">'
        '← → 键导航节点 | 点击查看详情</span>'
        '</div>'
    )

    export_btn = (
        '<div class="timeline-controls">'
        '<button class="tl-btn" onclick="exportTimelineSVG()" '
        'aria-label="导出时间轴为 SVG">📥 导出 SVG</button>'
        '</div>'
    )

    css = _timeline_css()
    js = _timeline_js(len(dayun))

    return (
        f'<div class="timeline-river-container">'
        f'<style>{css}</style>'
        f'<div class="timeline-scroll-wrapper">{svg_html}</div>'
        f'{legend_ctrl}'
        f'{export_btn}'
        f'<script>{js}</script>'
        f'</div>'
    )


def _is_current_dayun(index: int, total: int, qiyun_age: int) -> bool:
    """判断是否为当前所处大运（粗略估计）"""
    current_age = CURRENT_YEAR - 2002  # 基于 sample 数据中的出生年
    # 简化：假设每步大运10年，估算当前年龄对应的大运
    estimated_age = qiyun_age + index * 10
    return estimated_age <= current_age < estimated_age + 10


def _timeline_css() -> str:
    """时间轴的 CSS 样式"""
    return r"""
.timeline-river-container {
    position: relative;
    width: 100%;
    padding: 12px 0;
}
.timeline-scroll-wrapper {
    overflow-x: auto;
    overflow-y: hidden;
    scroll-behavior: smooth;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 8px;
}
.timeline-scroll-wrapper::-webkit-scrollbar {
    height: 4px;
}
.timeline-scroll-wrapper::-webkit-scrollbar-track {
    background: var(--neo-surface, #1a1a2e);
}
.timeline-scroll-wrapper::-webkit-scrollbar-thumb {
    background: var(--neo-border, #444);
    border-radius: 2px;
}
.timeline-river-svg {
    min-width: 800px;
    height: auto;
}
.dayun-node {
    cursor: pointer;
    transition: r 0.3s ease, stroke-width 0.3s ease;
}
.dayun-node:hover, .dayun-node:focus {
    r: 18;
    stroke-width: 3.5;
    filter: drop-shadow(0 0 6px currentColor);
    outline: none;
}
.dayun-node.active-node {
    r: 20;
    stroke-width: 4;
    filter: drop-shadow(0 0 10px currentColor);
}
.node-glow {
    transition: r 0.5s ease, opacity 0.5s ease;
}
.node-glow-warm-strong { opacity: 0.8; }
.node-glow-warm { opacity: 0.5; }
.node-glow-neutral { opacity: 0.15; }
.node-glow-cool { opacity: 0.4; }
.node-glow-cool-strong { opacity: 0.7; }
.dayun-node:hover ~ .node-glow,
.dayun-node:focus ~ .node-glow {
    r: 40;
    opacity: 0.9;
}
.river-line {
    transition: stroke-width 0.5s ease;
}
.timeline-legend {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 8px 16px;
    font-size: 11px;
    color: var(--neo-muted, #666);
    justify-content: center;
    flex-wrap: wrap;
}
.legend-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 2px;
}
.timeline-controls {
    display: flex;
    gap: 8px;
    justify-content: center;
    margin-top: 8px;
}
.tl-btn {
    padding: 5px 12px;
    border: 1px solid var(--neo-border, #444);
    border-radius: var(--neo-radius-sm, 8px);
    background: var(--neo-surface, #1a1a2e);
    color: var(--neo-ink-soft, #ccc);
    cursor: pointer;
    font-size: 12px;
    transition: all 0.2s ease;
}
.tl-btn:hover {
    background: var(--neo-surface-2, #2a2a3e);
    border-color: var(--neo-primary, #c4a86c);
    color: var(--neo-primary, #c4a86c);
}
.current-marker {
    pointer-events: none;
}
.current-label {
    pointer-events: none;
}
.empty-timeline-placeholder {
    text-align: center;
    color: var(--neo-muted, #666);
    padding: 30px;
    font-size: 14px;
}
"""


def _timeline_js(node_count: int) -> str:
    """时间轴交互 JS：键盘导航 + 导出"""
    return f"""
(function() {{
    var nodes = document.querySelectorAll('.dayun-node');
    var activeIndex = -1;
    var totalNodes = {node_count};

    function setActive(idx) {{
        nodes.forEach(function(n) {{ n.classList.remove('active-node'); }});
        if (idx >= 0 && idx < totalNodes) {{
            nodes[idx].classList.add('active-node');
            nodes[idx].focus();
            // 滚动到可见区域
            nodes[idx].scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
        }}
        activeIndex = idx;
    }}

    // 点击激活
    nodes.forEach(function(node, i) {{
        node.addEventListener('click', function() {{
            if (activeIndex === i) {{
                setActive(-1);
            }} else {{
                setActive(i);
            }}
        }});
    }});

    // 键盘导航
    document.addEventListener('keydown', function(e) {{
        if (e.target.closest('.timeline-river-container') === null) return;
        if (e.key === 'ArrowRight') {{
            e.preventDefault();
            setActive(Math.min(activeIndex + 1, totalNodes - 1));
        }} else if (e.key === 'ArrowLeft') {{
            e.preventDefault();
            setActive(Math.max(activeIndex - 1, 0));
        }} else if (e.key === 'Escape') {{
            setActive(-1);
        }}
    }});

    // 初始激活中间节点
    setActive(Math.floor(totalNodes / 2));

    // SVG 导出
    window.exportTimelineSVG = function() {{
        var svg = document.querySelector('.timeline-river-svg');
        if (!svg) return;
        var clone = svg.cloneNode(true);
        clone.querySelectorAll('animate').forEach(function(el) {{ el.remove(); }});
        var data = new XMLSerializer().serializeToString(clone);
        var blob = new Blob(['<?xml version="1.0" encoding="UTF-8"?>' + data],
                           {{type: 'image/svg+xml;charset=utf-8'}});
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'bazi-timeline-river.svg';
        a.click();
        URL.revokeObjectURL(url);
    }};
}})();
"""
