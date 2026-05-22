#!/usr/bin/env python3
"""
bazi-pro 动态 SVG 命盘 v4.5 — 书法字体四柱节点 + 刑冲合害关系弧线 + 五行粒子动画
纯 CSS/SVG 实现，零外部依赖
"""

from bazi_pro.view_model import DashboardVM, PillarVM, RelationVM

# 天干地支五行映射
GAN_WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
}
ZHI_WUXING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水',
}
WUXING_COLORS = {
    '木': '#5f8d72', '火': '#b85c4a', '土': '#b98b54',
    '金': '#c4a86c', '水': '#4f7896',
}
WUXING_COLORS_LIGHT = {
    '木': '#3d7a5c', '火': '#c0392b', '土': '#a0723a',
    '金': '#9b7d4a', '水': '#2c5f8a',
}
WUXING_PARTICLES = {
    '木': '#7fbfa0', '火': '#e8846a', '土': '#d4a76a',
    '金': '#e0c48a', '水': '#7aa8c4',
}

# 四柱布局位置（SVG viewBox 坐标）
PILLAR_POSITIONS = {
    '年': (200, 90),
    '月': (440, 90),
    '日': (320, 280),
    '时': (440, 470),
}

# 关系类型颜色
RELATION_COLORS = {
    '合': '#c4a86c',
    '冲': '#c0392b',
    '刑': '#8e44ad',
    '害': '#7f8c8d',
    '半合': '#d4a76a',
    '暗合': '#e0c48a',
    '破': '#e67e22',
}


def _wuxing_color(wx: str, theme: str = 'dark') -> str:
    """获取五行对应颜色"""
    if theme == 'light':
        return WUXING_COLORS_LIGHT.get(wx, '#333')
    return WUXING_COLORS.get(wx, '#ccc')


def _render_particle_animation(wx_from: str, wx_to: str, idx: int) -> str:
    """渲染五行粒子流动动画"""
    from_pos = {
        '木': (320, 480), '火': (320, 60), '土': (560, 280),
        '金': (80, 280), '水': (320, 60),
    }
    to_pos = {
        '木': (440, 470), '火': (200, 90), '土': (200, 90),
        '金': (440, 90), '水': (440, 90),
    }
    fx, fy = from_pos.get(wx_from, (320, 280))
    tx, ty = to_pos.get(wx_to, (320, 280))
    mid_x = (fx + tx) / 2 + (idx - 2) * 30
    mid_y = (fy + ty) / 2 - 40 + idx * 15
    color = WUXING_PARTICLES.get(wx_from, '#aaa')
    dur = 3 + idx * 0.7

    path_d = f"M{fx},{fy} Q{mid_x},{mid_y} {tx},{ty}"
    return (
        f'<circle r="3" fill="{color}" opacity="0">'
        f'<animateMotion dur="{dur}s" repeatCount="indefinite" begin="{idx * 0.5}s" path="{path_d}"/>'
        f'<animate attributeName="opacity" values="0;0.8;0.8;0" dur="{dur}s" repeatCount="indefinite" begin="{idx * 0.5}s"/>'
        f'</circle>'
    )


