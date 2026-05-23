#!/usr/bin/env python3
"""
bazi-pro 推理图谱 DAG v5.0 — 纯 SVG 节点-边图 + 置信度热力图 + zoom/pan
展示旺衰→格局→喜用的推理链和证据支持/反证关系
"""

from bazi_pro.view_model import DashboardVM, TraceStageVM

# 节点布局位置（分层）
NODE_LAYERS = {
    'parse': (0, 320, 80),
    'strength': (1, 200, 200),
    'retrieval_positive': (1, 440, 200),
    'pattern': (2, 320, 320),
    'yongshen': (3, 200, 440),
    'final_decision': (4, 320, 560),
}

STAGE_COLORS = {
    'done': '#5f8d72',
    'partial': '#b98b54',
    'pending': '#7f8c8d',
    'failed': '#c0392b',
}


def _confidence_color(confidence: float) -> str:
    """置信度→颜色映射（热力图效果）"""
    if confidence >= 0.85:
        return '#5f8d72'  # 高：绿色
    elif confidence >= 0.70:
        return '#7fbfa0'  # 中高：浅绿
    elif confidence >= 0.55:
        return '#b98b54'  # 中：橙色
    elif confidence >= 0.40:
        return '#d4a76a'  # 中低：浅橙
    else:
        return '#c0392b'  # 低：红色


def _confidence_opacity(stage_order: str) -> float:
    """根据推理步骤衰减透明度（越往后越高）"""
    order_map = {
        'parse': 0.55, 'strength': 0.65,
        'retrieval_positive': 0.70, 'retrieval_counterfactual': 0.70,
        'pattern': 0.80, 'yongshen': 0.90,
        'final_decision': 1.0,
    }
    return order_map.get(stage_order, 0.75)


def _layout_nodes(stages: list) -> list[dict]:
    """自动布局节点位置"""
    # 使用力导向简化：按层排列
    default_layers = [
        (0, 320, 80),
        (1, 180, 200),
        (1, 460, 200),
        (2, 320, 320),
        (3, 180, 440),
        (3, 460, 440),
        (4, 320, 560),
    ]

    positioned = []
    for i, stage in enumerate(stages):
        layer_idx = min(i, len(default_layers) - 1)
        layer, x, y = default_layers[layer_idx]
        # 同层微调
        same_layer = [n for n in positioned if n['layer'] == layer]
        offset_y = len(same_layer) * 70
        positioned.append({
            'id': stage.stage_id,
            'title': stage.title,
            'summary': stage.summary,
            'confidence': stage.confidence or 0.5,
            'status': stage.status,
            'x': x,
            'y': y + offset_y,
            'layer': layer,
            'rules': stage.rules,
            'positive': stage.positive_evidence,
            'counter': stage.counter_evidence,
        })
    return positioned


