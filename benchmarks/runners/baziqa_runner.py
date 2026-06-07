"""BaziQA 评测运行器

读取 BaziQA 数据集 → 调用 bazi-pro 排盘+LLM解盘 → 保存评测结果
支持混合 Prompt (baseline RAG + Exam 结构化推理) + Self-Consistency 投票

v2 优化：
- n_samples=1（reasoning model 忽略 temperature，SC 投票无效）
- 问题级并行（asyncio.gather + 信号量控制并发）
- RAG 古籍检索增强（双模板合并查询）
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

import requests

from benchmarks.config import API_BASE, BAZIQA_DIR, RESULTS_DIR

_ENV_LOADED = False

def _ensure_env():
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    env_path = Path(__file__).resolve().parent.parent.parent / "server" / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and k not in __import__("os").environ:
                    __import__("os").environ[k] = v
    _ENV_LOADED = True


def _build_analysis_context(analysis_result: dict) -> dict:
    """从 analysis_result 构建 RAG 检索所需的 analysis_context"""
    validation = analysis_result.get("validation", {}) if isinstance(analysis_result.get("validation"), dict) else {}
    pattern_info = analysis_result.get("pattern", {}) if isinstance(analysis_result.get("pattern"), dict) else {}
    yongshen_info = analysis_result.get("yongshen", {}) if isinstance(analysis_result.get("yongshen"), dict) else {}
    strength = analysis_result.get("strength", {}) if isinstance(analysis_result.get("strength"), dict) else {}

    day_master = analysis_result.get("日主", "") or validation.get("day_master", "") or analysis_result.get("day_master", "")
    pattern = pattern_info.get("pattern", "") if isinstance(pattern_info, dict) else ""
    ws = strength.get("wangshuai", {}) if isinstance(strength, dict) else {}
    ws_verdict = ws.get("verdict", "") if isinstance(ws, dict) else ""
    yongshen = yongshen_info.get("yongshen", "") if isinstance(yongshen_info, dict) else ""

    return {
        "day_master": day_master,
        "pattern": {"pattern": pattern},
        "wangshuai": {"verdict": ws_verdict},
        "yongshen": {"yongshen": yongshen},
    }


def _retrieve_rag(question: str, analysis_context: dict) -> dict | list | None:
    """调用 RAG 检索古籍引用"""
    try:
        from server.rag_engine import retrieve_for_chat
        return retrieve_for_chat(question, analysis_context, k=5)
    except Exception:
        return None


def load_baziqa_dataset(years: list[int] | None = None) -> list[dict]:
    """加载 BaziQA 数据集，返回所有命主列表"""
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
        "skip_llm_overview": True,
    }
    try:
        r = requests.post(f"{API_BASE}/api/v2/analyze", json=payload, timeout=10)
        if r.status_code == 202:
            return r.json().get("analysis_id")
    except Exception:
        pass
    return None


def poll_result(analysis_id: str, timeout: int = 300) -> dict | None:
    """轮询分析结果"""
    deadline = time.time() + timeout
    elapsed = 0
    while time.time() < deadline:
        try:
            r = requests.get(f"{API_BASE}/api/v2/analysis/{analysis_id}", timeout=10)
            if r.status_code == 429:
                time.sleep(10)
                elapsed += 10
                continue
            data = r.json()
            if data.get("status") == "completed":
                return data.get("result", {})
            if data.get("status") == "failed":
                return None
        except Exception:
            pass
        time.sleep(3)
        elapsed += 3
        if elapsed % 30 == 0:
            print(f"    ... 等待分析中 ({elapsed}s)")
    return None


async def ask_question_async(analysis_result: dict, question: str, options: list[str],
                             category: str, n_samples: int = 1) -> str:
    """使用混合 Prompt + Self-Consistency 投票回答问题（异步版本）"""
    from benchmarks.optimizers.self_consistency import answer_with_consistency

    analysis_context = _build_analysis_context(analysis_result)
    retrieval_results = _retrieve_rag(question, analysis_context)

    try:
        final, all_answers = await answer_with_consistency(
            analysis_result, question, options, category,
            n_samples=n_samples, temperature=0.7,
            retrieval_results=retrieval_results,
        )
        return final
    except Exception as e:
        return f"[ERROR] {e}"


def ask_question(analysis_result: dict, question: str, options: list[str],
                 category: str, n_samples: int = 1) -> str:
    """同步包装"""
    _ensure_env()
    return asyncio.run(ask_question_async(
        analysis_result, question, options, category, n_samples
    ))


async def _process_person_questions(
    result: dict, questions: list[dict], n_samples: int, semaphore: asyncio.Semaphore,
) -> dict[str, str]:
    """并行处理一个命主的所有问题"""
    async def _one(q: dict, delay: float = 0) -> tuple[str, str]:
        if delay > 0:
            await asyncio.sleep(delay)
        async with semaphore:
            qid = q["question_id"]
            reply = await ask_question_async(
                result, q["question"], q.get("options", []),
                q.get("category", "其他"), n_samples,
            )
            return qid, reply

    tasks = [_one(q, i * 0.5) for i, q in enumerate(questions)]
    pairs = await asyncio.gather(*tasks, return_exceptions=True)
    answers = {}
    for pair in pairs:
        if isinstance(pair, Exception):
            continue
        qid, reply = pair
        answers[qid] = reply
    return answers


def run_baziqa(years: list[int] | None = None, max_persons: int = 0,
               school: str = "ziping", n_samples: int = 1,
               concurrency: int = 2) -> dict:
    """运行 BaziQA 评测

    Args:
        n_samples: 每题 LLM 采样次数（reasoning model 建议 1，SC 无效）
        concurrency: 每个命主内问题并行数
    """
    _ensure_env()
    persons = load_baziqa_dataset(years)
    if max_persons > 0:
        persons = persons[:max_persons]
    print(f"加载 {len(persons)} 个命主 (n_samples={n_samples}, concurrency={concurrency})")

    results = []
    total_q = 0
    correct_q = 0
    semaphore = asyncio.Semaphore(concurrency)

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
        for qi, q in enumerate(questions):
            qid = q["question_id"]
            question_text = q["question"]
            options = q.get("options", [])
            category = q.get("category", "其他")
            gt = q.get("answer", "").strip().upper()

            if qi > 0:
                time.sleep(8)

            reply = ask_question(result, question_text, options, category, n_samples)
            if not reply:
                time.sleep(15)
                reply = ask_question(result, question_text, options, category, n_samples)

            is_correct = reply.strip().upper() == gt if gt else False
            if gt:
                total_q += 1
                if is_correct:
                    correct_q += 1

            person_answers[qid] = reply
            mark = "✓" if is_correct else "✗"
            acc_str = f" ({correct_q}/{total_q}={correct_q/total_q*100:.1f}%)" if total_q > 0 else ""
            print(f"  {mark} {qid}: {reply} (GT:{gt}){acc_str}")

        results.append({
            "person_id": pid,
            "status": "completed",
            "birth": birth,
            "gender": gender,
            "answers": person_answers,
        })
        time.sleep(5)

    accuracy = correct_q / total_q * 100 if total_q > 0 else 0
    output = {
        "benchmark": "baziqa",
        "timestamp": datetime.now().isoformat(),
        "school": school,
        "n_samples": n_samples,
        "concurrency": concurrency,
        "total_persons": len(persons),
        "total_questions": total_q,
        "correct": correct_q,
        "accuracy": round(accuracy, 1),
        "results": results,
    }

    out_path = RESULTS_DIR / f"baziqa_{school}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n结果已保存: {out_path}")
    print(f"准确率: {correct_q}/{total_q} = {accuracy:.1f}%")
    return output
