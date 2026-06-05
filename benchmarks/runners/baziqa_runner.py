"""BaziQA 评测运行器

读取 BaziQA 数据集 → 调用 bazi-pro 排盘+LLM解盘 → 保存评测结果
"""
import json
import time
from datetime import datetime

import requests

from benchmarks.config import API_BASE, BAZIQA_DIR, RESULTS_DIR


def load_baziqa_dataset(years: list[int] | None = None) -> list[dict]:
    """加载 BaziQA 数据集，返回所有命主列表

    Args:
        years: 比赛年份过滤（如 [2025] 只加载 contest8_2025.json），
               None 表示加载全部（含 celebrity50）
    """
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


def paipan(birth: dict, gender: str) -> dict | None:
    """调用 bazi-pro 排盘 API"""
    year = birth.get("year")
    month = birth.get("month")
    day = birth.get("day")
    hour = birth.get("hour")
    if not all([year, month, day]):
        return None
    solar = f"{year}-{month:02d}-{day:02d}"
    if hour is not None:
        solar += f" {hour:02d}:00"
    try:
        r = requests.post(f"{API_BASE}/api/v2/paipan", json={"阳历": solar, "性别": gender}, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def analyze(bazi_data: dict, school: str = "ziping") -> str | None:
    """调用 bazi-pro 分析 API，返回 analysis_id"""
    payload = {
        "八字": bazi_data.get("八字", ""),
        "日主": bazi_data.get("日主", ""),
        "性别": bazi_data.get("性别", "男"),
        "阳历": bazi_data.get("阳历", ""),
        "生肖": bazi_data.get("生肖", ""),
        "school": school,
    }
    try:
        r = requests.post(f"{API_BASE}/api/v2/analyze", json=payload, timeout=10)
        if r.status_code == 202:
            return r.json().get("analysis_id")
    except Exception:
        pass
    return None


def poll_result(analysis_id: str, timeout: int = 60) -> dict | None:
    """轮询分析结果"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{API_BASE}/api/v2/analysis/{analysis_id}", timeout=10)
            data = r.json()
            if data.get("status") == "completed":
                return data.get("result", {})
            if data.get("status") == "failed":
                return None
        except Exception:
            pass
        time.sleep(2)
    return None


def ask_question(analysis_id: str, question: str, school: str = "ziping") -> str:
    """向 bazi-pro 提问，获取 LLM 回答"""
    try:
        r = requests.post(f"{API_BASE}/api/v2/chat", json={
            "analysis_id": analysis_id,
            "message": question,
            "school": school,
        }, timeout=120)
        if r.status_code == 200:
            return r.json().get("reply", "")
    except Exception as e:
        return f"[ERROR] {e}"
    return ""


def run_baziqa(years: list[int] | None = None, max_persons: int = 0, school: str = "ziping") -> dict:
    """运行 BaziQA 评测"""
    persons = load_baziqa_dataset(years)
    if max_persons > 0:
        persons = persons[:max_persons]
    print(f"加载 {len(persons)} 个命主")

    results = []
    total_q = 0
    for i, person in enumerate(persons):
        pid = person["person_id"]
        profile = person.get("profile", {})
        birth = profile.get("birth", {})
        gender = "男" if profile.get("gender") == "male" else "女"
        questions = person.get("questions", [])
        if not questions:
            continue

        print(f"\n[{i+1}/{len(persons)}] {pid} ({birth.get('year')}年{gender})")

        bazi_data = paipan(birth, gender)
        if not bazi_data:
            print("  排盘失败，跳过")
            results.append({"person_id": pid, "status": "paipan_failed", "answers": {}})
            continue

        analysis_id = analyze(bazi_data, school)
        if not analysis_id:
            print("  分析提交失败，跳过")
            results.append({"person_id": pid, "status": "analyze_failed", "answers": {}})
            continue

        result = poll_result(analysis_id)
        if not result:
            print("  分析超时，跳过")
            results.append({"person_id": pid, "status": "timeout", "answers": {}})
            continue

        person_answers = {}
        for q in questions:
            qid = q["question_id"]
            question_text = q["question"]
            options_text = "\n".join(q.get("options", []))
            prompt = (
                f"{question_text}\n\n选项：\n{options_text}\n\n"
                "请分析命盘后选择一个答案，只需回答选项字母（如 A/B/C/D）。"
            )

            reply = ask_question(analysis_id, prompt, school)
            person_answers[qid] = reply
            total_q += 1
            print(f"  {qid}: {reply[:50]}...")

        results.append({
            "person_id": pid,
            "status": "completed",
            "birth": birth,
            "gender": gender,
            "answers": person_answers,
        })

    output = {
        "benchmark": "baziqa",
        "timestamp": datetime.now().isoformat(),
        "school": school,
        "total_persons": len(persons),
        "total_questions": total_q,
        "results": results,
    }

    out_path = RESULTS_DIR / f"baziqa_{school}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n结果已保存: {out_path}")
    return output
