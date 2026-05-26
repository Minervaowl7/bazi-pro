#!/usr/bin/env python3
"""Agent C: SKILL.md ↔ 代码一致性审计

验证 SKILL.md (LLM合约) 中提到的功能在代码中都存在，确保合约的有效性。

用法:
  python scripts/audit_skill_consistency.py
"""

import re
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SKILL_PATH = PROJECT / "SKILL.md"
CORE_INIT = PROJECT / "bazi_pro" / "core" / "__init__.py"

ISSUES = []


def check(name: str, condition: bool, detail: str):
    if not condition:
        ISSUES.append(f"[{name}] {detail}")


def load_skill():
    if not SKILL_PATH.exists():
        return ""
    return SKILL_PATH.read_text(encoding="utf-8")


def get_exported_symbols():
    """从 core/__init__.py 的 __all__ 中提取导出符号"""
    if not CORE_INIT.exists():
        return set()
    text = CORE_INIT.read_text(encoding="utf-8")
    m = re.search(r'__all__\s*=\s*\[(.*?)\]', text, re.DOTALL)
    if not m:
        return set()
    symbols = re.findall(r"['\"](\w+)['\"]", m.group(1))
    return set(symbols)


def get_py_functions():
    """从代码中提取所有 def 定义的函数名"""
    funcs = set()
    py_files = list((PROJECT / "bazi_pro" / "core").glob("*.py"))
    py_files.append(PROJECT / "bazi_pro" / "validation.py")
    for f in py_files:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r'^def\s+(\w+)', text, re.MULTILINE):
            funcs.add(m.group(1))
    return funcs


def audit():
    skill = load_skill()
    if not skill:
        check("SKILL.md", False, "SKILL.md 不存在")
        return

    exported = get_exported_symbols()
    py_funcs = get_py_functions()

    # ── 1. SKILL.md 中提到的函数名是否都存在于代码中 ──
    skill_func_refs = set()
    for m in re.finditer(r'`(full_analysis|derive_shishen|get_canggan|calc_deling|'
                         r'calc_dedi|calc_deshi|judge_wangshuai|screen_pattern|'
                         r'derive_yongshen|detect_relations|detect_shishen_relations|'
                         r'detect_disease|calc_element_forces)\(\)`', skill):
        skill_func_refs.add(m.group(1))

    for func_name in skill_func_refs:
        check("func_exists", func_name in exported or func_name in py_funcs,
              f"SKILL.md 引用 '{func_name}()' 但代码中不存在")

    # ── 2. SKILL.md 中提到的关键字段是否与实际输出匹配 ──
    skill_mentions_fields = set()
    for m in re.finditer(r'`(core_analysis|disease|has_disease|yongshen|jishen|'
                         r'xishen|wangshuai|verdict|element_forces|percent|'
                         r'status|pillars|relations|pattern)\.?(\w*)`', skill):
        field = m.group(1)
        if field not in ('core_analysis',):
            skill_mentions_fields.add(field)

    # 对照实际输出字段
    sys.path.insert(0, str(PROJECT))
    from bazi_pro.core import full_analysis
    result = full_analysis({"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"})

    top_keys = set(result.keys())
    sub_keys = set()
    for k, v in result.items():
        if isinstance(v, dict):
            sub_keys.update(v.keys())
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            sub_keys.update(v[0].keys())

    # 检查 SKILL.md 提到的字段在实际输出中存在
    for field in skill_mentions_fields:
        check("field_exists", field in top_keys or field in sub_keys,
              f"SKILL.md 引用字段 '{field}' 但不在 full_analysis() 输出中")

    # ── 3. SKILL.md 中的步骤数是否 ≥ 10 ──
    steps = len(re.findall(r'###\s+第[一二三四五六七八九十]步', skill))
    check("steps_count", steps >= 10, f"SKILL.md 应有≥10步，实际{steps}步")

    # ── 4. SKILL.md 是否包含必需的合约标记 ──
    required_sections = [
        "算析分离", "确定性计算", "格局", "喜用神", "旺衰",
        "刑冲合害", "大运", "流年",
    ]
    for section in required_sections:
        check("section_exists", section in skill,
              f"SKILL.md 缺少'{section}'相关内容")

    # ── 5. 版本号一致性 ──
    skill_ver = re.findall(r'v(\d+\.\d+)', skill[:500])
    py_ver = re.findall(r'"(\d+\.\d+\.\d+)"', (PROJECT / "bazi_pro" / "__init__.py").read_text(encoding="utf-8"))
    if skill_ver and py_ver:
        check("version_consistency", skill_ver[0] in py_ver[0],
              f"SKILL.md v{skill_ver[0]} vs bazi_pro v{py_ver[0]} 不匹配")

    if ISSUES:
        print(f"❌ Agent C (合约一致性): {len(ISSUES)} 个问题")
        for issue in ISSUES:
            print(f"  - {issue}")
        return 1

    print("✅ Agent C (合约一致性): SKILL.md 与代码一致")
    print(f"   函数引用: {len(skill_func_refs)} 个均存在")
    print(f"   字段引用: {len(skill_mentions_fields)} 个均匹配")
    return 0


if __name__ == "__main__":
    sys.exit(audit())