def _render_pillar_node(p: PillarVM, px: float, py: float, is_daymaster: bool) -> str:
    """渲染单个四柱节点"""
    gan_wx = GAN_WUXING.get(p.gan, '')
    zhi_wx = ZHI_WUXING.get(p.zhi, '')
    color = WUXING_COLORS.get(gan_wx if gan_wx else zhi_wx, '#ccc')
    radius = 38 if is_daymaster else 32
    font_size = 22 if is_daymaster else 18
    zhi_size = 14 if is_daymaster else 12
    label_y_offset = -50 if is_daymaster else -42
    stroke_width = 3.5 if is_daymaster else 2.5

    parts = []

    # 脉冲光圈（日主专用）
    if is_daymaster:
        parts.append(
            f'<circle cx="{px}" cy="{py}" r="{radius + 8}" fill="none" '
            f'stroke="{color}" stroke-width="2" opacity="0.3" class="pulse-ring">'
            f'<animate attributeName="r" values="{radius + 4};{radius + 14};{radius + 4}" '
            f'dur="2s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.4;0.05;0.4" '
            f'dur="2s" repeatCount="indefinite"/>'
            f'</circle>'
        )
        # 第二层脉冲
        parts.append(
            f'<circle cx="{px}" cy="{py}" r="{radius + 4}" fill="none" '
            f'stroke="{color}" stroke-width="1" opacity="0.2" class="pulse-ring-2">'
            f'<animate attributeName="r" values="{radius + 2};{radius + 18};{radius + 2}" '
            f'dur="2.5s" repeatCount="indefinite" begin="0.3s"/>'
            f'<animate attributeName="opacity" values="0.3;0.02;0.3" '
            f'dur="2.5s" repeatCount="indefinite" begin="0.3s"/>'
            f'</circle>'
        )

    # 节点背景圆
    parts.append(
        f'<circle cx="{px}" cy="{py}" r="{radius}" fill="var(--neo-surface, #1a1a2e)" '
        f'stroke="{color}" stroke-width="{stroke_width}" class="pillar-node" '
        f'data-position="{p.position}"/>'
    )

    # 天干文字（书法字体）
    parts.append(
        f'<text x="{px}" y="{py + 4}" text-anchor="middle" fill="{color}" '
        f'font-family="\'Zhi Mang Xing\', \'Ma Shan Zheng\', STKaiti, KaiTi, serif" '
        f'font-weight="800" font-size="{font_size}px" class="gan-text">{p.gan}</text>'
    )

    # 地支文字
    parts.append(
        f'<text x="{px}" y="{py + zhi_size + 14}" text-anchor="middle" '
        f'fill="var(--neo-ink-soft, #999)" font-size="{zhi_size}px" '
        f'class="zhi-text">{p.zhi}</text>'
    )

    # 位置标签
    parts.append(
        f'<text x="{px}" y="{py + label_y_offset}" text-anchor="middle" '
        f'fill="var(--neo-muted, #666)" font-size="11px" class="position-label">'
        f'{p.position}柱</text>'
    )

    return '\n'.join(parts)


def _render_relation_arc(r: RelationVM, pillar_map: dict, idx: int, total: int) -> str:
    """渲染刑冲合害关系弧线"""
    if r.from_pillar not in pillar_map or r.to_pillar not in pillar_map:
        return ''

    from_pos = PILLAR_POSITIONS.get(r.from_pillar)
    to_pos = PILLAR_POSITIONS.get(r.to_pillar)
    if not from_pos or not to_pos:
        return ''

    fx, fy = from_pos
    tx, ty = to_pos
    rtype = r.relation_type
    color = RELATION_COLORS.get(rtype, '#999')
    severity = {'高': '3', '中': '2', '低': '1.2'}.get(r.severity, '2')
    dash_map = {'冲': '8,4', '刑': '6,3', '害': '3,3', '破': '4,4'}
    dash = dash_map.get(rtype, 'none')

    # 贝塞尔曲线中点偏移
    cx = (fx + tx) / 2
    cy = (fy + ty) / 2
    offset = (idx - total / 2 + 0.5) * 25
    # 垂直于连线的偏移
    dx = tx - fx
    dy = ty - fy
    length = (dx**2 + dy**2) ** 0.5
    if length > 0:
        nx = -dy / length * offset
        ny = dx / length * offset
    else:
        nx = ny = 0
    mx = cx + nx
    my = cy + ny

    path_d = f"M{fx},{fy} Q{mx},{my} {tx},{ty}"
    return (
        f'<g class="relation-arc" data-type="{rtype}" data-from="{r.from_pillar}" data-to="{r.to_pillar}">'
        f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="{severity}" '
        f'stroke-dasharray="{dash}" opacity="0.55" class="relation-path"/>'
        f'<title>{r.from_pillar}{r.to_pillar}{rtype}: {r.description}</title>'
        f'<desc>{r.impact}（严重度: {r.severity}）</desc>'
        f'</g>'
    )


