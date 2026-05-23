#!/usr/bin/env python3
"""
bazi-pro Text Cleaner v5.0 — 统一输出编辑层
所有 UI 文案必经清洗：去 Markdown 残留、括号闭合、label/note 拆分
"""

import re
from dataclasses import dataclass, field


@dataclass
class CleanVerdict:
    """清洗后的裁决字段"""
    pattern_short: str = ''       # 短格局名，如 "建禄月劫 · 官杀混杂"
    pattern_detail: str = ''      # 详细说明，如 "丁壬合去官留杀，印化七杀"
    yongshen_label: str = ''      # 用神简称，如 "木"
    yongshen_note: str = ''       # 用神注释，如 "印星 · 化杀护身"
    xishen_labels: list[str] = field(default_factory=list)
    jishen_labels: list[str] = field(default_factory=list)
    decision: str = ''            # 裁决，如 "正格" / "不从"


def clean_text(raw: str) -> str:
    """清洗单条文本：去 Markdown 残留、修括号、去首尾空白"""
    if not raw:
        return ''

    # 去 Markdown 加粗/斜体/代码标记
    raw = re.sub(r'\*{1,3}', '', raw)
    raw = re.sub(r'_{1,3}', '', raw)
    raw = re.sub(r'`{1,3}', '', raw)

    # 修括号：如果左侧括号多于右侧，补闭合
    opens = raw.count('（') + raw.count('(')
    closes = raw.count('）') + raw.count(')')
    if opens > closes:
        raw += '）' * (opens - closes)

    # 过长括号解释（>10字）截断
    raw = re.sub(r'[（(]([^）)]{10,}?)[）)]', lambda m: _trim_parenthetical(m), raw)

    # 去首尾空白
    raw = raw.strip()

    return raw


def _trim_parenthetical(m) -> str:
    """截断过长括号内容，保留前 8 字 + ..."""
    inner = m.group(1)
    if len(inner) > 8:
        return f'（{inner[:8]}...）'
    return m.group(0)


def clean_pattern(raw_pattern: str) -> tuple[str, str]:
    """
    清洗格局名 → (short, detail)
    入: "建禄月劫，透官煞，丁壬合去官留杀，印化七杀"
    出: ("建禄月劫 · 官杀混杂", "丁壬合去官留杀，印化七杀")
    """
    raw = clean_text(raw_pattern)
    if not raw:
        return ('', '')

    # 已知模式映射
    patterns = [
        (r'建禄月劫.*?官[杀煞]', '建禄月劫 · 官杀混杂'),
        (r'建禄月劫.*?透官[杀煞]', '建禄月劫 · 官杀混杂'),
        (r'正官格', '正官格'),
        (r'七杀格', '七杀格'),
        (r'从强格', '从强格'),
        (r'从格', '从格'),
    ]

    short = raw[:12]  # fallback
    for pat, replacement in patterns:
        if re.search(pat, raw):
            short = replacement
            break

    # detail: 剩余的补充说明
    detail = raw
    if short in detail:
        detail = detail.replace(short, '').strip(' ·，,')
    if len(detail) > 30:
        detail = detail[:30].rstrip('，,。') + '…'

    return (short, detail)


def clean_yongshen(raw: str) -> tuple[str, str]:
    """
    清洗用神 → (label, note)
    入: "木（印星·七杀格以印化杀，出自《子平真诠》）"
    出: ("木", "印星 · 化杀护身")
    """
    raw = clean_text(raw)
    if not raw:
        return ('', '')

    # 提取五行标签（第一个字）
    label = raw[0] if raw[0] in '木火土金水' else raw[:2]

    # 提取括号内的注释
    note = ''
    m = re.search(r'[（(](.+?)[）)]', raw)
    if m:
        inner = m.group(1)
        # 简化：去古籍出处，只保留功能描述
        inner = re.sub(r'[，,]\s*出自.+$', '', inner)
        inner = re.sub(r'[，,]\s*见.+$', '', inner)
        if len(inner) > 12:
            inner = inner[:12].rstrip('，,。')
        note = inner

    # 去括号外的长文本
    label = re.sub(r'[（(].+[）)]', '', raw).strip()[:3]

    return (label, note)


def clean_xishen_jishen(raw: str) -> list[str]:
    """清洗喜神/忌神 → 五行标签列表（只从顶层逗号分段提取，忽略括号内注释）"""
    raw = clean_text(raw)
    if not raw:
        return []

    # Step 1: 移除所有括号及其内容
    cleaned = re.sub(r'[（(][^）)]*[）)]', '', raw)

    # Step 2: 按分隔符拆分成顶层段
    parts = re.split(r'[，,、]', cleaned)

    # Step 3: 每段取首个五行字符作为标签
    seen = set()
    result = []
    for part in parts:
        part = part.strip()
        m = re.match(r'^[木火土金水]', part)
        if m:
            label = m.group(0)
            if label not in seen:
                seen.add(label)
                result.append(label)

    return result[:3]


def build_clean_verdict(raw_pattern: str = '', raw_yongshen: str = '',
                        raw_xishen: str = '', raw_jishen: str = '',
                        raw_decision: str = '') -> CleanVerdict:
    """一站式构建 CleanVerdict"""
    cv = CleanVerdict()

    pat_short, pat_detail = clean_pattern(raw_pattern)
    cv.pattern_short = pat_short
    cv.pattern_detail = pat_detail

    ys_label, ys_note = clean_yongshen(raw_yongshen)
    cv.yongshen_label = ys_label
    cv.yongshen_note = ys_note

    cv.xishen_labels = clean_xishen_jishen(raw_xishen)
    cv.jishen_labels = clean_xishen_jishen(raw_jishen)

    cv.decision = clean_text(raw_decision)

    return cv
