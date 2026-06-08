import json
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data" / "baziqa"
RESULT_FILE = Path(__file__).parent / "results" / "baziqa_ziping_20260607_181405.json"

CATEGORY_RULES = [
    ("感情", ["感情", "婚姻", "恋情", "配偶", "伴侣", "妻子", "丈夫", "结婚", "离婚", "桃花", "恋爱", "嫁", "娶"]),
    ("六亲", ["六亲", "父母", "父亲", "母亲", "兄弟", "姐妹", "子女", "亲子", "亲属", "祖辈", "家庭", "家族"]),
    ("事业", ["事业", "职业", "工作", "官运", "仕途", "升迁", "行业", "发展", "政治", "选举", "职位"]),
    ("财富", ["财富", "财运", "资产", "金钱", "经济", "发财", "投资", "理财", "收入", "富裕", "贫穷"]),
    ("健康", ["健康", "疾病", "伤", "病", "寿", "死亡", "去世", "灾", "意外", "身体", "寿元", "生命"]),
    ("格局", ["格局", "用神", "喜神", "忌神", "日主", "身旺", "身弱", "从格", "正格", "专旺", "化气"]),
    ("大运", ["大运", "流年", "运程", "运势", "运途", "运"]),
    ("性格", ["性格", "性情", "个性", "为人", "品德", "特质"]),
    ("十神", ["十神", "正官", "偏官", "七杀", "正财", "偏财", "正印", "偏印", "食神", "伤官", "比肩", "劫财"]),
    ("五行", ["五行", "金", "木", "水", "火", "土", "日干", "天干", "地支"]),
]


def classify_question(question_text: str) -> str:
    for cat, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw in question_text:
                return cat
    return "其他"


def load_all_questions():
    qid_to_info = {}
    for f in sorted(DATA_DIR.glob("*.json")):
        if f.name == ".gitkeep":
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else [data]
        for item in items:
            if "questions" not in item:
                continue
            for q in item["questions"]:
                qid = q["question_id"]
                qid_to_info[qid] = {
                    "question": q["question"],
                    "answer": q["answer"],
                    "options": q.get("options", []),
                }
    return qid_to_info


def load_results():
    data = json.loads(RESULT_FILE.read_text(encoding="utf-8"))
    qid_to_answer = {}
    for person in data["results"]:
        for qid, ans in person.get("answers", {}).items():
            qid_to_answer[qid] = ans
    return qid_to_answer, data


def main():
    questions = load_all_questions()
    model_answers, meta = load_results()

    cat_stats = defaultdict(lambda: {"total": 0, "correct": 0, "errors": []})

    for qid, info in questions.items():
        cat = classify_question(info["question"])
        gt = info["answer"]
        pred = model_answers.get(qid)
        cat_stats[cat]["total"] += 1
        if pred is None:
            cat_stats[cat]["errors"].append((qid, info["question"], gt, "MISSING"))
        elif pred.strip().upper() == gt.strip().upper():
            cat_stats[cat]["correct"] += 1
        else:
            cat_stats[cat]["errors"].append((qid, info["question"], gt, pred))

    total_q = sum(s["total"] for s in cat_stats.values())
    total_c = sum(s["correct"] for s in cat_stats.values())

    print(f"总题数: {total_q}  总正确: {total_c}  总准确率: {total_c/total_q*100:.1f}%")
    print(f"结果文件: {RESULT_FILE.name}")
    print(f"模型声称准确率: {meta['accuracy']}%  ({meta['correct']}/{meta['total_questions']})")
    print()

    header = f"{'类别':<8} {'题数':>6} {'正确':>6} {'准确率':>8} {'常见错误模式'}"
    print(header)
    print("-" * 80)

    rows = []
    for cat in sorted(cat_stats.keys(), key=lambda c: cat_stats[c]["total"], reverse=True):
        s = cat_stats[cat]
        acc = s["correct"] / s["total"] * 100 if s["total"] else 0
        rows.append((cat, s["total"], s["correct"], acc, s["errors"]))

    for cat, total, correct, acc, errors in rows:
        print(f"{cat:<8} {total:>6} {correct:>6} {acc:>7.1f}% ", end="")
        if errors:
            gt_dist = defaultdict(int)
            pred_dist = defaultdict(int)
            for _, _, gt, pred in errors:
                gt_dist[gt] += 1
                pred_dist[pred] += 1
            top_pred = sorted(pred_dist.items(), key=lambda x: -x[1])[:3]
            top_gt = sorted(gt_dist.items(), key=lambda x: -x[1])[:3]
            pred_str = ", ".join(f"答{p}({c}次)" for p, c in top_pred)
            gt_str = ", ".join(f"应{p}({c}次)" for p, c in top_gt)
            print(f"错{len(errors)}题 | {gt_str} | 模型偏好→ {pred_str}")
        else:
            print()

    print()
    print("=" * 80)
    print("各分类详细错误样例（每个分类最多显示 5 条）:")
    print("=" * 80)

    for cat, total, correct, acc, errors in rows:
        if not errors:
            continue
        print(f"\n【{cat}】错 {len(errors)} 题，准确率 {acc:.1f}%")
        for qid, qtext, gt, pred in errors[:5]:
            qtext[:50] + "..." if len(qtext) > 50 else qtext
