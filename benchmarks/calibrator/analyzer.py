"""错题分析器"""
from collections import defaultdict


_ERROR_RULES: list[tuple[str, list[str]]] = [
    ("从格误判", ["从"]),
    ("旺衰误判", ["旺", "弱", "身强", "身弱"]),
    ("格局误判", ["格", "格局"]),
    ("用神误判", ["用神", "喜神", "忌神"]),
]


def analyze_errors(baseline: dict) -> dict[str, dict]:
    wrong = baseline.get("wrong_questions", [])
    clusters: dict[str, dict] = defaultdict(lambda: {"count": 0, "questions": []})

    for w in wrong:
        q_text = w.get("question_text", "")
        matched = False
        for error_type, keywords in _ERROR_RULES:
            if any(kw in q_text for kw in keywords):
                clusters[error_type]["count"] += 1
                clusters[error_type]["questions"].append(w)
                matched = True
                break
        if not matched:
            clusters["其他"]["count"] += 1
            clusters["其他"]["questions"].append(w)

    return dict(clusters)


def print_error_report(error_clusters: dict[str, dict]) -> None:
    if not error_clusters:
        print("无错题可分析")
        return

    print("\n" + "=" * 60)
    print("  错题模式分析")
    print("=" * 60)

    total_errors = sum(c["count"] for c in error_clusters.values())
    print(f"\n  错题总数: {total_errors}")
    print(f"\n  {'错误类型':<12} {'数量':>6} {'占比':>8}")
    print(f"  {'-'*30}")

    for etype, info in sorted(error_clusters.items(), key=lambda x: -x[1]["count"]):
        ratio = info["count"] / total_errors if total_errors > 0 else 0
        print(f"  {etype:<12} {info['count']:>6} {ratio:>7.1%}")

    for etype, info in error_clusters.items():
        if not info["questions"]:
            continue
        print(f"\n  [{etype}] 典型错题:")
        shown = 0
        for q in info["questions"]:
            if shown >= 3:
                break
            print(
                f"    {q['question_id']}: {q['question_text'][:40]}..."
                if len(q.get("question_text", "")) > 40
                else f"    {q['question_id']}: {q.get('question_text', '')}"
            )
            print(f"      预期={q['expected']}  提取={q['extracted'] or '(空)'}")
            shown += 1

    print("\n" + "=" * 60)
