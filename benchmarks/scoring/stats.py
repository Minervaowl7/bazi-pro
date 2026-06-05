"""多维度统计报告"""
import json
from collections import defaultdict
from pathlib import Path

from benchmarks.config import BAZIQA_DIR, RESULTS_DIR
from benchmarks.scoring.extractor import extract_answer, load_ground_truth


CATEGORIES = ["感情", "财富", "六亲", "事业", "健康", "学业", "性格", "运势", "其他"]


def categorize_question(qid: str, dataset: list[dict]) -> str:
    """根据 question_id 找到对应的分类"""
    for person in dataset:
        cats = person.get("categories", {})
        for cat_name, qids in cats.items():
            if qid in qids:
                return cat_name
        for q in person.get("questions", []):
            if q.get("question_id") == qid:
                q_text = q.get("question", "")
                if any(k in q_text for k in ["感情", "婚姻", "恋爱", "配偶", "结婚"]):
                    return "感情"
                if any(k in q_text for k in ["财", "富", "钱", "经济"]):
                    return "财富"
                if any(k in q_text for k in ["父", "母", "兄弟", "姐妹", "子女", "六亲"]):
                    return "六亲"
                if any(k in q_text for k in ["事业", "工作", "职业", "创业"]):
                    return "事业"
                if any(k in q_text for k in ["健康", "病", "身体"]):
                    return "健康"
    return "其他"


def load_latest_result() -> dict | None:
    """加载最新的评测结果"""
    results = sorted(RESULTS_DIR.glob("baziqa_*.json"), reverse=True)
    if not results:
        return None
    return json.loads(results[0].read_text(encoding="utf-8"))


def compute_stats(result: dict | None = None, dataset_dir: Path | None = None) -> dict:
    """计算多维度统计"""
    if result is None:
        result = load_latest_result()
    if not result:
        print("未找到评测结果，请先运行: python -m benchmarks run baziqa")
        return {}

    ds_dir = dataset_dir or BAZIQA_DIR
    dataset = []
    for f in sorted(ds_dir.glob("*.json")):
        try:
            dataset.extend(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass

    gt = load_ground_truth(dataset)

    total = 0
    correct = 0
    category_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    person_stats = []

    for person_result in result.get("results", []):
        if person_result.get("status") != "completed":
            continue
        pid = person_result["person_id"]
        answers = person_result.get("answers", {})
        p_total = 0
        p_correct = 0

        for qid, reply in answers.items():
            if qid not in gt:
                continue
            extracted = extract_answer(reply)
            is_correct = extracted == gt[qid]
            total += 1
            p_total += 1
            if is_correct:
                correct += 1
                p_correct += 1

            cat = categorize_question(qid, dataset)
            category_stats[cat]["total"] += 1
            if is_correct:
                category_stats[cat]["correct"] += 1

        if p_total > 0:
            person_stats.append({
                "person_id": pid,
                "total": p_total,
                "correct": p_correct,
                "accuracy": p_correct / p_total,
            })

    overall_acc = correct / total if total > 0 else 0
    cat_acc = {cat: {
        "total": v["total"],
        "correct": v["correct"],
        "accuracy": v["correct"] / v["total"] if v["total"] > 0 else 0,
    } for cat, v in category_stats.items()}

    return {
        "overall": {"total": total, "correct": correct, "accuracy": overall_acc},
        "by_category": cat_acc,
        "by_person": person_stats,
    }


def print_stats(stats: dict):
    """打印统计报告"""
    if not stats:
        return

    overall = stats.get("overall", {})
    print("\n" + "=" * 60)
    print("  BaziQA 评测报告")
    print("=" * 60)
    print(f"\n  总题数: {overall.get('total', 0)}")
    print(f"  正确数: {overall.get('correct', 0)}")
    print(f"  准确率: {overall.get('accuracy', 0):.1%}")

    cat = stats.get("by_category", {})
    if cat:
        print(f"\n  {'维度':<8} {'题数':>6} {'正确':>6} {'准确率':>8}")
        print(f"  {'-'*32}")
        for name, v in sorted(cat.items(), key=lambda x: -x[1]["accuracy"]):
            print(f"  {name:<8} {v['total']:>6} {v['correct']:>6} {v['accuracy']:>7.1%}")

    persons = stats.get("by_person", [])
    if persons:
        accs = [p["accuracy"] for p in persons]
        print(f"\n  命主数: {len(persons)}")
        print(f"  最高准确率: {max(accs):.1%}")
        print(f"  最低准确率: {min(accs):.1%}")
        print(f"  平均准确率: {sum(accs)/len(accs):.1%}")

    print("\n" + "=" * 60)


def save_stats(stats: dict, filename: str = "baziqa_stats.json"):
    out_path = RESULTS_DIR / filename
    out_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"统计已保存: {out_path}")