def _render_hover_tooltip(r: RelationVM, pillar_map: dict) -> str:
    """渲染关系弧线的 hover 提示气泡"""
    if r.from_pillar not in pillar_map or r.to_pillar not in pillar_map:
        return ''
    from_pos = PILLAR_POSITIONS.get(r.from_pillar)
    to_pos = PILLAR_POSITIONS.get(r.to_pillar)
    if not from_pos or not to_pos:
        return ''

    mx = (from_pos[0] + to_pos[0]) / 2
    my = (from_pos[1] + to_pos[1]) / 2 - 20

    return (
        f'<g class="tooltip-group" transform="translate({mx},{my})" opacity="0">'
        f'<rect x="-55" y="-28" width="110" height="36" rx="6" '
        f'fill="var(--neo-surface-2, #222)" stroke="var(--neo-border, #444)" stroke-width="1"/>'
        f'<text x="0" y="-10" text-anchor="middle" fill="var(--neo-ink, #ddd)" font-size="11">'
        f'{r.from_pillar}{r.to_pillar}{r.relation_type}</text>'
        f'<text x="0" y="3" text-anchor="middle" fill="var(--neo-ink-soft, #aaa)" font-size="9">'
        f'{r.impact}</text>'
        f'</g>'
    )


def render_pillar_chart(vm: 'DashboardVM', theme: str = 'dark') -> str:
    """生成动态 SVG 命盘

    Args:
        vm: DashboardVM 视图模型
        theme: 'dark' 或 'light'

    Returns:
        完整的 SVG 命盘 HTML
    """
    pillars = vm.pillars
    relations = vm.relations

    if not pillars:
        return '<p class="empty-chart-placeholder">⚠️ 命盘数据未加载，无法渲染命盘图</p>'

    # 建立位置→PillarVM 映射
    pillar_map = {p.position: p for p in pillars}

    # 确定日主柱
    daymaster_pos = '日'
    daymaster_pillar = pillar_map.get('日')
    if not daymaster_pillar:
        # 回退：取第三个柱
        if len(pillars) >= 3:
            daymaster_pos = pillars[2].position

    # 计算五行相生关系用于粒子动画
    wuxing_cycle = ['木', '火', '土', '金', '水']
    wuxing_present = set()
    for p in pillars:
        gan_wx = GAN_WUXING.get(p.gan)
        zhi_wx = ZHI_WUXING.get(p.zhi)
        if gan_wx:
            wuxing_present.add(gan_wx)
        if zhi_wx:
            wuxing_present.add(zhi_wx)

    # 确定主要五行对用于粒子动画
    from_wx = vm.verdict.day_master
    from_wx_5 = GAN_WUXING.get(from_wx, '木')
    to_idx = (wuxing_cycle.index(from_wx_5) + 1) % 5
    to_wx = wuxing_cycle[to_idx]

    svg_parts = []

    # SVG 容器
    svg_parts.append(
        '<svg class="pillar-chart-svg" viewBox="0 0 640 580" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="八字命盘动态图谱">'
    )
    svg_parts.append('<title>八字命盘动态图谱 — 四柱天干地支关系可视化</title>')
    svg_parts.append(
        '<desc>展示年、月、日、时四柱的天干地支、五行属性以及刑冲合害关系</desc>'
    )

    # 背景装饰：淡色网格线
    svg_parts.append('<g class="grid-bg" opacity="0.06">')
    for i in range(0, 640, 40):
        svg_parts.append(
            f'<line x1="{i}" y1="0" x2="{i}" y2="580" stroke="var(--neo-border, #444)"/>'
        )
    for j in range(0, 580, 40):
        svg_parts.append(
            f'<line x1="0" y1="{j}" x2="640" y2="{j}" stroke="var(--neo-border, #444)"/>'
        )
    svg_parts.append('</g>')

    # 五行粒子动画（5个粒子沿相生方向流动）
    if len(wuxing_present) >= 2:
        svg_parts.append('<g class="particle-layer">')
        for i in range(5):
            svg_parts.append(_render_particle_animation(from_wx_5, to_wx, i))
        svg_parts.append('</g>')

    # 连接线：各柱连接到日主
    svg_parts.append('<g class="connection-layer">')
    day_pos = PILLAR_POSITIONS.get(daymaster_pos, (320, 280))
    for pos_key, (px, py) in PILLAR_POSITIONS.items():
        if pos_key != daymaster_pos and pos_key in pillar_map:
            svg_parts.append(
                f'<line x1="{px}" y1="{py}" x2="{day_pos[0]}" y2="{day_pos[1]}" '
                f'stroke="var(--neo-border, #444)" stroke-width="1" opacity="0.12" '
                f'stroke-dasharray="4,6"/>'
            )
    svg_parts.append('</g>')

    # 刑冲合害关系弧线
    if relations:
        svg_parts.append('<g class="relations-layer">')
        for i, r in enumerate(relations):
            arc = _render_relation_arc(r, pillar_map, i, len(relations))
            if arc:
                svg_parts.append(arc)
        svg_parts.append('</g>')

    # hover 提示气泡
    if relations:
        svg_parts.append('<g class="tooltips-layer" style="pointer-events:none">')
        for r in relations:
            if r.from_pillar in pillar_map and r.to_pillar in pillar_map:
                svg_parts.append(_render_hover_tooltip(r, pillar_map))
        svg_parts.append('</g>')

    # 四柱节点
    svg_parts.append('<g class="pillars-layer">')
    for pos_key, (px, py) in PILLAR_POSITIONS.items():
        if pos_key in pillar_map:
            is_day = (pos_key == daymaster_pos)
            svg_parts.append(_render_pillar_node(pillar_map[pos_key], px, py, is_day))
    svg_parts.append('</g>')

    # 五行色调标注
    svg_parts.append('<g class="wuxing-legend" transform="translate(540, 520)">')
    for i, (wx, color) in enumerate(WUXING_COLORS.items()):
        lx = i * 20
        svg_parts.append(
            f'<circle cx="{lx}" cy="0" r="5" fill="{color}" opacity="0.7"/>'
        )
        svg_parts.append(
            f'<text x="{lx + 7}" y="3" fill="var(--neo-muted, #666)" font-size="9">{wx}</text>'
        )
    svg_parts.append('</g>')

    svg_parts.append('</svg>')

    svg_html = '\n'.join(svg_parts)

    # 包装 CSS + 交互 JS
    css = _pillar_chart_css()
    js = _pillar_chart_js()

    export_btn = (
        '<div class="chart-controls">'
        '<button class="chart-btn export-svg-btn" onclick="exportPillarChartSVG()" '
        'aria-label="导出命盘为 SVG 文件">📥 导出 SVG</button>'
        '<button class="chart-btn export-png-btn" onclick="exportPillarChartPNG()" '
        'aria-label="导出命盘为 PNG 图片">🖼️ 导出 PNG</button>'
        '</div>'
    )

    return (
        f'<div class="pillar-chart-container" data-theme="{theme}">'
        f'<style>{css}</style>'
        f'{svg_html}'
        f'{export_btn}'
        f'<script>{js}</script>'
        f'</div>'
    )


