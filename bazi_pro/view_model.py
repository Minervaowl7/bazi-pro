#!/usr/bin/env python3
"""
bazi-pro ViewModel v5.0 — 共享数据层
Dashboard / Report / Replay 三种输出形态共用同一个 ViewModel
标准构建路径: result.json → build_vm_from_result_json() → DashboardVM
过渡方案: build_vm_from_analysis_text() — 已废弃
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional

# ═══════════════════════════════════════════════════════════════════
# Core data types
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PillarVM:
    """一柱命盘数据"""
    position: str          # 年/月/日/时
    gan: str               # 天干
    zhi: str               # 地支
    wuxing_gan: str = ''   # 天干五行
    wuxing_zhi: str = ''   # 地支五行
    shishen: str = ''      # 十神
    canggan: list[str] = field(default_factory=list)  # 藏干


@dataclass
class VerdictVM:
    """最终裁决"""
    day_master: str = ''           # 日主
    pattern: str = ''              # 格局名称
    decision: str = ''             # 主裁决（如"不从，按正格论"）
    yongshen: list[str] = field(default_factory=list)
    xishen: list[str] = field(default_factory=list)
    jishen: list[str] = field(default_factory=list)
    confidence: float = 0.80       # 综合置信度
    summary_line: str = ''         # 一句话摘要


@dataclass
class WuxingVM:
    """五行力量分布"""
    wood: float = 0.0
    fire: float = 0.0
    earth: float = 0.0
    metal: float = 0.0
    water: float = 0.0
    # 命理角色映射
    roles: dict[str, str] = field(default_factory=dict)
    # 每行的解读文字
    interpretations: dict[str, str] = field(default_factory=dict)


@dataclass
class EvidenceVM:
    """单条证据"""
    stage_id: str = ''
    title: str = ''                # 简短标题（≤18 字）
    claim: str = ''                # 主张
    decision: str = ''             # 裁决
    confidence: float = 0.0
    rules: list[str] = field(default_factory=list)
    classics: list[str] = field(default_factory=list)
    counter_evidence: str = ''     # 反证


@dataclass
class RelationVM:
    """刑冲合害关系"""
    relation_type: str = ''        # 冲/合/刑/害/半合/暗合/破
    from_pillar: str = ''          # 来源柱
    to_pillar: str = ''            # 目标柱
    description: str = ''          # 关系描述
    impact: str = ''               # 影响
    severity: str = '中'           # 高/中/低


@dataclass
class TraceStageVM:
    """推理链的一步"""
    stage_id: str = ''
    title: str = ''
    summary: str = ''
    status: str = 'done'
    confidence: Optional[float] = None
    rules: list[str] = field(default_factory=list)
    positive_evidence: list[str] = field(default_factory=list)
    counter_evidence: list[str] = field(default_factory=list)


@dataclass
class DayunVM:
    """大运"""
    gan_zhi: str = ''
    age_range: str = ''
    shishen: str = ''
    assessment: str = '平'         # 吉/凶/平


# ═══════════════════════════════════════════════════════════════════
# Dashboard ViewModel (主数据容器)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class DashboardVM:
    """Dashboard 视图模型 — 三种输出形态的共享数据源"""
    # Meta
    run_id: str = ''
    corpus_hash: str = ''
    bazi: str = ''
    gender: str = ''
    solar_date: str = ''
    lunar_date: str = ''
    zodiac: str = ''
    day_master: str = ''  # convenience alias, primary source is verdict.day_master

    # Core
    pillars: list[PillarVM] = field(default_factory=list)
    verdict: VerdictVM = field(default_factory=VerdictVM)
    wuxing: WuxingVM = field(default_factory=WuxingVM)

    # Evidence
    evidence: list[EvidenceVM] = field(default_factory=list)
    relations: list[RelationVM] = field(default_factory=list)

    # Timeline
    trace_stages: list[TraceStageVM] = field(default_factory=list)
    dayun: list[DayunVM] = field(default_factory=list)
    qiyun_age: str = ''

    # Score
    pattern_score: int = 0
    pattern_score_label: str = ''


# ═══════════════════════════════════════════════════════════════════
# Builders: 从 trace.json 或分析文本构建 ViewModel
# ═══════════════════════════════════════════════════════════════════

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


def build_vm_from_trace(trace: dict) -> DashboardVM:
    """从 analysis_trace.json 构建 ViewModel"""
    vm = DashboardVM()

    vm.run_id = trace.get('run_id', '')
    engine = trace.get('engine', {})
    vm.corpus_hash = engine.get('corpus_hash', '')

    inp = trace.get('input', {})
    vm.day_master = inp.get('day_master', '')
    vm.gender = inp.get('gender', '')
    vm.solar_date = inp.get('solar_date', '')
    vm.lunar_date = inp.get('lunar_date', '')
    vm.zodiac = inp.get('zodiac', '')

    # Pillars
    for p in inp.get('pillars', []):
        gan, zhi = '', ''
        if isinstance(p, str) and len(p) >= 2:
            gan, zhi = p[0], p[1]
        elif isinstance(p, dict):
            gan, zhi = p.get('gan', ''), p.get('zhi', '')
        vm.pillars.append(PillarVM(
            position=['年', '月', '日', '时'][len(vm.pillars)] if len(vm.pillars) < 4 else '',
            gan=gan, zhi=zhi,
            wuxing_gan=GAN_WUXING.get(gan, ''),
            wuxing_zhi=ZHI_WUXING.get(zhi, ''),
        ))
    vm.bazi = ' '.join(f'{p.gan}{p.zhi}' for p in vm.pillars)

    # Verdict
    summary = trace.get('summary', {})
    vm.verdict = VerdictVM(
        day_master=vm.day_master or summary.get('day_master', ''),
        pattern=summary.get('pattern', ''),
        decision=summary.get('decision', ''),
        yongshen=summary.get('yongshen', []),
        xishen=summary.get('xishen', []),
        jishen=summary.get('jishen', []),
        confidence=summary.get('confidence', 0.80),
        summary_line=summary.get('summary_line', ''),
    )

    # Wuxing
    wx = trace.get('wuxing', {})
    vm.wuxing = WuxingVM(**{k: wx.get(k, 0.0) for k in ['wood', 'fire', 'earth', 'metal', 'water']})

    # Stages → evidence + trace_stages
    for stage in trace.get('stages', []):
        vm.trace_stages.append(TraceStageVM(
            stage_id=stage.get('id', ''),
            title=stage.get('title', ''),
            summary=stage.get('summary', ''),
            status=stage.get('status', 'done'),
            confidence=stage.get('confidence'),
            rules=stage.get('rules', []),
            positive_evidence=stage.get('positive', []),
            counter_evidence=stage.get('counterfactual', []),
        ))

    # Evidence from trace
    for ev in trace.get('evidence', []):
        vm.evidence.append(EvidenceVM(
            stage_id=ev.get('id', ''),
            title=ev.get('claim', ev.get('title', '')),
            claim=ev.get('claim', ''),
            decision=ev.get('decision', ''),
            confidence=ev.get('confidence', 0.0),
            rules=ev.get('rules', []),
            classics=ev.get('classics', []),
            counter_evidence=ev.get('counter', ''),
        ))

    return vm


def build_vm_from_result_json(json_path: str) -> DashboardVM:
    """从 .artifacts/result.json 构建 ViewModel — 标准构建路径（v5.0）

    result.json 由 SKILL.md Step 10 隐式输出，包含完整的结构化分析数据。
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    vm = DashboardVM()

    # Meta
    meta = data.get('meta', {})
    vm.bazi = meta.get('bazi', '')
    vm.gender = meta.get('gender', '')
    vm.solar_date = meta.get('solar_date', '')
    vm.lunar_date = meta.get('lunar_date', '')
    vm.zodiac = meta.get('zodiac', '')
    vm.day_master = meta.get('day_master', '')
    vm.qiyun_age = str(meta.get('qiyun_age', ''))

    # Pillars
    for p in data.get('pillars', []):
        vm.pillars.append(PillarVM(
            position=p.get('position', ''),
            gan=p.get('gan', ''),
            zhi=p.get('zhi', ''),
            wuxing_gan=GAN_WUXING.get(p.get('gan', ''), ''),
            wuxing_zhi=ZHI_WUXING.get(p.get('zhi', ''), ''),
            shishen=p.get('shishen', ''),
            canggan=p.get('canggan', []),
        ))

    # Verdict
    verdict = data.get('verdict', {})
    vm.verdict = VerdictVM(
        day_master=verdict.get('day_master', vm.day_master),
        pattern=verdict.get('pattern', ''),
        decision=verdict.get('decision', ''),
        yongshen=verdict.get('yongshen', []),
        xishen=verdict.get('xishen', []),
        jishen=verdict.get('jishen', []),
        confidence=verdict.get('confidence', 0.80),
        summary_line=verdict.get('summary', ''),
    )

    # Wuxing
    wuxing = data.get('wuxing', {})
    vm.wuxing = WuxingVM(
        wood=wuxing.get('wood', 0), fire=wuxing.get('fire', 0),
        earth=wuxing.get('earth', 0), metal=wuxing.get('metal', 0),
        water=wuxing.get('water', 0),
        roles=wuxing.get('roles', {}),
        interpretations=wuxing.get('interpretations', {}),
    )

    # Pattern score
    vm.pattern_score = data.get('pattern_score', 0)
    vm.pattern_score_label = data.get('pattern_score_label', '')

    # Evidence chain
    for ev in data.get('evidence', []):
        vm.evidence.append(EvidenceVM(
            stage_id=ev.get('stage_id', ''),
            title=ev.get('title', ''),
            claim=ev.get('claim', ''),
            decision=ev.get('decision', ''),
            confidence=ev.get('confidence', 0.0),
            rules=ev.get('rules', []),
            classics=ev.get('classics', []),
            counter_evidence=ev.get('counter_evidence', ''),
        ))

    # Relations
    for r in data.get('relations', []):
        vm.relations.append(RelationVM(
            relation_type=r.get('type', ''),
            from_pillar=r.get('from', ''),
            to_pillar=r.get('to', ''),
            description=r.get('description', ''),
            impact=r.get('impact', ''),
            severity=r.get('severity', '中'),
        ))

    # Dayun
    for dy in data.get('dayun', []):
        vm.dayun.append(DayunVM(
            gan_zhi=dy.get('gan_zhi', ''),
            age_range=dy.get('age_range', ''),
            shishen=dy.get('shishen', ''),
            assessment=dy.get('assessment', '平'),
        ))

    # Trace stages
    for s in data.get('stages', []):
        vm.trace_stages.append(TraceStageVM(
            stage_id=s.get('stage_id', ''),
            title=s.get('title', ''),
            summary=s.get('summary', ''),
            status=s.get('status', 'done'),
            confidence=s.get('confidence'),
            rules=s.get('rules', []),
            positive_evidence=s.get('positive_evidence', []),
            counter_evidence=s.get('counter_evidence', []),
        ))

    return vm