def render_reasoning_graph(vm: 'DashboardVM') -> str:
    """生成推理图谱 DAG HTML

    以节点-边图展示从数据校验到最终裁决的完整推理链

    Args:
        vm: DashboardVM 视图模型

    Returns:
        完整的推理图谱 HTML
    """
    stages = vm.trace_stages
    if not stages:
        stages = _default_stages(vm)

    nodes = _layout_nodes(stages)
    if not nodes:
        return '<p class="empty-graph-placeholder">⚠️ 推理数据未加载，无法渲染图谱</p>'

    # 计算 SVG 范围
    max_x = max(n['x'] for n in nodes) + 200
    max_y = max(n['y'] for n in nodes) + 120
    view_w = max(max_x, 700)
    view_h = max(max_y, 650)

    svg_parts = [
        f'<svg class="reasoning-graph-svg" viewBox="0 0 {view_w} {view_h}" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="八字推理链图谱">',
        '<title>八字推理链图谱 — DAG 证据网络</title>',
        '<desc>展示旺衰判断、格局判定、喜用神裁决的推理链及证据支持/反证关系</desc>',
        '<defs>',
        # 箭头标记
        '<marker id="arrowSolid" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">'
        '<polygon points="0 0, 8 3, 0 6" fill="var(--neo-ink-soft, #999)"/>'
        '</marker>',
        '<marker id="arrowDashed" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">'
        '<polygon points="0 0, 8 3, 0 6" fill="#c0392b"/>'
        '</marker>',
        # 光晕滤镜
        '<filter id="nodeGlow">'
        '<feGaussianBlur stdDeviation="3" result="blur"/>'
        '<feComposite in="SourceGraphic" in2="blur" operator="over"/>'
        '</filter>',
        '</defs>',
    ]

    # 背景网格（暗色增强深度感）
    svg_parts.append('<g class="graph-grid" opacity="0.04">')
    for gx in range(0, int(view_w), 50):
        svg_parts.append(
            f'<line x1="{gx}" y1="0" x2="{gx}" y2="{view_h}" stroke="#fff"/>'
        )
    for gy in range(0, int(view_h), 50):
        svg_parts.append(
            f'<line x1="0" y1="{gy}" x2="{view_w}" y2="{gy}" stroke="#fff"/>'
        )
    svg_parts.append('</g>')

    # 边：正向推理（实线）
    svg_parts.append('<g class="graph-edges-positive">')
    for i in range(len(nodes) - 1):
        src, dst = nodes[i], nodes[i + 1]
        # 仅在相邻层之间画边
        if dst['layer'] == src['layer'] + 1 or dst['layer'] == src['layer']:
            sw = 2.5
            color = 'var(--neo-ink-soft, #999)'
            svg_parts.append(
                f'<line x1="{src["x"]}" y1="{src["y"] + 30}" '
                f'x2="{dst["x"]}" y2="{dst["y"] - 30}" '
                f'stroke="{color}" stroke-width="{sw}" '
                f'marker-end="url(#arrowSolid)" opacity="0.5" class="graph-edge"/>'
            )
    svg_parts.append('</g>')

    # 边：反证（红色虚线——从有counter_evidence的节点出发）
    svg_parts.append('<g class="graph-edges-counter">')
    for node in nodes:
        if node['counter']:
            # 向右上方画虚线到"反证空间"
            svg_parts.append(
                f'<line x1="{node["x"]}" y1="{node["y"]}" '
                f'x2="{node["x"] + 80}" y2="{node["y"] - 60}" '
                f'stroke="#c0392b" stroke-width="1.5" stroke-dasharray="5,4" '
                f'marker-end="url(#arrowDashed)" opacity="0.4" class="counter-edge"/>'
            )
    svg_parts.append('</g>')

    # 节点
    svg_parts.append('<g class="graph-nodes">')
    for node in nodes:
        cx, cy = node['x'], node['y']
        conf = node['confidence']
        color = _confidence_color(conf)
        opacity = _confidence_opacity(node['id'])
        status = node['status']
        node_color = STAGE_COLORS.get(status, '#b98b54')

        # 置信度热力背景
        svg_parts.append(
            f'<rect x="{cx - 90}" y="{cy - 28}" width="180" height="56" rx="12" '
            f'fill="{color}" opacity="{opacity * 0.15}" class="confidence-bg"/>'
        )

        # 节点外框
        svg_parts.append(
            f'<rect x="{cx - 90}" y="{cy - 28}" width="180" height="56" rx="12" '
            f'fill="var(--neo-surface, #1a1a2e)" '
            f'stroke="{node_color}" stroke-width="2" '
            f'class="graph-node" data-node-id="{node["id"]}" tabindex="0" '
            f'role="button" aria-label="{node["title"]}：{node["summary"]}">'
            f'<title>{node["title"]}（置信度 {conf:.0%}）</title>'
            f'<desc>{node["summary"]}</desc>'
            f'</rect>'
        )

        # 节点标题
        svg_parts.append(
            f'<text x="{cx}" y="{cy - 6}" text-anchor="middle" '
            f'fill="var(--neo-ink, #ddd)" font-size="13" font-weight="700" '
            f'class="node-title">{node["title"]}</text>'
        )

        # 置信度数值
        svg_parts.append(
            f'<text x="{cx}" y="{cy + 14}" text-anchor="middle" '
            f'fill="{color}" font-size="11" font-weight="600" class="node-confidence">'
            f'置信度 {conf:.0%}</text>'
        )

        # 状态指示点
        svg_parts.append(
            f'<circle cx="{cx + 80}" cy="{cy - 20}" r="5" fill="{node_color}" '
            f'class="status-indicator"/>'
        )

        # 规则标签（在节点右侧）
        if node['rules']:
            rule_y = cy - 10
            for rule in node['rules'][:2]:  # 最多显示 2 条
                svg_parts.append(
                    f'<text x="{cx + 95}" y="{rule_y}" text-anchor="start" '
                    f'fill="var(--neo-muted, #666)" font-size="9" class="rule-label">'
                    f'· {rule[:20]}</text>'
                )
                rule_y += 12

        # 反证标记
        if node['counter']:
            svg_parts.append(
                f'<text x="{cx + 80}" y="{cy + 18}" text-anchor="middle" '
                f'fill="#c0392b" font-size="9" font-weight="600" class="counter-badge">'
                f'反证×{len(node["counter"])}</text>'
            )

    svg_parts.append('</g>')

    # 图例
    legend_x = view_w - 180
    legend_y = 20
    svg_parts.append(f'<g class="graph-legend" transform="translate({legend_x},{legend_y})">')
    svg_parts.append(
        '<rect x="-10" y="-8" width="170" height="95" rx="6" '
        'fill="var(--neo-surface-2, #222)" stroke="var(--neo-border, #444)" stroke-width="1"/>'
    )
    legend_items = [
        ('done', '已完成'), ('partial', '进行中'),
        ('pending', '待执行'), ('failed', '失败'),
    ]
    for i, (status, label) in enumerate(legend_items):
        ly = i * 20
        color = STAGE_COLORS.get(status, '#999')
        svg_parts.append(
            f'<circle cx="10" cy="{ly + 4}" r="5" fill="{color}"/>'
        )
        svg_parts.append(
            f'<text x="22" y="{ly + 8}" fill="var(--neo-ink-soft, #ccc)" font-size="10">{label}</text>'
        )
    svg_parts.append('</g>')

    svg_parts.append('</svg>')

    svg_html = '\n'.join(svg_parts)

    css = _reasoning_graph_css()
    js = _reasoning_graph_js()

    return (
        f'<div class="reasoning-graph-container">'
        f'<style>{css}</style>'
        f'<div class="graph-canvas-wrapper" id="graphCanvas">{svg_html}</div>'
        f'<div class="graph-info-bar">'
        f'<span>🖱️ 滚轮缩放 | 拖拽平移 | 点击节点展开详情</span>'
        f'<button class="graph-btn" onclick="resetGraphZoom()">↺ 重置视图</button>'
        f'<button class="graph-btn" onclick="exportReasoningGraphSVG()">📥 导出 SVG</button>'
        f'</div>'
        f'<div class="graph-detail-panel" id="graphDetail" style="display:none"></div>'
        f'<script>{js}</script>'
        f'</div>'
    )