def _pillar_chart_css() -> str:
    """命盘图表的 CSS 样式"""
    return r"""
.pillar-chart-container {
    position: relative;
    width: 100%;
    max-width: 680px;
    margin: 0 auto;
    padding: 16px 0;
}
.pillar-chart-svg {
    width: 100%;
    height: auto;
    display: block;
}
.pillar-node {
    cursor: pointer;
    transition: r 0.3s var(--neo-ease, ease);
}
.pillar-node:hover {
    filter: brightness(1.2);
}
.pulse-ring, .pulse-ring-2 {
    pointer-events: none;
}
.gan-text {
    transition: font-size 0.3s ease;
}
.pillar-node:hover + .gan-text,
.gan-text:hover {
    font-size: 24px;
}
.relation-path {
    transition: opacity 0.3s ease, stroke-width 0.3s ease;
}
.relation-arc:hover .relation-path {
    opacity: 0.9 !important;
    stroke-width: 4 !important;
    filter: drop-shadow(0 0 4px currentColor);
}
.relation-arc:hover + .tooltip-group,
.tooltip-group:hover {
    opacity: 1 !important;
    transition: opacity 0.2s ease;
}
.tooltip-group {
    transition: opacity 0.2s ease;
}
.chart-controls {
    display: flex;
    gap: 8px;
    justify-content: center;
    margin-top: 12px;
}
.chart-btn {
    padding: 6px 14px;
    border: 1px solid var(--neo-border, #444);
    border-radius: var(--neo-radius-sm, 8px);
    background: var(--neo-surface, #1a1a2e);
    color: var(--neo-ink-soft, #ccc);
    cursor: pointer;
    font-size: 13px;
    transition: all 0.2s ease;
}
.chart-btn:hover {
    background: var(--neo-surface-2, #2a2a3e);
    border-color: var(--neo-primary, #c4a86c);
    color: var(--neo-primary, #c4a86c);
}
.empty-chart-placeholder {
    text-align: center;
    color: var(--neo-muted, #666);
    padding: 40px;
    font-size: 14px;
}

/* 暗色主题 */
[data-theme="dark"] .pillar-node {
    filter: none;
}
[data-theme="dark"] .pillar-chart-svg text {
    font-family: 'Zhi Mang Xing', 'Ma Shan Zheng', STKaiti, KaiTi, serif;
}

/* 亮色主题 */
[data-theme="light"] .pillar-chart-container {
    background: transparent;
}
[data-theme="light"] .pillar-node {
    fill: #fafaf5;
}

/* 响应式 */
@media (max-width: 680px) {
    .pillar-chart-svg {
        transform: scale(0.85);
        transform-origin: top center;
    }
}
"""