def _strip_md(text: str) -> str:
    """剥离 Markdown 标记（**、*、__、` 等）"""
    import re
    # 去粗体/斜体
    text = re.sub(r'\*{1,3}([^*]+?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+?)_{1,3}', r'\1', text)
    # 去行内代码
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text.strip()


def build_vm_from_analysis_text(text: str) -> DashboardVM:
    """从分析文本（Markdown）构建 ViewModel

    .. note::
        v5.0 增强版：增加 _strip_md 清洗所有提取字段，增加大运提取，放宽五行匹配。
        保留此方法用于 generate_report.py --theme dashboard 的 VM 构建。
    """
    vm = DashboardVM()

    # Meta
    for key, pattern, target in [
        ('gender', r'\|\s*性别\s*\|\s*(.+?)\s*\|', 'gender'),
        ('solar_date', r'\|\s*阳历\s*\|\s*(.+?)\s*\|', 'solar_date'),
        ('lunar_date', r'\|\s*农历\s*\|\s*(.+?)\s*\|', 'lunar_date'),
        ('bazi', r'\|\s*八字\s*\|\s*(.+?)\s*\|', 'bazi'),
        ('day_master', r'\|\s*日主\s*\|\s*(.+?)\s*\|', 'verdict'),
        ('zodiac', r'\|\s*生肖\s*\|\s*(.+?)\s*\|', 'zodiac'),
    ]:
        m = re.search(pattern, text)
        if m:
            val = _strip_md(m.group(1).strip())
            if target == 'verdict':
                vm.verdict.day_master = val
                vm.day_master = val
            else:
                setattr(vm, target, val)

    # Qiyun age — handle **起运**：9岁 or 起运：9岁
    m = re.search(r'\*{0,2}起运(?:年龄)?\*{0,2}[：:]\s*\*{0,2}(\d+)', text)
    if m:
        vm.qiyun_age = m.group(1)

    # Pillars — 兼容两种表格格式
    for m in re.finditer(r'\|\s*(年|月|日|时)\s*\|\s*([甲乙丙丁戊己庚辛壬癸])\s*\|\s*(.+?)\s*\|\s*([子丑寅卯辰巳午未申酉戌亥])\s*\|', text):
        shishen_raw = _strip_md(m.group(3).strip())
        vm.pillars.append(PillarVM(
            position=m.group(1), gan=m.group(2),
            shishen=shishen_raw, zhi=m.group(4),
            wuxing_gan=GAN_WUXING.get(m.group(2), ''),
            wuxing_zhi=ZHI_WUXING.get(m.group(4), ''),
        ))

    # Wuxing — 放宽匹配：支持 emoji、ASCII bar、纯数字百分比
    wx_map = {'木': 'wood', '火': 'fire', '土': 'earth', '金': 'metal', '水': 'water'}
    for m in re.finditer(r'([木火土金水])\s*(?:[\U0001F300-\U0001FFFF]?\s*[█░]*\s*)?(\d+\.?\d*)\s*%', text):
        wx_key = wx_map.get(m.group(1))
        if wx_key:
            pct = float(m.group(2))
            setattr(vm.wuxing, wx_key, pct)

    # Verdict — pattern extraction (multi-strategy)
    _known_patterns = [
        '暗食神格', '暗正官格', '暗七杀格', '暗正财格', '暗偏财格',
        '从官杀格', '从强格', '从财格', '从儿格', '专旺格', '化气格',
        '正官格', '七杀格', '食神格', '伤官格', '正财格', '偏财格',
        '正印格', '偏印格', '建禄格', '月劫格', '羊刃格',
    ]
    vm.verdict.pattern = ''
    # Strategy 1: tree format — collect all layer matches, prefer deepest layer
    _layer_hits: list[tuple[int, str]] = []
    for m in re.finditer(r'[├─│]\s*层(\d)\s+(.+)', text):
        layer_num = int(m.group(1))
        candidate = _strip_md(m.group(2))
        for p in _known_patterns:
            if p in candidate:
                _layer_hits.append((layer_num, p))
                break
    if _layer_hits:
        _layer_hits.sort(key=lambda x: x[0], reverse=True)
        vm.verdict.pattern = _layer_hits[0][1]
    # Strategy 2: "实质是 **XXX格**" definitive statement
    if not vm.verdict.pattern:
        m = re.search(r'实质是\s*\*{0,2}(.+?)\*{0,2}(?:$|\n|。)', text)
        if m:
            candidate = _strip_md(m.group(1))
            for p in _known_patterns:
                if p in candidate:
                    vm.verdict.pattern = p
                    break
    # Strategy 3: fallback — "格局：" line (skip section headers)
    if not vm.verdict.pattern:
        m = re.search(r'(?:最终|综合)?格局[：:]\s*\*{0,2}(.+?)\*{0,2}(?:$|\n)', text)
        if m and '筛查' not in m.group(1) and '├' not in m.group(1):
            vm.verdict.pattern = _strip_md(m.group(1))

    # Pattern score
    m = re.search(r'(\d+)\s*/\s*100\s*[,，]?\s*(中等|中上等|中下等|上等|下等)', text)
    if m:
        vm.pattern_score = int(m.group(1))
        vm.pattern_score_label = m.group(2)

    # Decision/strength — from comprehensive judgment table
    vm.verdict.day_master = vm.verdict.day_master or vm.day_master
    m = re.search(r'\|\s*\*{0,2}综合\*{0,2}\s*\|.+?\|\s*\*{0,2}(身[旺弱]|极[旺弱])\*{0,2}\s*\|', text)
    if m:
        vm.verdict.decision = m.group(1)
    else:
        vm.verdict.decision = _strip_md(vm.verdict.decision or '')

    # Dayun extraction - cell-based parsing for varied table formats
    # Handles 5-column and 6-column tables, markdown bold, emoji markers
    dayun_header = re.search(r'大运(?:总览|逐运|排列)', text)
    if dayun_header:
        for line in text[dayun_header.start():].split('\n'):
            if not line.strip().startswith('|'):
                continue
            cells = [c.strip() for c in line.split('|')]
            cells = [c for c in cells if c]
            if len(cells) < 4:
                continue
            if not re.match(r'第[一二三四五六七八九十\d]+步|起运前', _strip_md(cells[0])):
                continue
            age_m = re.search(r'(\d+[-~]\d+)', cells[1])
            if not age_m:
                continue
            gz_m = re.search(r'([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])', cells[2])
            if not gz_m:
                continue
            raw_assess = re.sub(r'[^一-鿿]', '', _strip_md(cells[-1]))
            shishen = _strip_md(cells[3]) if len(cells) >= 5 else ''
            valid = ('大吉', '吉', '平', '凶', '大凶', '平偏吉', '平偏凶')
            vm.dayun.append(DayunVM(
                gan_zhi=gz_m.group(1),
                age_range=age_m.group(1),
                shishen=shishen,
                assessment=raw_assess if raw_assess in valid else '平',
            ))

    raw_yongshen = ''
    raw_xishen = ''
    raw_jishen = ''
    for key, pat in [('yongshen', r'用神[：:]\s*(.+?)(?:[，,\n]|$)'),
                      ('xishen', r'喜神[：:]\s*(.+?)(?:[，,\n]|$)'),
                      ('jishen', r'忌神[：:]\s*(.+?)(?:[，,\n]|$)')]:
        m = re.search(pat, text)
        if m:
            val = _strip_md(m.group(1).strip())
            if key == 'yongshen': raw_yongshen = val
            elif key == 'xishen': raw_xishen = val
            elif key == 'jishen': raw_jishen = val
            # 尝试按分隔符拆分
            items = re.split(r'[、，,]', val)
            setattr(vm.verdict, key, [x.strip() for x in items if x.strip()])

    # Text cleaning pass
    try:
        from bazi_pro.ui.text_cleaner import build_clean_verdict
        cv = build_clean_verdict(
            raw_pattern=vm.verdict.pattern,
            raw_yongshen=raw_yongshen,
            raw_xishen=raw_xishen,
            raw_jishen=raw_jishen,
            raw_decision=vm.verdict.decision,
        )
        # Only apply text_cleaner's pattern if ours isn't already a known clean name
        if cv.pattern_short and vm.verdict.pattern not in _known_patterns:
            vm.verdict.pattern = cv.pattern_short
        vm.verdict.yongshen = [cv.yongshen_label] if cv.yongshen_label else vm.verdict.yongshen
        vm.verdict.xishen = cv.xishen_labels if cv.xishen_labels else vm.verdict.xishen
        vm.verdict.jishen = cv.jishen_labels if cv.jishen_labels else vm.verdict.jishen
        vm.verdict.decision = cv.decision or vm.verdict.decision
    except ImportError:
        pass

    return vm
