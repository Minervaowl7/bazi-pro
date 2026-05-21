#!/usr/bin/env python3
"""
八字命理仪表盘生成器 — 交互式 HTML 主题
零外部依赖，纯 HTML+CSS+SVG，暗色/亮色切换，雷达图 + 时间轴。
"""

import re
import math
from html import escape


DASHBOARD_CSS = r'''
:root {
    --bg: #0f0f14; --bg-card: #1a1a24; --bg-pillar: #1e1e2e;
    --text: #e0d8c8; --text-dim: #8888a0; --accent: #c9a96e;
    --accent-glow: #f0d080; --fire: #e06040; --wood: #60b860;
    --earth: #c8a040; --metal: #d0d0c0; --water: #5088d0;
    --good: #60b878; --warn: #d0a040; --bad: #c05050;
    --border: #2a2a3a; --shadow: 0 2px 16px rgba(0,0,0,0.4);
    --radius: 8px;
}
[data-theme="light"] {
    --bg: #f5f0e8; --bg-card: #fffdf7; --bg-pillar: #fdf5e6;
    --text: #2c1810; --text-dim: #998870; --accent: #8b2500;
    --accent-glow: #a0522d; --border: #e8d5c4;
    --shadow: 0 2px 16px rgba(44,24,16,0.1);
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Noto Serif CJK SC","Microsoft YaHei",serif;background:var(--bg);color:var(--text);min-height:100vh;line-height:1.7}
a{color:var(--accent)}
.container{max-width:900px;margin:0 auto;padding:16px}

.header{text-align:center;padding:36px 16px 20px}
.header .bazi{font-size:32px;font-weight:700;letter-spacing:6px;color:var(--accent-glow);margin-bottom:6px}
.header .sub{font-size:14px;color:var(--text-dim)}

.theme-btn{position:fixed;top:12px;right:16px;z-index:99;
    background:var(--bg-card);border:1px solid var(--border);
    color:var(--text);padding:8px 14px;border-radius:20px;
    cursor:pointer;font-size:16px;transition:all .2s}
.theme-btn:hover{box-shadow:var(--shadow)}

.pillars{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:16px 0 20px}
.pillar{background:var(--bg-pillar);border:1px solid var(--border);
    border-radius:var(--radius);padding:14px 10px;text-align:center}
.pillar .gan{font-size:36px;font-weight:700;line-height:1.1}
.pillar .zhi{font-size:20px;color:var(--text-dim);margin:2px 0}
.pillar .label{font-size:11px;color:var(--text-dim);text-transform:uppercase;letter-spacing:1px}
.pillar .shishen{font-size:13px;margin-top:6px;padding:2px 8px;border-radius:10px;display:inline-block;
    background:var(--border);color:var(--accent)}

.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:14px 0}
@media(max-width:600px){.grid{grid-template-columns:1fr}.pillars{grid-template-columns:repeat(2,1fr)}}
.card{background:var(--bg-card);border:1px solid var(--border);
    border-radius:var(--radius);padding:18px;box-shadow:var(--shadow)}
.card h3{font-size:14px;color:var(--text-dim);margin-bottom:10px;letter-spacing:1px}
.card.full{grid-column:1/-1}

.radar-svg{width:100%;max-width:360px;margin:0 auto;display:block}
.radar-label{font-size:11px;fill:var(--text-dim);text-anchor:middle}

.timeline{display:flex;overflow-x:auto;gap:6px;padding:8px 0;scrollbar-width:thin}
.timeline::-webkit-scrollbar{height:4px}
.timeline::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.tl-item{flex:0 0 auto;min-width:80px;text-align:center;padding:8px 6px;border-radius:var(--radius);
    background:var(--bg-pillar);border:1px solid var(--border);cursor:default;transition:all .2s}
.tl-item:hover{transform:translateY(-2px);box-shadow:var(--shadow)}
.tl-item .tl-ganzhi{font-size:16px;font-weight:600}
.tl-item .tl-age{font-size:11px;color:var(--text-dim);margin-top:2px}
.tl-item .tl-badge{font-size:10px;padding:1px 6px;border-radius:8px;margin-top:4px;display:inline-block}
.tl-good{border-color:var(--good)}.tl-good .tl-badge{background:#1a3a1a;color:var(--good)}
.tl-warn{border-color:var(--warn)}.tl-warn .tl-badge{background:#3a2a0a;color:var(--warn)}
.tl-bad{border-color:var(--bad)}.tl-bad .tl-badge{background:#3a0a0a;color:var(--bad)}
.tl-neutral{border-color:var(--border)}

.info-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:14px}
.info-row:last-child{border-bottom:none}
.info-label{color:var(--text-dim)}
.info-value{font-weight:600;color:var(--accent)}

.score-ring{width:80px;height:80px;margin:0 auto}
.score-ring circle{fill:none;stroke-width:6}
.score-ring .bg{stroke:var(--border)}
.score-ring .fg{stroke:var(--accent);stroke-linecap:round;transform:rotate(-90deg);transform-origin:50% 50%}
.score-text{font-size:22px;font-weight:700;fill:var(--accent);text-anchor:middle;dominant-baseline:central}

.analysis-toggle{text-align:center;margin:20px 0}
.analysis-toggle button{background:var(--bg-card);border:1px solid var(--border);
    color:var(--accent);padding:10px 28px;border-radius:20px;cursor:pointer;font-size:15px}
.analysis-toggle button:hover{box-shadow:var(--shadow)}
.analysis-content{max-height:0;overflow:hidden;transition:max-height .5s}
.analysis-content.open{max-height:none}

.analysis-content h1,.analysis-content h2,.analysis-content h3{color:var(--accent);margin:16px 0 8px}
.analysis-content table{width:100%;border-collapse:collapse;font-size:13px;margin:10px 0}
.analysis-content table th{background:var(--bg-pillar);padding:6px 8px;border:1px solid var(--border)}
.analysis-content table td{padding:6px 8px;border:1px solid var(--border);text-align:center}
.analysis-content pre{background:#151520;color:#a0d468;padding:12px;border-radius:var(--radius);overflow-x:auto;font-size:12px}
.analysis-content blockquote{border-left:3px solid var(--accent);padding:8px 16px;margin:10px 0;background:var(--bg-pillar);border-radius:0 var(--radius) var(--radius) 0}
.analysis-content hr{border:none;border-top:1px solid var(--border);margin:20px 0}
.analysis-content ul,.analysis-content ol{padding-left:20px;margin:8px 0}
.analysis-content li{margin:4px 0}

.footer{text-align:center;padding:24px;color:var(--text-dim);font-size:11px;border-top:1px solid var(--border);margin-top:24px}
'''


