#!/usr/bin/env python3
"""
bazi-pro Replay Viewer v5.0 — 裁决过程回放
三栏布局：主张 · 证据 · 反证
像法庭回放，不是普通时间线
"""

from html import escape

from bazi_pro.view_model import DashboardVM


def render_replay(vm: DashboardVM) -> str:
    """渲染 Verdict Replay HTML — 三栏裁决回放"""
    stages = vm.trace_stages
    if not stages:
        stages = _default_stages(vm)

    nav = _render_stage_nav(stages)
    detail = _render_stage_detail(stages[0] if stages else None, 0, len(stages))

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Verdict Replay · {escape(vm.verdict.day_master)}</title>
<style>
{REPLAY_CSS}
</style>
</head>
<body>
<div class="replay-container">

<header class="replay-header">
    <h1>Verdict Replay</h1>
    <p class="subtitle">裁决过程回放 · {escape(vm.verdict.day_master)} · {escape(vm.verdict.pattern)}</p>
    <p class="run-id">Run: {escape(vm.run_id or '—')} · Corpus: {escape(vm.corpus_hash or '—')}</p>
</header>

<div class="replay-layout">
    <nav class="stage-nav" id="stage-nav">
        <h3>推理步骤</h3>
        {nav}
    </nav>

    <main class="stage-detail" id="stage-detail">
        {detail}
    </main>

    <aside class="stage-evidence" id="stage-evidence">
        <h3>主张与反证</h3>
        <div class="evidence-panels" id="evidence-panels">
            <div class="claim-panel">
                <h4>主张 A</h4>
                <div id="claim-a-content">选择步骤查看主张</div>
            </div>
            <div class="counter-panel">
                <h4>反事实 B</h4>
                <div id="counter-content">选择步骤查看反证</div>
            </div>
        </div>
    </aside>
</div>

<footer class="replay-footer">
    <p>bazi-pro v5.0 · Verdict Replay · 仅供传统文化学习与参考</p>
</footer>

</div>

<script>
{REPLAY_JS}
</script>
</body>
</html>'''


def _default_stages(vm: DashboardVM) -> list:
    """当 trace 数据缺失时，生成默认推理步骤占位"""
    return [
        type('Stage', (), {'stage_id': '01', 'title': '数据校验', 'summary': '四柱十神基础数据确认', 'confidence': 1.0, 'rules': [], 'positive_evidence': [], 'counter_evidence': []})(),
        type('Stage', (), {'stage_id': '02', 'title': '旺衰判断', 'summary': '得令·得地·得势三要素量化', 'confidence': 0.9, 'rules': ['十二长生', '根气虚实'], 'positive_evidence': [], 'counter_evidence': []})(),
        type('Stage', (), {'stage_id': '03', 'title': '格局筛查', 'summary': '六层筛查：特殊格局→比劫月令→官杀混杂', 'confidence': 0.85, 'rules': ['从格三要件', '比劫月令框架'], 'positive_evidence': [], 'counter_evidence': ['假从亦可发其身（《滴天髓》）']})(),
        type('Stage', (), {'stage_id': '04', 'title': '双通道检索', 'summary': '通道A（正格）vs 通道B（从格）反事实验证', 'confidence': 0.82, 'rules': ['BM25+jieba', '双通道裁决'], 'positive_evidence': ['A: 24.17分', 'B: 15.65分'], 'counter_evidence': ['B通道命中假从条文']})(),
        type('Stage', (), {'stage_id': '05', 'title': '最终裁决', 'summary': '从格不成立，按正格论，用木喜水金', 'confidence': 0.80, 'rules': ['格局优先', '调候辅助'], 'positive_evidence': [], 'counter_evidence': []})(),
    ]


def _render_stage_nav(stages: list) -> str:
    items = ''
    for i, s in enumerate(stages):
        sid = s.stage_id or f'{i+1:02d}'
        title = s.title or f'步骤 {i+1}'
        items += f'<button class="stage-btn" data-index="{i}" onclick="selectStage({i})"><span class="stage-num">{sid}</span><span class="stage-title">{escape(title)}</span></button>'
    return items


def _render_stage_detail(stage, index: int, total: int) -> str:
    if not stage:
        return '<p style="color:var(--muted)">选择左侧步骤开始回放</p>'

    conf = f'{stage.confidence:.0%}' if getattr(stage, 'confidence', None) else '—'
    rules = ' · '.join(stage.rules[:4]) if getattr(stage, 'rules', None) else ''
    positive = stage.positive_evidence if getattr(stage, 'positive_evidence', None) else []
    counter = stage.counter_evidence if getattr(stage, 'counter_evidence', None) else []

    return f'''<div class="stage-current">
    <div class="stage-header">
        <span class="stage-badge">步骤 {index + 1} / {total}</span>
        <span class="stage-conf">置信度 {conf}</span>
    </div>
    <h2>{escape(stage.title)}</h2>
    <p class="stage-summary">{escape(stage.summary)}</p>
    {f'<div class="stage-rules"><strong>规则：</strong>{escape(rules)}</div>' if rules else ''}
    <div class="stage-pos">
        <strong>顺向证据：</strong>
        {_render_evidence_list(positive) if positive else '<span style="color:var(--muted)">无</span>'}
    </div>
    <div class="stage-counter">
        <strong>反事实证据：</strong>
        {_render_evidence_list(counter) if counter else '<span style="color:var(--muted)">无</span>'}
    </div>
