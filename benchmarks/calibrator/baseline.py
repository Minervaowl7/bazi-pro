"""基线跑分器"""
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from benchmarks.config import BAZIQA_DIR, RESULTS_DIR
from benchmarks.scoring.extractor import extract_answer, load_ground_truth
from benchmarks.scoring.stats import categorize_question


def load_dataset(years: list[int] | None = None) -> list[dict]:
    persons = []
    for f in sorted(BAZIQA_DIR.glob("*.json")):
        if years:
            file_year = None
            for y in years:
                if str(y) in f.name:
                    file_year = y
                    break
            if file_year is None and "celebrity" not in f.name:
                continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for item in data:
            if "person_id" not in item:
                continue
            persons.append(item)
    return persons


def load_latest_result() -> dict | None:
    results = sorted(RESULTS_DIR.glob("baziqa_*.json"), reverse=True)
    if not results:
        return None
    return json.loads(results[0].read_text(encoding="utf-8"))


def _extract_year(person_id: str, dataset: list[dict]) -> str:
    for person in dataset:
        if person.get("person_id") == person_id:
            for part in person_id.split("_"):
                if part.isdigit() and len(part) == 4:
                    return part
            if "celebrity" in person_id.lower():
                return "名人"
            return "未知"
    for part in person_id.split("_"):
        if part.isdigit() and len(part) == 4:
            return part
    if "celebrity" in person_id.lower():
        return "名人"
    return "未知"


def compute_baseline(
    result: dict | None = None,
    dataset: list[dict] | None = None,
) -> dict:
    if result is None:
        result = load_latest_result()
    if not result:
        print("未找到评测结果，请先运行: python -m benchmarks run baziqa")
        return {}

    if dataset is None:
        dataset = load_dataset()

    gt = load_ground_truth(dataset)

    total = 0
    correct = 0
    category_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "correct": 0})
    year_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "correct": 0})
    wrong_questions: list[dict] = []

    for person_result in result.get("results", []):
        if person_result.get("status") != "completed":
            continue
        pid = person_result["person_id"]
        answers = person_result.get("answers", {})
        year = _extract_year(pid, dataset)

        for qid, reply in answers.items():
            if qid not in gt:
                continue
            extracted = extract_answer(reply)
            expected = gt[qid]
            is_correct = extracted == expected
            total += 1
            if is_correct:
                correct += 1

            cat = categorize_question(qid, dataset)
            category_stats[cat]["total"] += 1
            if is_correct:
                category_stats[cat]["correct"] += 1

            year_stats[year]["total"] += 1
            if is_correct:
                year_stats[year]["correct"] += 1

            if not is_correct:
                question_text = ""
                for person in dataset:
                    for q in person.get("questions", []):
                        if q.get("question_id") == qid:
                            question_text = q.get("question", "")
                            break
                wrong_questions.append({
                    "question_id": qid,
                    "person_id": pid,
                    "expected": expected,
                    "extracted": extracted,
                    "question_text": question_text,
                    "category": cat,
                })

    overall_acc = correct / total if total > 0 else 0
    cat_acc = {
        cat: {
            "total": v["total"],
            "correct": v["correct"],
            "accuracy": v["correct"] / v["total"] if v["total"] > 0 else 0,
        }
        for cat, v in category_stats.items()
    }
    yr_acc = {
        yr: {
            "total": v["total"],
            "correct": v["correct"],
            "accuracy": v["correct"] / v["total"] if v["total"] > 0 else 0,
        }
        for yr, v in year_stats.items()
    }

    return {
        "overall": {"total": total, "correct": correct, "accuracy": overall_acc},
        "by_category": cat_acc,
        "by_year": yr_acc,
        "wrong_questions": wrong_questions,
    }


def generate_markdown_report(baseline: dict) -> str:
    if not baseline:
        return ""

    lines: list[str] = []
    lines.append("# BaziQA 基线评测报告\n")

    overall = baseline.get("overall", {})
    lines.append("## 总体结果\n")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 总题数 | {overall.get('total', 0)} |")
    lines.append(f"| 正确数 | {overall.get('correct', 0)} |")
    lines.append(f"| 准确率 | {overall.get('accuracy', 0):.1%} |")

    cat = baseline.get("by_category", {})
    if cat:
        lines.append("\n## 按分类统计\n")
        lines.append(f"| 分类 | 题数 | 正确 | 准确率 |")
        lines.append(f"|------|------|------|--------|")
        for name, v in sorted(cat.items(), key=lambda x: -x[1]["accuracy"]):
            lines.append(f"| {name} | {v['total']} | {v['correct']} | {v['accuracy']:.1%} |")

    yr = baseline.get("by_year", {})
    if yr:
        lines.append("\n## 按年份统计\n")
        lines.append(f"| 年份 | 题数 | 正确 | 准确率 |")
        lines.append(f"|------|------|------|--------|")
        for name, v in sorted(yr.items()):
            lines.append(f"| {name} | {v['total']} | {v['correct']} | {v['accuracy']:.1%} |")

    wrong = baseline.get("wrong_questions", [])
    if wrong:
        lines.append(f"\n## 错题列表（共 {len(wrong)} 题）\n")
        lines.append(f"| 题目ID | 命主ID | 预期 | 提取 | 分类 |")
        lines.append(f"|--------|--------|------|------|------|")
        for w in wrong:
            lines.append(
                f"| {w['question_id']} | {w['person_id']} | {w['expected']} "
                f"| {w['extracted'] or '(空)'} | {w['category']} |"
            )

    lines.append(f"\n---\n*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    return "\n".join(lines)


def save_report(baseline: dict, report_md: str) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = RESULTS_DIR / f"baseline_{timestamp}.json"
    json_path.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path = RESULTS_DIR / f"baseline_{timestamp}.md"
    md_path.write_text(report_md, encoding="utf-8")
    print(f"基线报告已保存: {json_path}")
    print(f"Markdown 报告: {md_path}")
