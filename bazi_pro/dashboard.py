#!/usr/bin/env python3
"""
八字命理仪表盘生成器 v5.0 — Evidence Inspector + 刑冲合害关系图谱
零外部依赖，纯 HTML+CSS+SVG
v5.0: Evidence Inspector(可展开证据面板) + 刑冲合害图(SVG节点关系网)
v2.0: 天干五行着色、评分分级色环、五行横向条、系统主题检测
"""

import math
import re
from html import escape

GAN_WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火',
    '戊': '土', '己': '土', '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}
ZHI_WUXING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水',
}
WUXING_COLORS = {
    '木': '#4caf50', '火': '#ef5350', '土': '#ff9800',
    '金': '#e0c878', '水': '#42a5f5',
}
WUXING_COLORS_DIM = {
    '木': '#2e7d32', '火': '#b71c1c', '土': '#e65100',
    '金': '#a08850', '水': '#1565c0',
}

# ── CSS (v3.0: +evidence panels, +graph) ──
DASHBOARD_CSS = r'''
:root {
    --bg: #12121a; --bg-card: #1c1c28; --bg-pillar: #222236;
    --text: #e8e0d0; --text-dim: #9998b0; --accent: #d4af37;
    --accent-glow: #f0d060; --wood: #4caf50; --fire: #ef5350;
    --earth: #ff9800; --metal: #e0c878; --water: #42a5f5;
    --good: #66bb6a; --warn: #ffa726; --bad: #ef5350;
    --border: #2e2e44; --shadow: 0 2px 20px rgba(0,0,0,0.5);
    --radius: 10px; --gap: 14px;
    --bar-wood: #66bb6a; --bar-fire: #ef5350; --bar-earth: #ffa726;
    --bar-metal: #fdd835; --bar-water: #42a5f5;
    --he-color: #ffd700; --chong-color: #ff4444; --xing-color: #cc66ff;
    --hai-color: #888888; --sanhe-color: #44ddcc;
}
@media (prefers-color-scheme: light) {
    :root {
        --bg: #faf6ed; --bg-card: #fffef7; --bg-pillar: #fdf5e8;
        --text: #3a2510; --text-dim: #887860; --accent: #8b4513;
        --accent-glow: #a0522d; --border: #e0d0b8;
        --shadow: 0 2px 16px rgba(60,30,10,0.08);
        --bar-wood: #4caf50; --bar-fire: #ef5350; --bar-earth: #ff9800;
        --bar-metal: #f9a825; --bar-water: #42a5f5;
        --he-color: #b8860b; --chong-color: #cc0000; --xing-color: #9933cc;
        --hai-color: #888888; --sanhe-color: #008877;
    }
}
[data-theme="light"] {
    --bg: #faf6ed; --bg-card: #fffef7; --bg-pillar: #fdf5e8;
    --text: #3a2510; --text-dim: #887860; --accent: #8b4513;
    --accent-glow: #a0522d; --border: #e0d0b8;
    --shadow: 0 2px 16px rgba(60,30,10,0.08);
    --bar-wood: #4caf50; --bar-fire: #ef5350; --bar-earth: #ff9800;
    --bar-metal: #f9a825; --bar-water: #42a5f5;
    --he-color: #b8860b; --chong-color: #cc0000; --xing-color: #9933cc;
    --hai-color: #888888; --sanhe-color: #008877;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Noto Serif SC","Noto Serif CJK SC","Source Han Serif SC","STSong","SimSun","Microsoft YaHei",serif;background:var(--bg);color:var(--text);min-height:100vh;line-height:1.75;font-size:15px}
a{color:var(--accent)}
.container{max-width:960px;margin:0 auto;padding:20px}

.header{text-align:center;padding:40px 16px 24px}
.header .bazi{font-size:34px;font-weight:800;letter-spacing:8px;color:var(--accent-glow);margin-bottom:8px;text-shadow:0 1px 4px rgba(0,0,0,0.2)}
.header .sub{font-size:14px;color:var(--text-dim)}

.theme-btn{position:fixed;top:14px;right:18px;z-index:99;
    background:var(--bg-card);border:1.5px solid var(--border);
    color:var(--text);padding:10px 16px;border-radius:22px;
    cursor:pointer;font-size:16px;transition:all .2s;box-shadow:var(--shadow)}
.theme-btn:hover{transform:scale(1.05)}

/* Pillars */
.pillars{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--gap);margin:20px 0 24px}
.pillar{background:var(--bg-pillar);border:2px solid var(--border);
    border-radius:var(--radius);padding:18px 12px;text-align:center;
    transition:all .25s;position:relative;overflow:hidden}
.pillar:hover{transform:translateY(-3px);box-shadow:var(--shadow)}
.pillar::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
    background:var(--pillar-accent, var(--accent));border-radius:var(--radius) var(--radius) 0 0}
.pillar .gan{font-size:40px;font-weight:800;line-height:1.15;color:var(--pillar-color, var(--accent))}
.pillar .zhi{font-size:22px;color:var(--pillar-zhi-color, var(--text-dim));margin:4px 0 2px}
.pillar .label{font-size:11px;color:var(--text-dim);text-transform:uppercase;letter-spacing:2px}
.pillar .shishen{font-size:13px;margin-top:8px;padding:3px 10px;border-radius:12px;display:inline-block;
    background:var(--border);color:var(--text);font-weight:500}

.grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--gap);margin:var(--gap) 0}
@media(max-width:640px){.grid{grid-template-columns:1fr}.pillars{grid-template-columns:repeat(2,1fr)}}
.card{background:var(--bg-card);border:1.5px solid var(--border);
    border-radius:var(--radius);padding:20px;box-shadow:var(--shadow)}
.card h3{font-size:13px;color:var(--text-dim);margin-bottom:14px;letter-spacing:2px;text-transform:uppercase}
.card.full{grid-column:1/-1}

/* Score ring */
.score-ring-wrap{width:100px;height:100px;margin:0 auto}
.score-ring-wrap circle{fill:none;stroke-width:7}
.score-ring-wrap .bg{stroke:var(--border)}
.score-text{font-size:28px;font-weight:800;text-anchor:middle;dominant-baseline:central}

/* Radar */
.radar-svg{width:100%;max-width:380px;margin:0 auto;display:block}
.radar-label{font-size:14px;font-weight:700;text-anchor:middle}

/* 五行色条 */
.wx-bars{display:flex;flex-direction:column;gap:8px;margin-top:6px}
.wx-bar-row{display:flex;align-items:center;gap:8px}
.wx-bar-label{width:28px;text-align:right;font-size:14px;font-weight:700;flex-shrink:0}
.wx-bar-track{flex:1;height:12px;background:var(--border);border-radius:6px;overflow:hidden}
.wx-bar-fill{height:100%;border-radius:6px;transition:width .4s}
.wx-bar-pct{width:44px;text-align:right;font-size:13px;color:var(--text-dim);flex-shrink:0}

/* Timeline */
.timeline{display:flex;overflow-x:auto;gap:8px;padding:10px 0;scrollbar-width:thin}
.timeline::-webkit-scrollbar{height:5px}
.timeline::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.tl-item{flex:0 0 auto;min-width:88px;text-align:center;padding:10px 8px;border-radius:var(--radius);
    background:var(--bg-pillar);border:2px solid var(--border);cursor:default;transition:all .2s;position:relative}
.tl-item::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
    background:var(--tl-accent, var(--border));border-radius:var(--radius) var(--radius) 0 0}
.tl-item:hover{transform:translateY(-3px);box-shadow:var(--shadow)}
.tl-item .tl-ganzhi{font-size:18px;font-weight:700}
.tl-item .tl-gan{color:var(--tl-gan-color, var(--text))}
.tl-item .tl-zhi{color:var(--tl-zhi-color, var(--text-dim));margin-left:2px}
.tl-item .tl-age{font-size:12px;color:var(--text-dim);margin-top:4px}
.tl-item .tl-badge{font-size:11px;padding:2px 8px;border-radius:10px;margin-top:6px;display:inline-block;font-weight:600}
.tl-good{--tl-accent:var(--good)}.tl-good .tl-badge{background:#0d3a1a;color:var(--good)}
.tl-warn{--tl-accent:var(--warn)}.tl-warn .tl-badge{background:#3a2a08;color:var(--warn)}
.tl-bad{--tl-accent:var(--bad)}.tl-bad .tl-badge{background:#3a0a0a;color:var(--bad)}
.tl-neutral{--tl-accent:var(--border)}

/* ── v3.0: Evidence Inspector ── */
.evidence-section{margin:var(--gap) 0}
.evidence-card{background:var(--bg-card);border:1.5px solid var(--border);border-radius:var(--radius);
    margin-bottom:10px;overflow:hidden}
.evidence-card summary{padding:14px 20px;cursor:pointer;font-weight:600;font-size:15px;
    color:var(--accent-glow);list-style:none;display:flex;justify-content:space-between;align-items:center}
.evidence-card summary::-webkit-details-marker{display:none}
.evidence-card summary::after{content:'▾';font-size:12px;color:var(--text-dim);transition:transform .3s}
.evidence-card[open] summary::after{transform:rotate(180deg)}
.evidence-card .evi-body{padding:0 20px 16px;font-size:14px;line-height:1.8}
.evidence-card .evi-row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border);font-size:13px}
.evidence-card .evi-row:last-child{border-bottom:none}
.evi-label{color:var(--text-dim);flex-shrink:0}
.evi-value{text-align:right;font-weight:500;max-width:65%;word-break:break-all}
.evi-confidence{display:inline-block;padding:2px 8px;border-radius:8px;font-size:12px;font-weight:700}
.conf-high{background:#0d3a1a;color:var(--good)}
.conf-mid{background:#3a2a08;color:var(--warn)}
.conf-low{background:#3a0a0a;color:var(--bad)}
.evi-classic{display:inline-block;background:var(--bg-pillar);padding:2px 8px;border-radius:6px;
    font-size:12px;margin:2px 4px 2px 0;font-family:monospace;color:var(--accent)}
.evi-counter{color:var(--warn);font-size:13px;padding:8px 12px;margin-top:8px;
    background:rgba(255,167,38,0.1);border-left:3px solid var(--warn);border-radius:0 var(--radius) var(--radius) 0}

/* ── v3.0: 关系图谱 ── */
.relation-graph{width:100%;max-width:600px;margin:0 auto;display:block}
.graph-node text{font-size:13px;font-weight:600;text-anchor:middle;fill:var(--text)}
.graph-node .sub{font-size:11px;fill:var(--text-dim)}
.graph-edge line{stroke-width:2;opacity:0.7}
.graph-edge.he line{stroke:var(--he-color);stroke-dasharray:none}
.graph-edge.chong line{stroke:var(--chong-color);stroke-dasharray:6,2}
.graph-edge.xing line{stroke:var(--xing-color);stroke-dasharray:2,2}
.graph-edge.hai line{stroke:var(--hai-color);stroke-dasharray:3,3}
.graph-edge.sanhe line{stroke:var(--sanhe-color);stroke-dasharray:10,2}
.legend{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;margin-top:10px;font-size:12px}
.legend span{display:inline-flex;align-items:center;gap:4px}
.legend .swatch{width:14px;height:3px;border-radius:2px;display:inline-block}

/* Info rows */
.info-row{display:flex;justify-content:space-between;align-items:center;
    padding:10px 0;border-bottom:1px solid var(--border);font-size:15px}
.info-row:last-child{border-bottom:none}
.info-label{color:var(--text-dim);flex-shrink:0}
.info-value{font-weight:700;color:var(--accent-glow);text-align:right;max-width:60%;word-break:break-all}

/* Collapsible analysis */
.analysis-toggle{text-align:center;margin:24px 0}
.analysis-toggle button{background:var(--bg-card);border:1.5px solid var(--border);
    color:var(--accent-glow);padding:12px 32px;border-radius:24px;
    cursor:pointer;font-size:15px;font-weight:600;transition:all .2s;box-shadow:var(--shadow)}
.analysis-toggle button:hover{transform:scale(1.03);opacity:0.9}
.analysis-content{max-height:0;overflow:hidden;transition:max-height .6s ease}
.analysis-content.open{max-height:none}
.analysis-content h1,.analysis-content h2,.analysis-content h3{color:var(--accent);margin:18px 0 10px}
.analysis-content table{width:100%;border-collapse:collapse;font-size:14px;margin:12px 0}
.analysis-content table th{background:var(--bg-pillar);padding:8px 10px;border:1px solid var(--border);font-weight:600}
.analysis-content table td{padding:8px 10px;border:1px solid var(--border);text-align:center}
.analysis-content pre{background:#14182a;color:#b8cce0;padding:14px;border-radius:var(--radius);overflow-x:auto;font-size:13px}
.analysis-content blockquote{border-left:4px solid var(--accent);padding:10px 18px;margin:12px 0;background:var(--bg-pillar);border-radius:0 var(--radius) var(--radius) 0}
.analysis-content hr{border:none;border-top:1.5px solid var(--border);margin:22px 0}
.analysis-content ul,.analysis-content ol{padding-left:22px;margin:10px 0;font-size:14px}
.analysis-content li{margin:5px 0;line-height:1.7}

.footer{text-align:center;padding:28px;color:var(--text-dim);font-size:12px;
    border-top:1.5px solid var(--border);margin-top:28px;line-height:1.8}
'''


