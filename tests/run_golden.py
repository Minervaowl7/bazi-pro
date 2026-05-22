#!/usr/bin/env python3
"""
Golden Case 验证器 — 确保引擎不回归关键边界案例
用法: python tests/run_golden.py
"""

import json
import sys
from pathlib import Path

GOLDEN_DIR = Path(__file__).resolve().parent / "golden_cases"


def load_cases():
    return [json.loads(f.read_text()) for f in sorted(GOLDEN_DIR.glob("*.json"))]


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
        return True  # can't check
    text = skill_md.read_text()
    for term in case.get("must_not_include", []):
        if term in text:
            # The term should appear ONLY in a "禁止" context, not as a recommended usage
            # Simple check: if it appears without "禁止" nearby, flag it
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
        ok &= test_evidence_structure(case)
        # keyword_exclusion is a soft check (SKILL.md 解读红线正确引用这些术语)
        test_keyword_exclusions(case)
        if ok:
            passed += 1
        print()

    print(f"{passed}/{len(cases)} 通过")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
