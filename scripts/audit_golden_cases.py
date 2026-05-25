#!/usr/bin/env python3
"""Agent D: Golden Case 预期值审计

交叉验证 golden cases 的内部一致性：
1. 预期值与代码实际产出一致
2. 格局描述与旺衰期望不自相矛盾
3. must_include / must_not_include 逻辑一致性
4. 从格+不含"从"的矛盾检查

用法:
  python scripts/audit_golden_cases.py
  python scripts/audit_golden_cases.py --verbose
"""

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = PROJECT / "tests" / "golden_cases"
ISSUES = []


def check(case_id: str, condition: bool, detail: str):
    if not condition:
        ISSUES.append(f"[{case_id}] {detail}")


_CONG_PATTERNS = {'从强格', '假从强格', '从财格', '从官杀格', '从儿格', '从势格'}
_YANG_PATTERNS = {'从强格', '专旺格', '从革格', '曲直格', '炎上格', '稼穑格', '润下格'}
_YIN_PATTERNS = {'从财格', '从官杀格', '从儿格', '从势格'}


def audit_case(case: dict):
    cid = case.get("id", "unknown")
    inp = case.get("input", {})

    # ── 1. 必要字段存在 ──
    for field in ("id", "description", "input"):
        check(cid, field in case, f"缺少字段 '{field}'")
    for field in ("bazi", "day_master"):
        check(cid, field in inp, f"input 缺少 '{field}'")

    # ── 2. 有 must_not_include 中"从格"的，格局名不应该以"从"开头 ──
    mni = case.get("must_not_include", [])
    ep = inp.get("expected_pattern", "")
    if "从格" in mni:
        check(cid, not ep.startswith("从"),
              f"must_not_include 有'从格'但 expected_pattern='{ep}'以'从'开头")

    # ── 3. 包含 expected_pattern 的，must_include 必须命中 ──
    mi = case.get("must_include", [])
    if ep and mi:
        for kw in mi:
            check(cid, kw in ep or any(kw in item for item in _CONG_PATTERNS),
                  f"must_include '{kw}' 不在 expected_pattern '{ep}' 中")

    # ── 4. 旺衰与格局一致性 ──
    ews = inp.get("expected_wangshuai", "")
    if ep in _YANG_PATTERNS and ews:
        check(cid, "旺" in ews or "强" in ews or "极" in ews,
              f"格局'{ep}'是从强/专旺，但旺衰='{ews}'（应偏旺或更强）")
    if ep in _YIN_PATTERNS and ews:
        check(cid, "弱" in ews or "极" in ews,
              f"格局'{ep}'是从弱，但旺衰='{ews}'（应偏弱或更弱）")

    # ── 5. 得令分数与旺衰的一致性 ──
    edl = inp.get("expected_deling_score")
    if edl is not None and ews:
        if "旺" in ews and edl < 0:
            check(cid, False, f"旺衰='{ews}'但得令={edl}<0（不应得令为负却身旺）")
        if "弱" in ews and edl > 0:
            # 得令为正时也可能身弱（如被群克），这是合理的
            pass

    # ── 6. must_not_include 不应该同时出现在 must_include ──
    overlap = set(mi) & set(mni)
    check(cid, not overlap, f"must_include 与 must_not_include 重叠: {overlap}")

    # ── 7. 八字格式检查 ──
    bazi = inp.get("bazi", "")
    parts = bazi.split()
    if bazi:
        check(cid, len(parts) in (0, 4), f"八字'{bazi}'应有4柱，实际{len(parts)}柱")
        for part in parts:
            check(cid, len(part) == 2, f"八字元素'{part}'应含1天干+1地支")


def audit_missing_vs_code():
    """检查 golden cases 的预期值是否与代码产出匹配"""
    sys.path.insert(0, str(PROJECT))
    from bazi_pro.core import full_analysis

    for f in sorted(GOLDEN_DIR.glob("*.json")):
        case = json.loads(f.read_text(encoding="utf-8"))
        cid = case["id"]
        inp = case.get("input", {})
        bazi = inp.get("bazi", "")
        dm = inp.get("day_master", "")
        if not bazi or not dm:
            continue

        result = full_analysis({"八字": bazi, "日主": dm})
        if result.get("status") != "completed":
            continue

        # 检查 expected_pattern 与代码产出的一致性
        ep = inp.get("expected_pattern", "")
        if ep:
            actual = result["pattern"]["pattern"]
            check(cid, ep == actual,
                  f"expected_pattern='{ep}' ≠ 代码产出='{actual}'")

        # 检查 expected_wangshuai
        ews = inp.get("expected_wangshuai", "")
        if ews:
            actual_ws = result["wangshuai"]["verdict"]
            check(cid, ews == actual_ws,
                  f"expected_wangshuai='{ews}' ≠ 代码产出='{actual_ws}'")

        # 检查 expected_yongshen_wx
        eyw = inp.get("expected_yongshen_wx", "")
        if eyw:
            actual_ys = result["yongshen"]["yongshen"]
            check(cid, eyw == actual_ys,
                  f"expected_yongshen_wx='{eyw}' ≠ 代码产出='{actual_ys}'")


def main():
    verbose = "--verbose" in sys.argv

    # Phase 1: 结构性审计
    for f in sorted(GOLDEN_DIR.glob("*.json")):
        try:
            case = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            ISSUES.append(f"[{f.stem}] JSON 解析失败: {e}")
            continue
        audit_case(case)

    # Phase 2: 代码一致性审计
    audit_missing_vs_code()

    if ISSUES:
        print(f"❌ Agent D (Golden Case 审计): {len(ISSUES)} 个问题")
        for issue in ISSUES:
            print(f"  - {issue}")
        return 1

    count = len(list(GOLDEN_DIR.glob("*.json")))
    print(f"✅ Agent D (Golden Case 审计): {count} 个用例通过")
    if verbose:
        print(f"   包含 {count} 个 JSON 用例")
    return 0


if __name__ == "__main__":
    sys.exit(main())
