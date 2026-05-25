#!/usr/bin/env python3
"""格局规则交叉验证 — 对照古籍验证 PATTERN_YONGSHEN 表

从语料库中提取格局相关规则（如"正官格忌伤官"），
与代码中的 PATTERN_YONGSHEN 表交叉验证。

用法:
  python scripts/validate_pattern_rules.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bazi_pro.core.patterns import PATTERN_YONGSHEN

ISSUES = []


def check(condition: bool, detail: str):
    if not condition:
        ISSUES.append(detail)


# ── 《子平真诠》格局用神/忌神规则（手工整理） ──
# 这些是经典中明确记载的规则，用于验证 PATTERN_YONGSHEN 表
CLASSICAL_RULES = {
    '正官格': {
        '用神应含': ['财星', '印星'],
        '忌神应含': ['伤官'],
        '来源': '《子平真诠》：正官佩印，正官用财',
    },
    '七杀格': {
        '用神应含': ['食神', '印星'],
        '忌神应含': [],
        '来源': '《子平真诠》：食神制杀，杀印相生',
    },
    '正财格': {
        '用神应含': ['食伤', '官星'],
        '忌神应含': ['比劫'],
        '来源': '《子平真诠》：财格配印，财格用官',
    },
    '偏财格': {
        '用神应含': ['食伤', '官星'],
        '忌神应含': ['比劫'],
        '来源': '《子平真诠》：偏财用食伤生之',
    },
    '正印格': {
        '用神应含': ['官星'],
        '忌神应含': ['财星'],
        '来源': '《子平真诠》：印格用官，忌财坏印',
    },
    '偏印格': {
        '用神应含': ['财星'],
        '忌神应含': [],
        '来源': '《子平真诠》：偏印用财制之',
    },
    '食神格': {
        '用神应含': ['财星'],
        '忌神应含': ['偏印'],
        '来源': '《子平真诠》：食神生财，忌枭夺食',
    },
    '伤官格': {
        '用神应含': ['印星', '财星'],
        '忌神应含': [],
        '来源': '《子平真诠》：伤官佩印，伤官生财',
    },
    '建禄格': {
        '用神应含': ['官杀', '财星', '食伤'],
        '忌神应含': ['比劫'],
        '来源': '《子平真诠》：建禄月劫，无官煞则用食伤',
    },
    '月劫格': {
        '用神应含': ['官杀', '财星', '食伤'],
        '忌神应含': ['比劫'],
        '来源': '《子平真诠》：建禄月劫，无官煞则用食伤',
    },
    '羊刃格': {
        '用神应含': ['官杀'],
        '忌神应含': [],
        '来源': '《子平真诠》：羊刃用官杀制之',
    },
}


def validate_pattern_table():
    """验证 PATTERN_YONGSHEN 表与经典规则一致"""
    for pattern_name, rules in CLASSICAL_RULES.items():
        if pattern_name not in PATTERN_YONGSHEN:
            check(False, f"PATTERN_YONGSHEN 缺少格局 '{pattern_name}'")
            continue

        table_entry = PATTERN_YONGSHEN[pattern_name]
        table_yong = table_entry.get('用神', [])
        table_ji = table_entry.get('忌神', [])

        # 检查用神
        for expected in rules['用神应含']:
            found = any(expected in y or y.startswith(expected) for y in table_yong)
            check(found, f"{pattern_name}: 用神表应含'{expected}'，实际={table_yong} ({rules['来源']})")

        # 检查忌神
        for expected in rules['忌神应含']:
            found = any(expected in j or j.startswith(expected) for j in table_ji)
            check(found, f"{pattern_name}: 忌神表应含'{expected}'，实际={table_ji} ({rules['来源']})")


def validate_corpus_mentions():
    """从语料库中提取格局规则并验证"""
    from importlib.resources import files

    from bazi_pro.retrieve_classical import load_corpus

    p = str(files('bazi_pro.data').joinpath('classical_corpus.md'))
    entries = load_corpus(p)

    # 提取格局相关条目
    geju_entries = [e for e in entries if e['topic'] == '格局']

    # 检查关键规则是否在语料库中有支撑
    key_rules = [
        ('正官格', '忌伤官', '正官格忌伤官'),
        ('食神格', '忌偏印', '食神格忌偏印/枭神'),
        ('建禄', '用食伤', '建禄月劫用食伤'),
    ]

    found_count = 0
    for pattern, keyword, desc in key_rules:
        found = any(pattern in e['content'] and keyword in e['content'] for e in geju_entries)
        if not found:
            found = any(pattern in e['content'] and keyword in e['content'] for e in entries)
        if found:
            found_count += 1

    print(f"  语料库格局规则覆盖: {found_count}/{len(key_rules)} 条关键规则有古籍支撑")


def main():
    print("═══ 格局规则交叉验证 ═══")
    print()

    validate_pattern_table()
    validate_corpus_mentions()

    print()
    if ISSUES:
        print(f"❌ {len(ISSUES)} 个不一致:")
        for issue in ISSUES:
            print(f"  - {issue}")
        return 1

    print("✅ PATTERN_YONGSHEN 表与《子平真诠》规则一致")
    print(f"   验证了 {len(CLASSICAL_RULES)} 个格局的用神/忌神方向")
    return 0


if __name__ == "__main__":
    sys.exit(main())