def _draw_radar_svg(wuxing: dict) -> str:
    """Generate SVG radar chart for 五行 distribution."""
    labels = ['木', '火', '土', '金', '水']
    values = [wuxing.get(k, 0) for k in labels]
    cx, cy, r = 180, 180, 140

    parts = [f'<svg class="radar-svg" viewBox="0 0 360 360" xmlns="http://www.w3.org/2000/svg">']

    for level in range(1, 6):
        lr = r * level / 5
        pts = []
        for i in range(5):
            angle = -math.pi / 2 + i * 2 * math.pi / 5
            x = cx + lr * math.cos(angle)
            y = cy + lr * math.sin(angle)
            pts.append(f'{x:.1f},{y:.1f}')
        parts.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="var(--border)" stroke-width="1" opacity="0.5"/>')

    for i in range(5):
        angle = -math.pi / 2 + i * 2 * math.pi / 5
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="var(--border)" stroke-width="1" opacity="0.3"/>')

    data_pts = []
    for i in range(5):
        angle = -math.pi / 2 + i * 2 * math.pi / 5
        val = min(values[i], 100) / 100.0
        dx = cx + r * val * math.cos(angle)
        dy = cy + r * val * math.sin(angle)
        data_pts.append(f'{dx:.1f},{dy:.1f}')
    parts.append(f'<polygon points="{" ".join(data_pts)}" fill="var(--accent)" fill-opacity="0.25" stroke="var(--accent-glow)" stroke-width="2"/>')
    for pt in data_pts:
        x, y = pt.split(',')
        parts.append(f'<circle cx="{x}" cy="{y}" r="3" fill="var(--accent-glow)"/>')

    for i in range(5):
        angle = -math.pi / 2 + i * 2 * math.pi / 5
        lx = cx + (r + 28) * math.cos(angle)
        ly = cy + (r + 28) * math.sin(angle)
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" class="radar-label" font-size="14" font-weight="700">{labels[i]}</text>')
        plx = cx + (r + 44) * math.cos(angle)
        ply = cy + (r + 44) * math.sin(angle)
        parts.append(f'<text x="{plx:.1f}" y="{ply:.1f}" class="radar-label" font-size="11">{values[i]:.1f}%</text>')

    parts.append('</svg>')
    return '\n'.join(parts)


