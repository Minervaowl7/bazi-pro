#!/usr/bin/env python3
"""
bazi-pro ViewModel v4.3 — 共享数据层
Dashboard / Report / Replay 三种输出形态共用同一个 ViewModel
从 analysis_trace.json 或分析文本加载，不依赖 Markdown 正则硬扒
"""

from dataclasses import dataclass, field
from typing import Optional
import re


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


def build_vm_from_analysis_text(text: str) -> DashboardVM:
    """从分析文本（Markdown）构建 ViewModel — 过渡方案，最终应使用 trace.json"""
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
            val = m.group(1).strip()
            if target == 'verdict':
                vm.verdict.day_master = val
            else:
                setattr(vm, target, val)

    # Pillars
    for m in re.finditer(r'\|\s*(年|月|日|时)\s*\|\s*([甲乙丙丁戊己庚辛壬癸])\s*\|\s*(.+?)\s*\|\s*([子丑寅卯辰巳午未申酉戌亥])\s*\|', text):
        vm.pillars.append(PillarVM(
            position=m.group(1), gan=m.group(2),
            shishen=m.group(3).strip(), zhi=m.group(4),
            wuxing_gan=GAN_WUXING.get(m.group(2), ''),
            wuxing_zhi=ZHI_WUXING.get(m.group(4), ''),
        ))

    # Wuxing
    for m in re.finditer(r'([木火土金水])\s+[🌿🔥⛰️⚜️💧]?\s*[█░]+\s*(\d+\.?\d*)%', text):
        pct = float(m.group(2))
        setattr(vm.wuxing, {'木': 'wood', '火': 'fire', '土': 'earth', '金': 'metal', '水': 'water'}[m.group(1)], pct)

    # Verdict
    m = re.search(r'格局命名[：:]\s*(.+?)(?:\n|$)', text)
    if m: vm.verdict.pattern = m.group(1).strip()

    m = re.search(r'(\d+)\s*/\s*100.*?(中[下上]等|上等|下等)', text)
    if m:
        vm.pattern_score = int(m.group(1))
        vm.pattern_score_label = m.group(2)

    vm.verdict.day_master = vm.verdict.day_master or vm.day_master
    vm.verdict.decision = '不从，按正格论' if '从格' in text else ''

    raw_yongshen = ''
    raw_xishen = ''
    raw_jishen = ''
    for key, pat in [('yongshen', r'用神[：:]\s*(.+?)(?:[，,\n]|$)'),
                      ('xishen', r'喜神[：:]\s*(.+?)(?:[，,\n]|$)'),
                      ('jishen', r'忌神[：:]\s*(.+?)(?:[，,\n]|$)')]:
        m = re.search(pat, text)
        if m:
            val = m.group(1).strip()
            if key == 'yongshen': raw_yongshen = val
            elif key == 'xishen': raw_xishen = val
            elif key == 'jishen': raw_jishen = val
            setattr(vm.verdict, key, [val])  # raw single-item list

    # ── v4.3.1: Text cleaning pass ──
    try:
        from bazi_pro.ui.text_cleaner import build_clean_verdict
        cv = build_clean_verdict(
            raw_pattern=vm.verdict.pattern,
            raw_yongshen=raw_yongshen,
            raw_xishen=raw_xishen,
            raw_jishen=raw_jishen,
            raw_decision=vm.verdict.decision,
        )
        vm.verdict.pattern = cv.pattern_short or vm.verdict.pattern
        vm.verdict.yongshen = [cv.yongshen_label] if cv.yongshen_label else vm.verdict.yongshen
        vm.verdict.xishen = cv.xishen_labels if cv.xishen_labels else vm.verdict.xishen
        vm.verdict.jishen = cv.jishen_labels if cv.jishen_labels else vm.verdict.jishen
        vm.verdict.decision = cv.decision or vm.verdict.decision
    except ImportError:
        pass  # text_cleaner not available, use raw

    return vm