# ── Helper functions (unchanged from v2.0) ──

def _wuxing_bar_html(wuxing: dict) -> str:
    order = ['木', '火', '土', '金', '水']
    bars = []
    for wx in order:
        pct = wuxing.get(wx, 0)
        color = WUXING_COLORS.get(wx, 'var(--accent)')
        bars.append(f'<div class="wx-bar-row"><span class="wx-bar-label" style="color:{color}">{wx}</span><div class="wx-bar-track"><div class="wx-bar-fill" style="width:{pct:.1f}%;background:{color}"></div></div><span class="wx-bar-pct">{pct:.1f}%</span></div>')
    return '<div class="wx-bars">' + '\n'.join(bars) + '</div>'


def _draw_radar_svg(wuxing: dict) -> str:
    labels = ['木', '火', '土', '金', '水']
    values = [wuxing.get(k, 0) for k in labels]
    cx, cy, r = 180, 180, 130
    parts = ['<svg class="radar-svg" viewBox="0 0 360 360" xmlns="http://www.w3.org/2000/svg">']
    for level in range(1, 6):
        lr = r * level / 5
        pts = []
        for i in range(5):
            angle = -math.pi / 2 + i * 2 * math.pi / 5
            pts.append(f'{cx + lr * math.cos(angle):.1f},{cy + lr * math.sin(angle):.1f}')
        parts.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="var(--border)" stroke-width="1" opacity="0.4"/>')
    for i in range(5):
        angle = -math.pi / 2 + i * 2 * math.pi / 5
        ex, ey = cx + r * math.cos(angle), cy + r * math.sin(angle)
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="var(--border)" stroke-width="1" opacity="0.25"/>')
    data_pts = []
    for i in range(5):
        angle = -math.pi / 2 + i * 2 * math.pi / 5
        val = min(values[i], 100) / 100.0
        data_pts.append(f'{cx + r * val * math.cos(angle):.1f},{cy + r * val * math.sin(angle):.1f}')
    parts.append(f'<polygon points="{" ".join(data_pts)}" fill="var(--accent)" fill-opacity="0.2" stroke="var(--accent-glow)" stroke-width="2.5" stroke-linejoin="round"/>')
    for i, pt in enumerate(data_pts):
        x, y = pt.split(',')
        color = WUXING_COLORS.get(labels[i], 'var(--accent-glow)')
        parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{color}" stroke="{color}" stroke-width="1.5" opacity="0.9"/>')
    for i in range(5):
        angle = -math.pi / 2 + i * 2 * math.pi / 5
        lx, ly = cx + (r + 30) * math.cos(angle), cy + (r + 30) * math.sin(angle)
        color = WUXING_COLORS.get(labels[i], 'var(--accent)')
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" class="radar-label" fill="{color}">{labels[i]}</text>')
        plx, ply = cx + (r + 48) * math.cos(angle), cy + (r + 48) * math.sin(angle)
        parts.append(f'<text x="{plx:.1f}" y="{ply:.1f}" class="radar-label" font-size="11" fill="var(--text-dim)">{values[i]:.1f}%</text>')
    parts.append('</svg>')
    return '\n'.join(parts)