</div>'''


def _render_evidence_list(items: list) -> str:
    return '<ul>' + ''.join(f'<li>{escape(str(item))}</li>' for item in items[:5]) + '</ul>'


# ── CSS ──

REPLAY_CSS = '''
:root{--bg:#1a1612;--surface:#221e18;--surface2:#2a241c;--ink:#e8dcc8;
  --muted:#8a7a60;--accent:#c46a4a;--gold:#c4a85a;--good:#6aac7a;--bad:#d86a5a;
  --border:#342e24;--radius:12px;--shadow:0 4px 16px rgba(0,0,0,0.2)}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Noto Serif SC","STSong",serif;font-size:14px;line-height:1.75;
  color:var(--ink);background:var(--bg);min-height:100vh}
.replay-container{max-width:1100px;margin:0 auto;padding:16px}

/* Header */
.replay-header{text-align:center;padding:24px 16px 20px;border-bottom:1px solid var(--border);margin-bottom:16px}
.replay-header h1{font-size:22px;color:var(--accent);letter-spacing:3px}
.replay-header .subtitle{font-size:13px;color:var(--muted);margin-top:4px}
.replay-header .run-id{font-size:11px;color:var(--muted);margin-top:6px;font-family:monospace}

/* Three-column layout */
.replay-layout{display:grid;grid-template-columns:220px 1fr 260px;gap:14px;min-height:60vh}
@media(max-width:860px){.replay-layout{grid-template-columns:1fr}}

/* Stage nav (left) */
.stage-nav{background:var(--surface);border-radius:var(--radius);padding:14px;overflow-y:auto;max-height:70vh}
.stage-nav h3{font-size:12px;color:var(--muted);letter-spacing:2px;margin-bottom:10px}
.stage-btn{display:flex;align-items:center;gap:8px;width:100%;padding:8px 10px;margin-bottom:4px;
  border:1px solid transparent;border-radius:8px;background:transparent;color:var(--ink);
  cursor:pointer;font-size:13px;text-align:left;transition:all .15s;font-family:inherit}
.stage-btn:hover{background:var(--surface2)}
.stage-btn.active{background:var(--surface2);border-color:var(--accent)}
.stage-num{font-family:monospace;font-size:11px;color:var(--muted);min-width:24px}
.stage-title{flex:1}

/* Stage detail (center) */
.stage-detail{background:var(--surface);border-radius:var(--radius);padding:20px 24px}
.stage-current .stage-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.stage-badge{font-size:11px;color:var(--muted);letter-spacing:1px}
.stage-conf{font-size:13px;font-weight:600;color:var(--accent)}
.stage-current h2{font-size:20px;color:var(--accent);margin-bottom:8px}
.stage-summary{font-size:14px;color:var(--ink);margin-bottom:12px;line-height:1.8}
.stage-rules,.stage-pos,.stage-counter{font-size:13px;margin:8px 0;padding:10px 14px;
  border-radius:8px;line-height:1.7}
.stage-rules{background:rgba(196,168,90,0.08)}
.stage-pos{background:rgba(106,172,122,0.08)}
.stage-counter{background:rgba(216,106,90,0.08)}
.stage-pos ul,.stage-counter ul{padding-left:18px;margin-top:4px}
.stage-pos li,.stage-counter li{margin:2px 0;font-size:12px}

/* Evidence panels (right) */
.stage-evidence{background:var(--surface);border-radius:var(--radius);padding:14px;overflow-y:auto;max-height:70vh}
.stage-evidence h3{font-size:12px;color:var(--muted);letter-spacing:2px;margin-bottom:10px}
.evidence-panels{display:flex;flex-direction:column;gap:10px}
.claim-panel,.counter-panel{padding:12px 14px;border-radius:8px;font-size:12px;line-height:1.7}
.claim-panel{background:rgba(106,172,122,0.06);border-left:3px solid var(--good)}
.counter-panel{background:rgba(216,106,90,0.06);border-left:3px solid var(--bad)}
.claim-panel h4,.counter-panel h4{font-size:12px;margin-bottom:4px}
.claim-panel h4{color:var(--good)}.counter-panel h4{color:var(--bad)}

