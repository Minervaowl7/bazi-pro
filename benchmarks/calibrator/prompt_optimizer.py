"""Prompt A/B 测试器"""
import asyncio
from pathlib import Path
from typing import Awaitable, Callable

from benchmarks.scoring.extractor import extract_answer

DIMENSION_TEMPLATES: dict[str, str] = {
    "事业": "根据命盘分析此人的事业运势特点，选择最符合的选项。",
    "感情": "根据命盘分析此人的感情婚姻特点，选择最符合的选项。",
    "六亲": "根据命盘分析此人的六亲关系特点，选择最符合的选项。",
    "健康": "根据命盘分析此人的健康体质特点，选择最符合的选项。",
    "财运": "根据命盘分析此人的财运特点，选择最符合的选项。",
    "性格": "根据命盘分析此人的性格特点，选择最符合的选项。",
    "运势": "根据命盘分析此人的运势特点，选择最符合的选项。",
    "学业": "根据命盘分析此人的学业特点，选择最符合的选项。",
}

VARIANTS: list[dict] = [
    {"name": "baseline", "classical_count": 0, "prefix": ""},
    {
        "name": "few_classical",
        "classical_count": 3,
        "prefix": "参考以下古籍论述：\n{classical_quotes}\n\n",
    },
    {
        "name": "many_classical",
        "classical_count": 8,
        "prefix": "参考以下古籍论述：\n{classical_quotes}\n\n",
    },
]


def build_prompt(
    question: str,
    options: list[str],
    dimension: str,
    variant: dict,
    classical_quotes: list[str] | None = None,
) -> str:
    template = DIMENSION_TEMPLATES.get(dimension, "")
    prefix = ""
    if variant["prefix"] and classical_quotes:
        count = variant["classical_count"]
        selected = classical_quotes[:count]
        quotes_text = "\n".join(f"- {q}" for q in selected)
        prefix = variant["prefix"].format(classical_quotes=quotes_text)

    options_text = "\n".join(options)
    return f"{prefix}{template}\n\n题目：{question}\n\n选项：\n{options_text}\n\n请直接给出选项字母（A/B/C/D）。"


async def run_ab_test(
    questions_by_dimension: dict[str, list[dict]],
    llm_fn: Callable[[str], Awaitable[str]],
    classical_quotes: list[str] | None = None,
) -> dict[str, dict]:
    results: dict[str, dict] = {}
    best: dict[str, str] = {}

    for dimension, questions in questions_by_dimension.items():
        dim_results: dict[str, float] = {}

        for variant in VARIANTS:
            async def _eval_one(q: dict) -> bool:
                prompt = build_prompt(
                    q["question"], q["options"], dimension, variant, classical_quotes
                )
                reply = await llm_fn(prompt)
                extracted = extract_answer(reply)
                return extracted == q["answer"].strip().upper()

            outcomes = await asyncio.gather(*[_eval_one(q) for q in questions])
            total = len(questions)
            correct = sum(1 for o in outcomes if o)

            accuracy = correct / total if total > 0 else 0.0
            dim_results[variant["name"]] = accuracy

        results[dimension] = dim_results
        if dim_results:
            best[dimension] = max(dim_results, key=dim_results.get)  # type: ignore[arg-type]

    results["best"] = best  # type: ignore[assignment]
    return results


def save_optimal_prompts(
    best_prompts: dict[str, str],
    output_dir: Path | str = Path("benchmarks/calibrator/prompts"),
) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for dimension, variant_name in best_prompts.items():
        variant = next((v for v in VARIANTS if v["name"] == variant_name), VARIANTS[0])
        template = DIMENSION_TEMPLATES.get(dimension, "")
        prefix = variant["prefix"].replace("{classical_quotes}", "（具体古籍语料按需注入）") if variant["prefix"] else ""
        content = f"{prefix}{template}"
        (out / f"{dimension}.txt").write_text(content, encoding="utf-8")