def _score_ring_svg(score: int, max_score: int = 100) -> str:
    pct = score / max_score
    circumference = 2 * math.pi * 34
    if score >= 80: color, glow = '#66bb6a', '#a5d6a7'
    elif score >= 60: color, glow = '#4caf50', '#81c784'
    elif score >= 40: color, glow = '#ffa726', '#ffcc80'
    else: color, glow = '#ef5350', '#ef9a9a'
    dash = pct * circumference
    return f'''<svg class="score-ring-wrap" viewBox="0 0 100 100">
    <circle class="bg" cx="50" cy="50" r="34"/>
    <circle cx="50" cy="50" r="34" fill="none" stroke="{color}" stroke-width="7"
        stroke-dasharray="{dash:.1f} {circumference:.1f}" stroke-linecap="round"
        transform="rotate(-90 50 50)"/>
    <text class="score-text" x="50" y="47" fill="{glow}">{score}</text>
    <text x="50" y="62" font-size="11" fill="var(--text-dim)" text-anchor="middle">/ 100</text>
</svg>'''


def _timeline_html(dayun_list: list) -> str:
    if not dayun_list:
        return '<p style="color:var(--text-dim);text-align:center">大运数据未提取</p>'
    ji_map = {'吉': 'tl-good', '大吉': 'tl-good', '凶': 'tl-bad',
              '平': 'tl-neutral', '平偏吉': 'tl-good', '平偏凶': 'tl-bad'}
    items = []
    for dy in dayun_list:
        ji = dy.get('ji', '平')
        cls = ji_map.get(ji, 'tl-neutral')
        gz = dy.get('ganzhi', '?')
        gan, zhi = (gz[0], gz[1]) if len(gz) >= 2 else (gz, '')
        gan_color = WUXING_COLORS.get(GAN_WUXING.get(gan, ''), 'var(--text)')
        zhi_color = WUXING_COLORS_DIM.get(ZHI_WUXING.get(zhi, ''), 'var(--text-dim)')
        items.append(f'<div class="tl-item {cls}"><div class="tl-ganzhi"><span class="tl-gan" style="color:{gan_color}">{gan}</span><span class="tl-zhi" style="color:{zhi_color}">{zhi}</span></div><div class="tl-age">{dy.get("age", "?")}岁</div><div class="tl-badge">{ji}</div></div>')
    return '<div class="timeline">' + '\n'.join(items) + '</div>'


