from __future__ import annotations

import asyncio
import logging
from collections import Counter

from benchmarks.optimizers.exam_prompts import build_hybrid_prompt
from benchmarks.scoring.extractor import extract_answer

logger = logging.getLogger(__name__)


async def _call_with_retry(
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 8192,
    max_attempts: int = 4,
) -> str:
    """调用 LLM，带指数退避重试"""
    from server.llm import chat_completion

    for attempt in range(max_attempts):
        try:
            reply = await chat_completion(
                messages, temperature=temperature, max_tokens=max_tokens,
            )
            if reply and reply.strip():
                return reply
            logger.warning("[sc] empty reply on attempt %d/%d", attempt + 1, max_attempts)
        except Exception as e:
            logger.warning("[sc] error on attempt %d/%d: %s", attempt + 1, max_attempts, e)

        if attempt < max_attempts - 1:
            wait = min(2 ** attempt * 3, 30)
            await asyncio.sleep(wait)

    return ""


async def answer_with_consistency(
    analysis_result: dict,
    question: str,
    options: list[str],
    category: str,
    n_samples: int = 1,
    temperature: float = 0.7,
    retrieval_results: dict | list | None = None,
) -> tuple[str, list[str]]:
    """Self-Consistency: 跑 n_samples 次，多数投票

    Args:
        retrieval_results: RAG 检索结果，注入到 prompt 中

    Returns:
        (final_answer, all_answers): 最终答案和所有采样答案
    """
    system_prompt = build_hybrid_prompt(analysis_result, category, retrieval_results, options)
    user_prompt = f"{question}\n\n" + "\n".join(options)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    answers = []
    for _ in range(n_samples):
        reply = await _call_with_retry(messages, temperature=temperature)
        if reply:
            answer = extract_answer(reply)
            if answer:
                answers.append(answer)

    if not answers:
        reply = await _call_with_retry(messages, temperature=0)
        if reply:
            ans = extract_answer(reply)
            return ans, [ans] if ans else []
        return "", []

    counter = Counter(answers)
    final = counter.most_common(1)[0][0]
    return final, answers