def _score_ring_svg(score: int, max_score: int = 100) -> str:
    pct = score / max_score
    circumference = 2 * math.pi * 32
    dash = pct * circumference
    return f'''<svg class="score-ring" viewBox="0 0 80 80">
    <circle class="bg" cx="40" cy="40" r="32"/>
    <circle class="fg" cx="40" cy="40" r="32" stroke-dasharray="{dash:.1f} {circumference:.1f}"/>
    <text class="score-text" x="40" y="40">{score}</text>
</svg>'''


def _timeline_html(dayun_list: list) -> str:
    if not dayun_list:
        return '<p style="color:var(--text-dim)">大运数据未提取</p>'
    ji_map = {'吉': 'tl-good', '大吉': 'tl-good', '凶': 'tl-bad',
              '平': 'tl-neutral', '平偏吉': 'tl-good', '平偏凶': 'tl-bad'}
    items = []
    for dy in dayun_list:
        ji = dy.get('ji', '平')
        cls = ji_map.get(ji, 'tl-neutral')
        items.append(f'''<div class="tl-item {cls}">
            <div class="tl-ganzhi">{dy.get('ganzhi', '?')}</div>
            <div class="tl-age">{dy.get('age', '?')}</div>
            <div class="tl-badge">{ji}</div>
        </div>''')
    return '<div class="timeline">' + '\n'.join(items) + '</div>'


def extract_dashboard_data(text: str, meta: dict) -> dict:
    data = {
        'bazi': meta.get('bazi', ''),
        'day_master': meta.get('day_master', ''),
        'gender': meta.get('gender', ''),
        'solar_date': meta.get('solar_date', ''),
        'lunar_date': meta.get('lunar_date', ''),
        'pillars': [],
        'wuxing': {},
        'geju': '',
        'score': 0,
        'score_label': '',
        'yongshen': '',
        'xishen': '',
        'jishen': '',
        'dayun': [],
        'qiyun_age': '',
    }

    if not data['bazi']:
        m = re.search(r'\*\*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\*\*', text)
        if m:
            data['bazi'] = m.group(1)

    # Pillars from step 1 table
    for m in re.finditer(
        r'\|\s*(年|月|日|时)\s*\|\s*([甲乙丙丁戊己庚辛壬癸])\s*\|\s*(.+?)\s*\|\s*([子丑寅卯辰巳午未申酉戌亥])\s*\|',
        text
    ):
        data['pillars'].append({'pos': m.group(1), 'gan': m.group(2),
                                'shishen': m.group(3).strip(), 'zhi': m.group(4)})

    # Wuxing percentages
    for m in re.finditer(r'([木火土金水])\s+[🌿🔥⛰️⚜️💧]?\s*█+.*?(\d+\.?\d*)%', text):
        data['wuxing'][m.group(1)] = float(m.group(2))

    # Geju
    m = re.search(r'格局命名[：:]\s*(.+?)(?:\n|$)', text)
    if m:
        data['geju'] = m.group(1).strip()

    # Score
    m = re.search(r'(\d+)/100.*?(中[下上]等|上等|下等)', text)
    if m:
        data['score'] = int(m.group(1))
        data['score_label'] = m.group(2)

    # Yongshen / Xishen / Jishen
    for key, pat in [('yongshen', r'用神[：:]\s*(.+?)(?:[，,\n]|$)'),
                      ('xishen', r'喜神[：:]\s*(.+?)(?:[，,\n]|$)'),
                      ('jishen', r'忌神[：:]\s*(.+?)(?:[，,\n]|$)')]:
        m = re.search(pat, text)
        if m:
            data[key] = m.group(1).strip()

    # Dayun
    for m in re.finditer(
        r'\|\s*第.+?步\s*\|\s*(\d+)[-~](\d+).*?\|\s*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s*\|.*?\|\s*(\S+)\s*\|',
        text
    ):
        data['dayun'].append({'age': f'{m.group(1)}-{m.group(2)}',
                              'ganzhi': m.group(3), 'ji': m.group(4).strip()})
    if not data['dayun']:
        for m in re.finditer(
            r'\|\s*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s*\|\s*(\d+)[-~](\d+).*?\|',
            text
        ):
            data['dayun'].append({'age': f'{m.group(2)}-{m.group(3)}',
                                  'ganzhi': m.group(1), 'ji': '平'})

    # Qiyun age
    m = re.search(r'起运年龄[：:]\s*(\d+)', text)
    if m:
        data['qiyun_age'] = m.group(1)

    return data