# ── v3.0: Evidence Inspector ──

def _extract_evidence(text: str) -> list[dict]:
    """从分析文本提取证据链：古籍引用 + 评分breakdown + 用神裁决"""
    evidence = []

    # E1: 古籍引用（从第〇步结果提取）
    classics = []
    for m in re.finditer(r'\|\s*\d+\s*\|\s*([\d.]+)\s*\|\s*《(.+?)》\s*\|\s*(.+?)\s*\|', text):
        classics.append({'score': float(m.group(1)), 'source': m.group(2), 'content': m.group(3)[:60]})
    if classics:
        evidence.append({
            'claim': '古籍检索',
            'confidence': 0.85,
            'classics': [f'{c["source"]}: {c["content"]}...' for c in classics[:5]],
            'rules': ['BM25 + jieba 分词', f'命中 {len(classics)} 条条文'],
            'counter': None
        })

    # E2: 格局评分
    m_score = re.search(r'(\d+)\s*/\s*100.*?(中[下上]等|上等|下等)', text)
    if m_score:
        evidence.append({
            'claim': f'格局评分 {m_score.group(1)}/100（{m_score.group(2)}）',
            'confidence': 0.82,
            'rules': ['六层格局筛查', '用神力度·相神完备·忌神受制·格局清纯·日主有根'],
        })

    # E3: 旺衰
    m_ws = re.search(r'身(旺|弱|强|中和).*?(偏强|偏弱)?', text)
    if m_ws:
        evidence.append({
            'claim': f'日主{m_ws.group(0)}',
            'confidence': 0.78,
            'rules': ['得令·得地·得势三要素量化'],
        })

    # E4: 喜用神
    m_ys = re.search(r'用神[：:]\s*(.+?)(?:[，,\n]|$)', text)
    m_xs = re.search(r'喜神[：:]\s*(.+?)(?:[，,\n]|$)', text)
    m_js = re.search(r'忌神[：:]\s*(.+?)(?:[，,\n]|$)', text)
    if m_ys:
        claim_parts = [f'用神={m_ys.group(1).strip()}']
        if m_xs: claim_parts.append(f'喜神={m_xs.group(1).strip()}')
        if m_js: claim_parts.append(f'忌神={m_js.group(1).strip()}')
        evidence.append({
            'claim': '喜用神判定: ' + ', '.join(claim_parts),
            'confidence': 0.80,
            'rules': ['四层架构（格局·病药·扶抑·调候）', '格局优先裁决'],
        })

    # E5: 大运趋势
    ji_count = len(re.findall(r'(?:吉|大吉)', text[:len(text)//2]))
    if ji_count > 0:
        evidence.append({
            'claim': f'大运趋势分析（{ji_count}+步吉运识别）',
            'confidence': 0.75,
            'rules': ['大运上限原则', '病药突破机制', '连续性忌神检测'],
        })

    return evidence


def _evidence_html(evidence: list[dict]) -> str:
    """生成可展开证据面板 HTML"""
    if not evidence:
        return ''
    cards = []
    for i, evi in enumerate(evidence):
        conf = evi.get('confidence', 0.7)
        conf_cls = 'conf-high' if conf >= 0.8 else ('conf-mid' if conf >= 0.65 else 'conf-low')
        rows = []
        rows.append(f'<div class="evi-row"><span class="evi-label">置信度</span><span class="evi-value"><span class="evi-confidence {conf_cls}">{conf:.0%}</span></span></div>')
        if evi.get('rules'):
            rows.append(f'<div class="evi-row"><span class="evi-label">规则</span><span class="evi-value">{", ".join(evi["rules"])}</span></div>')
        if evi.get('classics'):
            classic_html = ' '.join(f'<span class="evi-classic">{escape(c)}</span>' for c in evi['classics'])
            rows.append(f'<div class="evi-row"><span class="evi-label">古籍依据</span><span class="evi-value">{classic_html}</span></div>')
        if evi.get('counter'):
            rows.append(f'<div class="evi-counter">⚠️ 反证: {escape(evi["counter"])}</div>')
        cards.append(f'''<details class="evidence-card">
            <summary>🔍 {escape(evi["claim"])}</summary>
            <div class="evi-body">{''.join(rows)}</div>
        </details>''')
    return '<div class="evidence-section"><h3 style="font-size:13px;color:var(--text-dim);margin-bottom:10px;letter-spacing:2px">证据链审查</h3>' + '\n'.join(cards) + '</div>'


# ── v3.0: 刑冲合害关系图谱 ──

def _extract_relations(text: str) -> list[dict]:
    """从分析文本提取刑冲合害关系"""
    relations = []
    # 合
    for m in re.finditer(r'(\S+)合[^，,\n]*?[（(](年|月|日|时)[)）]\s*→?\s*(.+?)(?:[。，,\n]|$)', text):
        rel_type = m.group(0)
        if '冲' not in rel_type[:4]:
            relations.append({'type': '合', 'desc': m.group(0).strip()[:30]})
    # 冲
    for m in re.finditer(r'([子丑寅卯辰巳午未申酉戌亥])([子丑寅卯辰巳午未申酉戌亥])\s*冲', text):
        relations.append({'type': '冲', 'desc': m.group(0).strip()[:30]})
    # 刑
    for m in re.finditer(r'([子丑寅卯辰巳午未申酉戌亥])([子丑寅卯辰巳午未申酉戌亥])\s*刑', text):
        relations.append({'type': '刑', 'desc': m.group(0).strip()[:30]})
    # 害
    for m in re.finditer(r'([子丑寅卯辰巳午未申酉戌亥])([子丑寅卯辰巳午未申酉戌亥])\s*害', text):
        relations.append({'type': '害', 'desc': m.group(0).strip()[:30]})
    return relations[:8]


def _relation_graph_svg(pillars: list[dict], relations: list[dict]) -> str:
    """SVG 关系图谱：四柱节点 + 边"""
    if not pillars:
        return '<p style="color:var(--text-dim);text-align:center">四柱数据未提取</p>'

    # 布局：四角 + 中心日柱
    pos = {
        '年': (140, 60), '月': (340, 60),
        '日': (240, 170),  # center
        '时': (240, 280),
    }
    colors = {'合': 'var(--he-color)', '冲': 'var(--chong-color)',
              '刑': 'var(--xing-color)', '害': 'var(--hai-color)',
              '半合': 'var(--sanhe-color)', '暗合': 'var(--he-color)'}

    parts = ['<svg class="relation-graph" viewBox="0 0 480 340" xmlns="http://www.w3.org/2000/svg">']

    # Edges
    for i, rel in enumerate(relations):
        rtype = rel['type']
        # Simple: connect adjacent pillars by default
        if i < len(pos) - 1:
            keys = list(pos.keys())
            if i < len(keys) - 1:
                x1, y1 = pos[keys[i]]
                x2, y2 = pos[keys[i+1]]
                color = colors.get(rtype, 'var(--border)')
                dash = '6,3' if rtype == '冲' else ('3,3' if rtype == '害' else 'none')
                parts.append(f'<line x1="{x1}" y1="{y1+10}" x2="{x2}" y2="{y2-10}" stroke="{color}" stroke-width="2" stroke-dasharray="{dash}" opacity="0.6"/>')

    # Connect each pillar to center (日柱)
    cx, cy = 240, 170
    for key, (px, py) in pos.items():
        if key != '日':
            parts.append(f'<line x1="{px}" y1="{py}" x2="{cx}" y2="{cy}" stroke="var(--border)" stroke-width="1" opacity="0.15"/>')

    # Nodes
    for p in pillars:
        key = p['pos']
        if key in pos:
            px, py = pos[key]
            gan = p['gan']
            wx = GAN_WUXING.get(gan, '')
            color = WUXING_COLORS.get(wx, 'var(--accent)')
            _is_self = 'font-weight:800;font-size:15px' if key == '日' else ''
            parts.append(f'<circle cx="{px}" cy="{py}" r="24" fill="var(--bg-pillar)" stroke="{color}" stroke-width="2.5"/>')
            parts.append(f'<text x="{px}" y="{py-2}" text-anchor="middle" fill="{color}" font-weight="800" font-size="13">{gan}</text>')
            parts.append(f'<text x="{px}" y="{py+14}" text-anchor="middle" fill="var(--text-dim)" font-size="11">{p["zhi"]}</text>')
            parts.append(f'<text x="{px}" y="{py-32}" text-anchor="middle" fill="var(--text-dim)" font-size="10">{key}柱</text>')

    parts.append('</svg>')

    # Legend
    legend = '<div class="legend">'
    for rtype, color in [('合', 'var(--he-color)'), ('冲', 'var(--chong-color)'),
                          ('刑', 'var(--xing-color)'), ('害', 'var(--hai-color)')]:
        legend += f'<span><span class="swatch" style="background:{color};width:20px"></span>{rtype}</span>'
    legend += '</div>'

    return '\n'.join(parts) + legend


# ── Data extraction (unchanged from v2.0) ──

def extract_dashboard_data(text: str, meta: dict) -> dict:
    data = {
        'bazi': meta.get('bazi', ''), 'day_master': meta.get('day_master', ''),
        'gender': meta.get('gender', ''), 'solar_date': meta.get('solar_date', ''),
        'lunar_date': meta.get('lunar_date', ''),
        'pillars': [], 'wuxing': {}, 'geju': '', 'score': 0, 'score_label': '',
        'yongshen': '', 'xishen': '', 'jishen': '', 'dayun': [], 'qiyun_age': '',
    }
    if not data['bazi']:
        m = re.search(r'\*\*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\*\*', text)
        if m: data['bazi'] = m.group(1)
    if not data['bazi']:
        m = re.search(r'[：:]\s*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])', text)
        if m: data['bazi'] = m.group(1)
    if data['bazi']: data['bazi'] = re.sub(r'\*+', '', data['bazi'])
    if not data['bazi']: data['bazi'] = meta.get('八字', meta.get('bazi', ''))

    for m in re.finditer(r'\|\s*(年|月|日|时)\s*\|\s*([甲乙丙丁戊己庚辛壬癸])\s*\|\s*(.+?)\s*\|\s*([子丑寅卯辰巳午未申酉戌亥])\s*\|', text):
        data['pillars'].append({'pos': m.group(1), 'gan': m.group(2), 'shishen': m.group(3).strip(), 'zhi': m.group(4)})

    for m in re.finditer(r'([木火土金水])\s+[🌿🔥⛰️⚜️💧]?\s*[█░]+\s*(\d+\.?\d*)%', text):
        data['wuxing'][m.group(1)] = float(m.group(2))
    if not data['wuxing']:
        for m in re.finditer(r'\|\s*([木火土金水])\s*\|\s*(\d+\.?\d*)\s*%\s*\|', text):
            data['wuxing'][m.group(1)] = float(m.group(2))

    m = re.search(r'格局[命名]*[：:]\s*(.+?)(?:\n|$|\*\*)', text)
    if not m: m = re.search(r'\*\*格局[命名]*[：:]?\s*(.+?)\*\*', text)
    if m: data['geju'] = m.group(1).strip()

    m = re.search(r'(\d+)\s*/\s*100', text)
    if m:
        data['score'] = int(m.group(1))
        ml = re.search(r'(中[下上]等|上等|下等)', text[m.end():m.end()+50])
        if ml: data['score_label'] = ml.group(1)

    for key, pat in [('yongshen', r'(?:^|\n)\s*用神[：:]\s*(.+?)(?:[，,，\n]|$)'),
                      ('xishen', r'(?:^|\n)\s*喜神[：:]\s*(.+?)(?:[，,，\n]|$)'),
                      ('jishen', r'(?:^|\n)\s*忌神[：:]\s*(.+?)(?:[，,，\n]|$)')]:
        m = re.search(pat, text)
        if not m:
            bpat = key.replace('yongshen','用神').replace('xishen','喜神').replace('jishen','忌神')
            m = re.search(r'\|\s*\*\*' + bpat + r'\*\*\s*\|\s*(.+?)\s*\|', text)
        if m: data[key] = m.group(1).strip()

    for m in re.finditer(r'\|\s*第.+?步\s*\|\s*(\d+)[-~](\d+).*?\|\s*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s*\|.*?\|\s*(\S+)\s*\|', text):
        data['dayun'].append({'age': f'{m.group(1)}-{m.group(2)}', 'ganzhi': m.group(3), 'ji': m.group(4).strip()})
    if not data['dayun']:
        for m in re.finditer(r'\|\s*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s*\|\s*(\d+)\s*[-~]\s*(\d+).*?\|\s*(\S+)\s*\|', text):
            ji = m.group(4).strip().rstrip('⭐').strip()
            if ji in ('吉','大吉','凶','平','平偏吉','平偏凶'):
                data['dayun'].append({'age': f'{m.group(2)}-{m.group(3)}', 'ganzhi': m.group(1), 'ji': ji})
    if not data['dayun']:
        for m in re.finditer(r'\|\s*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s*\|\s*(\d+)[-~](\d+).*?\|', text):
            data['dayun'].append({'age': f'{m.group(2)}-{m.group(3)}', 'ganzhi': m.group(1), 'ji': '平'})

    m = re.search(r'起运年龄[：:]\s*(\d+)', text)
    if m: data['qiyun_age'] = m.group(1)
    return data


def generate_dashboard(meta: dict, analysis_text: str,
                       report_title: str, report_date: str,
                       md_to_html_func) -> str:
    dd = extract_dashboard_data(analysis_text, meta)

    # ── Pillars ──
    pillar_html = ''
    if dd['pillars']:
        for p in dd['pillars']:
            wx = GAN_WUXING.get(p['gan'], '')
            color = WUXING_COLORS.get(wx, 'var(--accent)')
            zhi_color = WUXING_COLORS_DIM.get(ZHI_WUXING.get(p['zhi'], ''), 'var(--text-dim)')
            pillar_html += f'<div class="pillar" style="--pillar-accent:{color};--pillar-color:{color};--pillar-zhi-color:{zhi_color}"><div class="label">{p["pos"]}柱</div><div class="gan">{p["gan"]}</div><div class="zhi">{p["zhi"]}</div><div class="shishen">{p["shishen"]}</div></div>'
    elif dd['bazi']:
        for i, pt in enumerate(dd['bazi'].split()[:4]):
            gan, zhi = pt[0], pt[1] if len(pt) > 1 else ''
            wx = GAN_WUXING.get(gan, '')
            color = WUXING_COLORS.get(wx, 'var(--accent)')
            zhi_color = WUXING_COLORS_DIM.get(ZHI_WUXING.get(zhi, ''), 'var(--text-dim)')
            pillar_html += f'<div class="pillar" style="--pillar-accent:{color};--pillar-color:{color};--pillar-zhi-color:{zhi_color}"><div class="label">{["年","月","日","时"][i]}柱</div><div class="gan">{gan}</div><div class="zhi">{zhi}</div></div>'

    # ── Charts ──
    radar_html = _draw_radar_svg(dd['wuxing']) if dd['wuxing'] else '<p style="color:var(--text-dim);text-align:center">五行数据未提取</p>'
    bars_html = _wuxing_bar_html(dd['wuxing']) if dd['wuxing'] else ''
    score_html = _score_ring_svg(dd['score']) if dd['score'] > 0 else ''
    timeline_html = _timeline_html(dd['dayun'])

    # ── v3.0: Evidence ──
    evidence = _extract_evidence(analysis_text)
    evidence_html = _evidence_html(evidence)

    # ── v3.0: Relation graph ──
    relations = _extract_relations(analysis_text)
    graph_html = _relation_graph_svg(dd['pillars'], relations)

    # ── Info rows ──
    info_rows = []
    for label, key in [('性别', 'gender'), ('阳历', 'solar_date'), ('农历', 'lunar_date'),
                        ('日主', 'day_master'), ('起运', 'qiyun_age'),
                        ('用神', 'yongshen'), ('喜神', 'xishen'), ('忌神', 'jishen')]:
        val = dd.get(key, '') or meta.get(key, '')
        if val:
            if key == 'qiyun_age': val = f'{val}岁'
            info_rows.append(f'<div class="info-row"><span class="info-label">{label}</span><span class="info-value">{escape(val)}</span></div>')

    analysis_html = md_to_html_func(analysis_text)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(report_title)}</title>
<style>{DASHBOARD_CSS}</style>
<script>
(function(){{
    var m=window.matchMedia('(prefers-color-scheme:dark)');
    var t=m.matches?'dark':'light';
    document.body.dataset.theme=t;
    var btn=document.querySelector('.theme-btn');
    if(btn)btn.textContent=t==='dark'?'☀️':'🌙';
}})();
function toggleTheme(){{
    var b=document.body;
    b.dataset.theme=b.dataset.theme==='dark'?'light':'dark';
    document.querySelector('.theme-btn').textContent=b.dataset.theme==='dark'?'☀️':'🌙';
}}
</script>
</head>
<body>

<button class="theme-btn" onclick="toggleTheme()">☀️</button>

<div class="container">

<div class="header">
    <div class="bazi">{escape(dd['bazi'] or '八字数据未提取')}</div>
    <div class="sub">{escape(report_title)} &nbsp;·&nbsp; {escape(report_date)}</div>
</div>

<div class="pillars">{pillar_html}</div>

<div class="grid">
    <div class="card" style="text-align:center">
        <h3>格局评分</h3>
        {score_html}
        <div style="margin-top:10px;font-size:19px;font-weight:800;color:var(--accent-glow)">{escape(dd['geju'] or '未提取')}</div>
        <div style="font-size:13px;color:var(--text-dim);margin-top:6px">{escape(dd['score_label'])}</div>
    </div>
    <div class="card" style="text-align:center">
        <h3>五行力量分布</h3>
        {radar_html}
    </div>
</div>

<div class="grid">
    <div class="card">
        <h3>五行占比明细</h3>
        {bars_html or '<p style="color:var(--text-dim)">五行数据未提取</p>'}
    </div>
    <div class="card">
        <h3>基本信息 &amp; 喜用神</h3>
        {''.join(info_rows)}
    </div>
</div>

<!-- v3.0: 证据链审查 -->
<div class="card full">
    {evidence_html or '<p style="color:var(--text-dim);text-align:center">证据数据未提取</p>'}
</div>

<!-- v3.0: 刑冲合害关系图谱 -->
<div class="card full" style="text-align:center">
    <h3>刑冲合害关系图谱</h3>
    {graph_html or '<p style="color:var(--text-dim)">关系数据未提取</p>'}
</div>

<div class="card full">
    <h3>大运时间轴（横向滚动）</h3>
    {timeline_html}
</div>

<div class="analysis-toggle">
    <button onclick="var c=document.getElementById('analysis');var b=this;c.classList.toggle('open');b.textContent=c.classList.contains('open')?'▲ 收起详细分析':'▶ 展开详细分析';">▶ 展开详细分析</button>
</div>
<div class="analysis-content" id="analysis">{analysis_html}</div>

<div class="footer">
    <p>{escape(report_date)} &nbsp;|&nbsp; bazi-pro v5.0 &nbsp;|&nbsp; Dashboard v5.0</p>
    <p style="margin-top:4px">仅供传统文化学习与参考，不构成任何决策依据</p>
</div>

</div>
</body>
</html>'''
