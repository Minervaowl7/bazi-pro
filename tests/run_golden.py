#!/usr/bin/env python3
"""
Golden Case 验证器 — 确保引擎不回归关键边界案例
用法: python tests/run_golden.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

GOLDEN_DIR = Path(__file__).resolve().parent / "golden_cases"


def load_cases():
    return [json.loads(f.read_text()) for f in sorted(GOLDEN_DIR.glob("*.json"))]


def test_core_analysis(case: dict) -> bool:
    """调用 bazi_pro.core_rules.full_analysis 做确定性计算强断言验证"""
    from bazi_pro.core_rules import full_analysis

    inp = case.get("input", {})
    bazi = inp.get("bazi", "")
    day_master = inp.get("day_master", "")

    if not bazi or not day_master:
        print("  ⏭️  Core: 缺少 bazi/day_master 字段，跳过确定性计算验证")
        return True

    mcp_json = {"八字": bazi, "日主": day_master}
    result = full_analysis(mcp_json)

    if result.get("status") != "completed":
        print(f"  ❌ Core: full_analysis 返回异常状态: {result.get('status')}")
        return False

    ok = True

    expected_ws = inp.get("expected_wangshuai")
    if expected_ws:
        actual_ws = result["wangshuai"]["verdict"]
        if expected_ws != actual_ws:
            print(f"  ❌ Core 旺衰: 预期 '{expected_ws}'，实际 '{actual_ws}'")
            ok = False
        else:
            print(f"  ✅ Core 旺衰: {actual_ws}")

    pattern_str = result["pattern"]["pattern"]
    must_include = case.get("must_include", [])
    for kw in must_include:
        if kw not in pattern_str:
            found_in_ws = kw in result["wangshuai"]["verdict"]
            found_in_yongshen = kw in str(result.get("yongshen", {}))
            found_in_reason = kw in result["pattern"].get("reason", "")
            if not (found_in_ws or found_in_yongshen or found_in_reason):
                print(f"  ❌ Core 格局 must_include: 关键词 '{kw}' 未在格局/旺衰/用神结果中找到")
                ok = False
            else:
                print(f"  ✅ Core 格局 must_include: '{kw}' 已命中（格局={pattern_str}）")
        else:
            print(f"  ✅ Core 格局 must_include: '{kw}' 已命中（格局={pattern_str}）")

    must_not_include = case.get("must_not_include", [])
    for kw in must_not_include:
        if kw in pattern_str:
            print(f"  ❌ Core 格局 must_not_include: 关键词 '{kw}' 不应出现在格局判定中（格局={pattern_str}）")
            ok = False
        else:
            print(f"  ✅ Core 格局 must_not_include: '{kw}' 未出现（格局={pattern_str}）")

    pillars = result.get("pillars", [])
    has_shishen = any(p.get("shishen") for p in pillars)
    if not has_shishen:
        print("  ❌ Core 十神: 推导结果为空")
        ok = False
    else:
        shishen_list = [p["shishen"] for p in pillars if p.get("shishen")]
        print(f"  ✅ Core 十神: {', '.join(shishen_list)}")

    pct = result["element_forces"].get("percent", {})
    pct_sum = sum(pct.values())
    if abs(pct_sum - 100.0) > 5.0:
        print(f"  ❌ Core 五行力量: 百分比总和 {pct_sum:.1f}% 偏离100%超过5%")
        ok = False
    else:
        print(f"  ✅ Core 五行力量: 总和 {pct_sum:.1f}%")

    return ok


def test_retrieve_classical(case: dict) -> bool:
    """验证古籍检索是否覆盖 case 需要的经典条文"""
    import subprocess
    query = f"{case['scenario']}"[:80]
    r = subprocess.run(
        ["python3", "-m", "bazi_pro.retrieve_classical", query, "-k", "8", "--json"],
        capture_output=True, text=True, timeout=30,
        cwd=str(Path(__file__).resolve().parent.parent)
    )
    if r.returncode != 0:
        print(f"  ⚠️ 检索脚本失败: {r.stderr[:100]}")
        return False
    data = json.loads(r.stdout)
    results = data.get("queries", [{"results": data.get("results", [])}])[0].get("results", [])
    found_ids = {r["id"] for r in results}
    expected = set(case.get("classical_support", []))
    overlap = found_ids & expected
    if overlap:
        print(f"  ✅ 古籍命中: {overlap}")
        return True
    else:
        print(f"  ❌ 预期 {expected}，实际未命中（返回 {len(results)} 条）")
        return False


def test_evidence_structure(case: dict) -> bool:
    """验证 evidence.py 输出结构完整性"""
    import subprocess
    r = subprocess.run(
        ["python3", "-c",
         f"from bazi_pro.evidence import build_analysis_evidence; "
         f"d=build_analysis_evidence("
         f"day_master='{case['input'].get('day_master','丙')}', "
         f"gender='女', bazi='test', "
         f"deling_score=0, dedi_score=2.0, deshi_score=2.0, wangshuai='test', "
         f"pattern_name='{case['id']}', pattern_score=60, pattern_tier='中等', "
         f"yongshen='火', xishen='木', jishen='水', "
         f"classical_refs=[], key_features=[], dayun_summary=[]); "
         f"print('chains='+str(len(d['evidence_chain']))+', completeness='+d['meta']['evidence_chain_completeness'])"
        ],
        capture_output=True, text=True, timeout=10,
        cwd=str(Path(__file__).resolve().parent.parent)
    )
    if r.returncode == 0:
        print(f"  ✅ Evidence: {r.stdout.strip()}")
        return True
    print(f"  ❌ Evidence 失败: {r.stderr[:100]}")
    return False


def test_keyword_exclusions(case: dict) -> bool:
    """验证 SKILL.md 解读红线是否包含禁止术语"""
    skill_md = Path(__file__).resolve().parent.parent / "SKILL.md"
    if not skill_md.exists():
        return True
    text = skill_md.read_text()
    for term in case.get("must_not_include", []):
        if term in text:
            idx = text.find(term)
            context = text[max(0, idx-30):idx+len(term)+30]
            if "禁止" not in context and "不可" not in context and "严禁" not in context:
                print(f"  ⚠️  术语 '{term}' 出现在非禁止上下文: ...{context}...")
                return False
    print(f"  ✅ 禁止术语检查通过 ({len(case.get('must_not_include', []))} terms)")
    return True


def main():
    cases = load_cases()
    print(f"Golden Cases: {len(cases)} 个边界测试\n")

    passed = 0
    for case in cases:
        print(f"--- {case['id']} ---")
        print(f"  {case['description']}")
        ok = True
        ok &= test_core_analysis(case)
        ok &= test_evidence_structure(case)
        test_keyword_exclusions(case)
        if ok:
            passed += 1
        print()

    print(f"{passed}/{len(cases)} 通过")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