def generate_dashboard(meta: dict, analysis_text: str,
                       report_title: str, report_date: str,
                       md_to_html_func) -> str:
    """Generate interactive dashboard HTML."""
    dd = extract_dashboard_data(analysis_text, meta)

    # Pillar cards
    pillar_html = ''
    if dd['pillars']:
        for p in dd['pillars']:
            pillar_html += f'''<div class="pillar">
                <div class="label">{p['pos']}柱</div>
                <div class="gan">{p['gan']}</div>
                <div class="zhi">{p['zhi']}</div>
                <div class="shishen">{p['shishen']}</div>
            </div>'''
    elif dd['bazi']:
        labels = ['年', '月', '日', '时']
        for i, pt in enumerate(dd['bazi'].split()[:4]):
            gan, zhi = pt[0], pt[1] if len(pt) > 1 else ''
            pillar_html += f'''<div class="pillar">
                <div class="label">{labels[i]}柱</div>
                <div class="gan">{gan}</div>
                <div class="zhi">{zhi}</div>
            </div>'''

    # Radar
    radar_html = _draw_radar_svg(dd['wuxing']) if dd['wuxing'] else \
        '<p style="color:var(--text-dim);text-align:center">五行数据未提取</p>'

    # Score ring
    score_html = _score_ring_svg(dd['score']) if dd['score'] > 0 else ''

    # Timeline
    timeline_html = _timeline_html(dd['dayun'])

    # Info rows
    info_rows = []
    for label, key in [('性别', 'gender'), ('阳历', 'solar_date'), ('农历', 'lunar_date'),
                        ('日主', 'day_master'), ('起运', 'qiyun_age'),
                        ('用神', 'yongshen'), ('喜神', 'xishen'), ('忌神', 'jishen')]:
        val = dd.get(key, '') or meta.get(key, '')
        if val:
            if key == 'qiyun_age':
                val = f'{val}岁'
            info_rows.append(f'<div class="info-row"><span class="info-label">{label}</span><span class="info-value">{escape(val)}</span></div>')

    # Convert analysis to HTML for collapsible section
    analysis_html = md_to_html_func(analysis_text)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(report_title)}</title>
<style>{DASHBOARD_CSS}</style>
</head>
<body data-theme="dark">

<button class="theme-btn" onclick="
    var b=document.body;
    b.dataset.theme=b.dataset.theme==='dark'?'light':'dark';
    this.textContent=b.dataset.theme==='dark'?'☀️':'🌙';
">☀️</button>

<div class="container">

<div class="header">
    <div class="bazi">{escape(dd['bazi'] or '八字数据未提取')}</div>
    <div class="sub">{escape(report_title)} &nbsp;·&nbsp; {escape(report_date)}</div>
</div>

<div class="pillars">
    {pillar_html}
</div>

<div class="grid">
    <div class="card" style="text-align:center">
        <h3>格局评分</h3>
        {score_html}
        <div style="margin-top:8px;font-size:18px;font-weight:700;color:var(--accent)">{escape(dd['geju'] or '未提取')}</div>
        <div style="font-size:13px;color:var(--text-dim);margin-top:4px">{escape(dd['score_label'])}</div>
    </div>
    <div class="card" style="text-align:center">
        <h3>五行力量分布</h3>
        {radar_html}
    </div>
</div>

<div class="card full">
    <h3>基本信息 &amp; 喜用神</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 20px">
        {''.join(info_rows)}
    </div>
</div>

<div class="card full">
    <h3>大运时间轴（横向滚动）</h3>
    {timeline_html}
</div>

<div class="analysis-toggle">
    <button onclick="
        var c=document.getElementById('analysis');
        var b=this;
        c.classList.toggle('open');
        b.textContent=c.classList.contains('open')?'▲ 收起详细分析':'▶ 展开详细分析';
    ">▶ 展开详细分析</button>
</div>
<div class="analysis-content" id="analysis">
    {analysis_html}
</div>

<div class="footer">
    <p>{escape(report_date)} &nbsp;|&nbsp; bazi-pro v3.5 &nbsp;|&nbsp; Dashboard Theme</p>
    <p style="margin-top:4px">仅供传统文化学习与参考，不构成任何决策依据</p>
</div>

</div>
</body>
</html>'''
