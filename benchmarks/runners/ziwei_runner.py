"""MingLi-Bench 紫微斗数评测运行器

读取 MingLi-Bench 数据集 → 调用 bazi-pro 紫微排盘+LLM解盘 → 保存评测结果
"""
import json
from datetime import datetime

import requests

from benchmarks.config import API_BASE, MINGLI_DIR, RESULTS_DIR


def load_mingli_dataset(years: list[int] | None = None) -> list[dict]:
    """加载 MingLi-Bench 数据集，返回题目列表"""
    data_file = MINGLI_DIR / "data.json"
    if not data_file.exists():
        print(f"数据文件不存在: {data_file}")
        print("请先运行: python -m benchmarks download")
        return []
    raw = json.loads(data_file.read_text(encoding="utf-8"))
    questions = raw.get("questions", []) if isinstance(raw, dict) else raw
    if years:
        questions = [q for q in questions if q.get("birth_info", {}).get("year") in years]
    return questions


def load_precomputed_charts() -> dict:
    """加载预计算的紫微命盘"""
    fortune_file = MINGLI_DIR / "fortune_api_results.json"
    if not fortune_file.exists():
        return {}
    return json.loads(fortune_file.read_text(encoding="utf-8"))


def get_ziwei_chart(birth_info: dict) -> dict | None:
    """调用 bazi-pro 紫微排盘 API"""
    year = birth_info.get("year")
    month = birth_info.get("month")
    day = birth_info.get("day")
    hour = birth_info.get("hour", 0)
    if not all([year, month, day]):
        return None
    solar = f"{year}-{month:02d}-{day:02d}"
    gender = 1 if birth_info.get("gender") == "男" else 0
    try:
        r = requests.post(f"{API_BASE}/api/v2/ziwei/chart", json={
            "solar_date": solar,
            "hour": hour or 0,
            "gender": gender,
        }, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def run_ziwei(years: list[int] | None = None, max_questions: int = 0) -> dict:
    """运行紫微斗数评测"""
    questions = load_mingli_dataset(years)
    if max_questions > 0:
        questions = questions[:max_questions]
    print(f"加载 {len(questions)} 道题目")

    precomputed = load_precomputed_charts()
    print(f"预计算命盘: {len(precomputed)} 条")

    case_cache = {}
    results = []
    total = 0

    for i, q in enumerate(questions):
        qid = q.get("id", f"q_{i}")
        case_id = q.get("case_id", "")
        birth_info = q.get("birth_info", {})
        question_text = q.get("question", "")
        options = q.get("options", [])
        answer = q.get("answer", "")
        category = q.get("category", "其他")

        print(f"\n[{i+1}/{len(questions)}] {qid} [{category}]")

        chart = None
        if case_id in precomputed:
            chart = precomputed[case_id]
            print("  使用预计算命盘")
        elif case_id not in case_cache:
            chart = get_ziwei_chart(birth_info)
            if chart:
                case_cache[case_id] = chart
                print("  调用紫微排盘成功")
            else:
                print("  紫微排盘失败，跳过")
                results.append({"id": qid, "status": "chart_failed"})
                continue
        else:
            chart = case_cache[case_id]

        options_text = "\n".join(
            f"{o.get('letter', '')}. {o.get('text', '')}" for o in options
        )
        chart_str = json.dumps(chart, ensure_ascii=False)[:1500]
        prompt = (
            f"紫微命盘：{chart_str}\n\n问题：{question_text}\n\n"
            f"选项：\n{options_text}\n\n请分析命盘后选择一个答案，只需回答选项字母。"
        )

        results.append({
            "id": qid,
            "case_id": case_id,
            "category": category,
            "question": question_text,
            "expected_answer": answer,
            "prompt": prompt,
            "status": "ready",
        })
        total += 1

    output = {
        "benchmark": "ziwei",
        "timestamp": datetime.now().isoformat(),
        "total_questions": total,
        "results": results,
    }
    out_path = RESULTS_DIR / f"ziwei_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n结果已保存: {out_path}")
    print(f"共 {total} 道题目准备就绪")
    return output