def _pillar_chart_js() -> str:
    """命盘图表的交互 JS"""
    return r"""
(function() {
    // 关系弧线 hover 联动 tooltip
    var arcs = document.querySelectorAll('.relation-arc');
    var tooltips = document.querySelectorAll('.tooltip-group');

    arcs.forEach(function(arc, i) {
        arc.addEventListener('mouseenter', function() {
            if (tooltips[i]) tooltips[i].style.opacity = '1';
        });
        arc.addEventListener('mouseleave', function() {
            if (tooltips[i]) tooltips[i].style.opacity = '0';
        });
    });

    // 导出 SVG
    window.exportPillarChartSVG = function() {
        var svg = document.querySelector('.pillar-chart-svg');
        if (!svg) return;
        var clone = svg.cloneNode(true);
        // 移除动画元素以生成静态快照
        clone.querySelectorAll('animate,animateMotion').forEach(function(el) { el.remove(); });
        var data = new XMLSerializer().serializeToString(clone);
        var blob = new Blob(['<?xml version="1.0" encoding="UTF-8"?>' + data],
                           {type: 'image/svg+xml;charset=utf-8'});
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'bazi-pillar-chart.svg';
        a.click();
        URL.revokeObjectURL(url);
    };

    // 导出 PNG（通过 canvas）
    window.exportPillarChartPNG = function() {
        var svg = document.querySelector('.pillar-chart-svg');
        if (!svg) return;
        var clone = svg.cloneNode(true);
        clone.querySelectorAll('animate,animateMotion').forEach(function(el) { el.remove(); });
        var data = new XMLSerializer().serializeToString(clone);
        var blob = new Blob(['<?xml version="1.0" encoding="UTF-8"?>' + data],
                           {type: 'image/svg+xml;charset=utf-8'});

        var url = URL.createObjectURL(blob);
        var img = new Image();
        img.onload = function() {
            var canvas = document.createElement('canvas');
            var svgRect = svg.getBoundingClientRect();
            var scale = 2;
            canvas.width = 640 * scale;
            canvas.height = 580 * scale;
            var ctx = canvas.getContext('2d');
            ctx.fillStyle = '#1a1a2e';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            canvas.toBlob(function(pngBlob) {
                var pngUrl = URL.createObjectURL(pngBlob);
                var a = document.createElement('a');
                a.href = pngUrl;
                a.download = 'bazi-pillar-chart.png';
                a.click();
                URL.revokeObjectURL(pngUrl);
            }, 'image/png');
        };
        img.src = url;
    };
})();
"""
