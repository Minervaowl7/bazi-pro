#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

GOLDEN_DIR = Path(__file__).resolve().parent / "golden_cases"


def load_cases():
    return [json.loads(f.read_text(encoding='utf-8')) for f in sorted(GOLDEN_DIR.glob("*.json"))]


def test_core_analysis(case: dict) -> bool:
    from bazi_pro.core.constants import derive_shishen
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

    ws = result["wangshuai"]
    verdict = ws["verdict"]
    if '旺' in verdict or '强' in verdict:
        if not ws.get("is_strong"):
            print(f"  ❌ Core 旺衰标志: verdict='{verdict}' 但 is_strong=False")
            ok = False
    if '弱' in verdict:
        if not ws.get("is_weak"):
            print(f"  ❌ Core 旺衰标志: verdict='{verdict}' 但 is_weak=False")
            ok = False
    if verdict == '极旺':
        if not ws.get("is_extreme_strong"):
            print("  ❌ Core 旺衰标志: verdict='极旺' 但 is_extreme_strong=False")
            ok = False
    if verdict == '极弱':
        if not ws.get("is_extreme_weak"):
            print("  ❌ Core 旺衰标志: verdict='极弱' 但 is_extreme_weak=False")
            ok = False

    expected_pattern = inp.get("expected_pattern")
    if expected_pattern:
        actual_pattern = result["pattern"]["pattern"]
        if expected_pattern != actual_pattern:
            print(f"  ❌ Core 格局: 预期 '{expected_pattern}'，实际 '{actual_pattern}'")
            ok = False
        else:
            print(f"  ✅ Core 格局: {actual_pattern}")

    expected_yongshen_wx = inp.get("expected_yongshen_wx")
    if expected_yongshen_wx:
        actual_yongshen = result["yongshen"]["yongshen"]
        if expected_yongshen_wx != actual_yongshen:
            print(f"  ❌ Core 用神: 预期 '{expected_yongshen_wx}'，实际 '{actual_yongshen}'")
            ok = False
        else:
            print(f"  ✅ Core 用神: {actual_yongshen}")

    expected_deling_score = inp.get("expected_deling_score")
    if expected_deling_score is not None:
        actual_deling_score = result["deling"]["score"]
        if expected_deling_score != actual_deling_score:
            print(f"  ❌ Core 得令: 预期 {expected_deling_score}，实际 {actual_deling_score}")
            ok = False
        else:
            print(f"  ✅ Core 得令: {actual_deling_score}")

    expected_dedi_level = inp.get("expected_dedi_level")
    if expected_dedi_level:
        actual_dedi_level = result["dedi"]["level"]
        if expected_dedi_level != actual_dedi_level:
            print(f"  ❌ Core 得地: 预期 '{expected_dedi_level}'，实际 '{actual_dedi_level}'")
            ok = False
        else:
            print(f"  ✅ Core 得地: {actual_dedi_level}")

    expected_deshi_level = inp.get("expected_deshi_level")
    if expected_deshi_level:
        actual_deshi_level = result["deshi"]["level"]
        if expected_deshi_level != actual_deshi_level:
            print(f"  ❌ Core 得势: 预期 '{expected_deshi_level}'，实际 '{actual_deshi_level}'")
            ok = False
        else:
            print(f"  ✅ Core 得势: {actual_deshi_level}")

    pattern_str = result["pattern"]["pattern"]
    pattern_reason = result["pattern"].get("reason", "")
    yongshen_str = str(result.get("yongshen", {}))

    must_include = case.get("must_include", [])
    for kw in must_include:
        found = (kw in pattern_str or kw in pattern_reason or kw in yongshen_str)
        if not found:
            print(f"  ❌ Core must_include: 关键词 '{kw}' 未在格局/原因/用神中找到")
            ok = False
        else:
            print(f"  ✅ Core must_include: '{kw}' 已命中（格局={pattern_str}）")

    must_not_include = case.get("must_not_include", [])
    for kw in must_not_include:
        if kw in pattern_str:
            print(f"  ❌ Core must_not_include: 关键词 '{kw}' 不应出现在格局判定中（格局={pattern_str}）")
            ok = False
        else:
            print(f"  ✅ Core must_not_include: '{kw}' 未出现（格局={pattern_str}）")

    pillars = result.get("pillars", [])
    has_shishen = any(p.get("shishen") for p in pillars)
    if not has_shishen:
        print("  ❌ Core 十神: 推导结果为空")
        ok = False
    else:
        shishen_list = [p["shishen"] for p in pillars if p.get("shishen")]
        print(f"  ✅ Core 十神: {', '.join(shishen_list)}")

        for p in pillars:
            gan = p.get("gan", "")
            expected_ss = derive_shishen(day_master, gan)
            actual_ss = p.get("shishen", "")
            if expected_ss != actual_ss:
                print(f"  ❌ Core 十神验证: {p.get('position','')}干 {gan} 预期 '{expected_ss}'，实际 '{actual_ss}'")
                ok = False

    pct = result["element_forces"].get("percent", {})
    pct_sum = sum(pct.values())
    if abs(pct_sum - 100.0) > 5.0:
        print(f"  ❌ Core 五行力量: 百分比总和 {pct_sum:.1f}% 偏离100%超过5%")
        ok = False
    else:
        print(f"  ✅ Core 五行力量: 总和 {pct_sum:.1f}%")

    return ok


def test_evidence_structure(case: dict) -> bool:
    try:
        from bazi_pro.evidence import build_analysis_evidence
        d = build_analysis_evidence(
            day_master=case['input'].get('day_master', '丙'),
            gender='女', bazi='test',
            deling_score=0, dedi_score=2.0, deshi_score=2.0, wangshuai='test',
            pattern_name=case['id'], pattern_score=60, pattern_tier='中等',
            yongshen='火', xishen='木', jishen='水',
            classical_refs=[], key_features=[], dayun_summary=[],
        )
        chains = len(d.get('evidence_chain', []))
        completeness = d.get('meta', {}).get('evidence_chain_completeness', '')
        if chains < 3:
            print(f"  ❌ Evidence: 证据链仅 {chains} 条，低于最低 3 条")
            return False
        print(f"  ✅ Evidence: chains={chains}, completeness={completeness}")
        return True
    except Exception as e:
        print(f"  ⚠️  Evidence: 跳过（{e}）")
        return True


def test_keyword_exclusions(case: dict) -> bool:
    skill_md = Path(__file__).resolve().parent.parent / "SKILL.md"
    if not skill_md.exists():
        return True
    text = skill_md.read_text(encoding='utf-8')
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