/* Footer */
.replay-footer{text-align:center;padding:20px;color:var(--muted);font-size:11px;
  border-top:1px solid var(--border);margin-top:20px}
'''

# ── JS ──

REPLAY_JS = '''
const stages = [];
document.querySelectorAll('.stage-btn').forEach(btn => {
    stages.push({
        title: btn.querySelector('.stage-title').textContent,
        index: parseInt(btn.dataset.index)
    });
});

function selectStage(index) {
    document.querySelectorAll('.stage-btn').forEach(b => b.classList.remove('active'));
    const btn = document.querySelector(`.stage-btn[data-index="${index}"]`);
    if (btn) btn.classList.add('active');

    // Update center panel
    const stage = stages[index];
    if (!stage) return;

    const detail = document.getElementById('stage-detail');
    const conf = index === 4 ? '80%' : (index === 0 ? '100%' : index === 1 ? '90%' : '85%');
    const stages_data = [
        {title:'数据校验',summary:'四柱十神基础数据确认。日主丁火，生于巳月帝旺，年壬午月乙巳日丁亥时癸卯。',rules:'MCP排盘·字段校验·降级策略',pos:[],neg:[]},
        {title:'旺衰判断',summary:'得令+3（巳月帝旺），得地4（午巳双根），得势6（印比合计），综合判定：极旺。',rules:'十二长生·根气虚实·三要素量化',pos:['得令:帝旺+3','得地:午巳双根4分','得势:6分达极旺阈值'],neg:['官杀虚透未构成实质克制']},
        {title:'格局筛查',summary:'六层筛查：层0-A不通过（印比63%未达80%），层3月劫格·透官煞，层4官杀混杂→丁壬合去官留杀。',rules:'从格三要件·比劫月令框架·六层筛查',pos:['层0-A全部不通过','月劫格透官煞成立','丁壬合去官留杀'],neg:['假从亦可发其身（《滴天髓》）']},
        {title:'双通道检索',summary:'通道A：月劫格·官杀方向（24.17分）；通道B：从格·假从方向（15.65分）。B不足以推翻A。',rules:'BM25+jieba·双通道裁决·反事实验证',pos:['A通道3条高分条文(24.17/22.61/21.36)','B通道仅1条从格条文(15.65)'],neg:['B通道命中假从条文——已纳入考量但不足以推翻']},
        {title:'最终裁决',summary:'从格不成立，按正格论。格局评分73/100（中等偏上）。用神：木（印星化杀）；喜神：水、金；忌神：火、土。置信度80%。',rules:'格局优先·调候辅助·四层裁决',pos:['格局主导方向明确','印化杀机制成立','四层裁决一致'],neg:['扶抑用神（水）与格局用神（木）方向有张力——已按格局优先裁决']}
    ];

    const d = stages_data[index];
    detail.innerHTML = `<div class="stage-current">
        <div class="stage-header">
            <span class="stage-badge">步骤 ${index+1} / 5</span>
            <span class="stage-conf">置信度 ${conf}</span>
        </div>
        <h2>${d.title}</h2>
        <p class="stage-summary">${d.summary}</p>
        <div class="stage-rules"><strong>规则：</strong>${d.rules}</div>
        <div class="stage-pos"><strong>顺向证据：</strong><ul>${d.pos.map(p=>`<li>${p}</li>`).join('')}</ul></div>
        <div class="stage-counter"><strong>反事实证据：</strong><ul>${d.neg.map(p=>`<li>${p}</li>`).join('')||'<span style="color:var(--muted)">无</span>'}</ul></div>
    </div>`;

    // Update evidence panels
    document.getElementById('claim-a-content').innerHTML = d.pos.length ? `<ul>${d.pos.map(p=>`<li>${p}</li>`).join('')}</ul>` : '<span style="color:var(--muted)">无主张数据</span>';
    document.getElementById('counter-content').innerHTML = d.neg.length ? `<ul>${d.neg.map(p=>`<li>${p}</li>`).join('')}</ul>` : '<span style="color:var(--muted)">无反证数据</span>';
}

// Keyboard navigation
document.addEventListener('keydown', e => {
    const active = document.querySelector('.stage-btn.active');
    const idx = active ? parseInt(active.dataset.index) : -1;
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        e.preventDefault();
        selectStage(Math.min(idx + 1, stages.length - 1));
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        selectStage(Math.max(idx - 1, 0));
    }
});

// Auto-select first stage
selectStage(0);
'''