def _default_stages(vm: 'DashboardVM') -> list:
    """当无 trace 数据时，从 ViewModel 构建默认推理步骤"""
    stages = []
    evidence_data = vm.evidence if vm.evidence else []

    stages.append(TraceStageVM(
        stage_id='strength', title='日主旺衰', summary=vm.verdict.summary_line,
        confidence=vm.verdict.confidence, status='done',
        rules=[f'日主{vm.day_master}', f'格局{vm.verdict.pattern}'],
    ))

    stages.append(TraceStageVM(
        stage_id='pattern', title='格局判定', summary=vm.verdict.pattern,
        confidence=vm.verdict.confidence, status='done',
        rules=[vm.verdict.decision],
    ))

    stages.append(TraceStageVM(
        stage_id='yongshen', title='喜用神裁决',
        summary=f'用神: {",".join(vm.verdict.yongshen)} | 喜神: {",".join(vm.verdict.xishen)}',
        confidence=vm.verdict.confidence, status='done',
        rules=[f'忌神: {",".join(vm.verdict.jishen)}'],
    ))

    for ev in evidence_data:
        stages.append(TraceStageVM(
            stage_id=ev.stage_id, title=ev.title, summary=ev.claim,
            confidence=ev.confidence, status='done',
            rules=ev.rules, positive_evidence=ev.classics,
            counter_evidence=[ev.counter_evidence] if ev.counter_evidence else [],
        ))

    return stages


def _reasoning_graph_css() -> str:
    """推理图谱 CSS"""
    return r"""
.reasoning-graph-container {
    position: relative;
    width: 100%;
    padding: 8px 0;
}
.graph-canvas-wrapper {
    overflow: hidden;
    border: 1px solid var(--neo-border, #333);
    border-radius: var(--neo-radius-md, 16px);
    background: var(--neo-bg, #111122);
    cursor: grab;
    position: relative;
}
.graph-canvas-wrapper:active {
    cursor: grabbing;
}
.graph-canvas-wrapper.panning {
    cursor: grabbing;
}
.reasoning-graph-svg {
    width: 100%;
    height: auto;
    display: block;
    transition: transform 0.1s ease-out;
}
.graph-node {
    cursor: pointer;
    transition: stroke-width 0.2s ease, filter 0.2s ease;
}
.graph-node:hover, .graph-node:focus {
    stroke-width: 3.5 !important;
    filter: url(#nodeGlow);
    outline: none;
}
.graph-node.active-node {
    stroke-width: 3.5 !important;
    filter: url(#nodeGlow);
}
.graph-edge {
    transition: opacity 0.2s ease;
}
.counter-edge {
    transition: opacity 0.2s ease;
}
.counter-edge:hover {
    opacity: 0.8 !important;
}
.confidence-bg {
    transition: opacity 0.3s ease;
}
.graph-info-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    font-size: 11px;
    color: var(--neo-muted, #666);
    gap: 12px;
    flex-wrap: wrap;
}
.graph-btn {
    padding: 4px 10px;
    border: 1px solid var(--neo-border, #444);
    border-radius: var(--neo-radius-sm, 6px);
    background: var(--neo-surface, #1a1a2e);
    color: var(--neo-ink-soft, #ccc);
    cursor: pointer;
    font-size: 11px;
    transition: all 0.2s ease;
}
.graph-btn:hover {
    background: var(--neo-surface-2, #2a2a3e);
    border-color: var(--neo-primary, #c4a86c);
    color: var(--neo-primary, #c4a86c);
}
.graph-detail-panel {
    margin-top: 12px;
    padding: 16px;
    background: var(--neo-surface-2, #1e1e30);
    border: 1px solid var(--neo-border, #333);
    border-radius: var(--neo-radius-md, 12px);
    font-size: 13px;
    color: var(--neo-ink-soft, #ccc);
    line-height: 1.6;
}
.graph-detail-panel h3 {
    margin: 0 0 8px 0;
    font-size: 15px;
}
.graph-detail-panel .detail-rules {
    margin: 8px 0;
    padding-left: 16px;
}
.graph-detail-panel .detail-counter {
    color: #c0392b;
    border-left: 3px solid #c0392b;
    padding-left: 12px;
    margin-top: 8px;
}
.empty-graph-placeholder {
    text-align: center;
    color: var(--neo-muted, #666);
    padding: 30px;
    font-size: 14px;
}
"""


def _reasoning_graph_js() -> str:
    """推理图谱交互 JS：zoom/pan + 节点展开"""
    return r"""
(function() {
    var wrapper = document.querySelector('.graph-canvas-wrapper');
    var svg = document.querySelector('.reasoning-graph-svg');
    var detail = document.getElementById('graphDetail');
    if (!wrapper || !svg) return;

    var scale = 1;
    var translateX = 0, translateY = 0;
    var isPanning = false;
    var startX, startY, startTX, startTY;

    function applyTransform() {
        svg.style.transform = 'translate(' + translateX + 'px, ' + translateY + 'px) scale(' + scale + ')';
    }

    // 缩放
    wrapper.addEventListener('wheel', function(e) {
        e.preventDefault();
        var delta = e.deltaY > 0 ? -0.1 : 0.1;
        scale = Math.max(0.3, Math.min(3, scale + delta));
        applyTransform();
    });

    // 平移
    wrapper.addEventListener('mousedown', function(e) {
        if (e.target.closest('.graph-node')) return;
        isPanning = true;
        wrapper.classList.add('panning');
        startX = e.clientX;
        startY = e.clientY;
        startTX = translateX;
        startTY = translateY;
    });

    window.addEventListener('mousemove', function(e) {
        if (!isPanning) return;
        translateX = startTX + (e.clientX - startX);
        translateY = startTY + (e.clientY - startY);
        applyTransform();
    });

    window.addEventListener('mouseup', function() {
        isPanning = false;
        if (wrapper) wrapper.classList.remove('panning');
    });

    // 重置
    window.resetGraphZoom = function() {
        scale = 1;
        translateX = 0;
        translateY = 0;
        applyTransform();
    };

    // 节点点击展开详情
    var nodes = document.querySelectorAll('.graph-node');
    nodes.forEach(function(node) {
        node.addEventListener('click', function(e) {
            e.stopPropagation();
            nodes.forEach(function(n) { n.classList.remove('active-node'); });
            node.classList.add('active-node');

            var title = (node.querySelector('title') || {}).textContent || '';
            var desc = (node.querySelector('desc') || {}).textContent || '';
            var confEl = node.parentElement.querySelector('.node-confidence');
            var confidence = confEl ? confEl.textContent : '';
            var rules = [];
            var ruleEls = node.parentElement.querySelectorAll('.rule-label');
            ruleEls.forEach(function(r) { rules.push(r.textContent); });
            var counterBadge = node.parentElement.querySelector('.counter-badge');
            var hasCounter = counterBadge && counterBadge.textContent;

            var html = '<h3>' + title + '</h3>';
            html += '<p>' + desc + '</p>';
            html += '<p><strong>' + confidence + '</strong></p>';
            if (rules.length > 0) {
                html += '<div class="detail-rules"><strong>规则依据：</strong><br>' +
                        rules.join('<br>') + '</div>';
            }
            if (hasCounter) {
                html += '<div class="detail-counter"><strong>反证提示：</strong> ' +
                        hasCounter + '</div>';
            }
            if (detail) {
                detail.innerHTML = html;
                detail.style.display = 'block';
            }
        });
    });

    // 导出 SVG
    window.exportReasoningGraphSVG = function() {
        if (!svg) return;
        svg.style.transform = '';
        var clone = svg.cloneNode(true);
        svg.style.transform = 'translate(' + translateX + 'px, ' + translateY + 'px) scale(' + scale + ')';
        var data = new XMLSerializer().serializeToString(clone);
        var blob = new Blob(['<?xml version="1.0" encoding="UTF-8"?>' + data],
                           {type: 'image/svg+xml;charset=utf-8'});
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'bazi-reasoning-graph.svg';
        a.click();
        URL.revokeObjectURL(url);
    };
})();
"""
