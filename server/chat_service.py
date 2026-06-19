"""Shared logic for chat and report endpoints.

Extracts duplicated context-building code from v2_chat.py so that
api_v2_chat, api_v2_chat_stream, and api_v2_create_report each call
a single function instead of repeating ~80 lines of setup.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field

from server.db import (
    get_analysis,
    get_latest_summary,
    get_messages_after_id,
    insert_chat_summary,
)
from server.llm import (
    build_chat_system_prompt,
    build_report_system_prompt,
)

logger = logging.getLogger("bazi-pro")

# ============ 对话上下文管理常量 ============
_MAX_CONTEXT_ROUNDS = int(os.environ.get("BAZI_CHAT_CONTEXT_ROUNDS", "10"))
"""最大上下文轮数（每轮 = user + assistant 两条消息），默认 10 轮"""

_TOKEN_BUDGET = int(os.environ.get("BAZI_CHAT_TOKEN_BUDGET", "4000"))
"""对话历史 token 预算，超过此值触发自动摘要"""


def _estimate_tokens(text: str) -> int:
    """估算文本的 token 数量（中文约 1.5 字/token，英文约 4 字符/token）"""
    if not text:
        return 0
    cn_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    other_chars = len(text) - cn_chars
    return int(cn_chars / 1.5 + other_chars / 4)


async def _generate_chat_summary(messages: list[dict], previous_summary: str = "") -> str:
    """使用 LLM 生成对话摘要，复用 chat_completion()"""
    from server.llm import chat_completion

    conversation = ""
    for msg in messages:
        role = "命主" if msg["role"] == "user" else "命理师"
        content = msg["content"][:500]  # 截断过长内容
        conversation += f"{role}: {content}\n\n"

    prompt_parts = [
        "请将以下命理对话历史压缩为一段简洁的摘要，保留关键信息：",
        "1. 命主提出的主要问题",
        "2. 命理师给出的核心论断",
        "3. 涉及的具体干支、格局、用神等关键数据",
        "4. 未完成的讨论话题",
    ]
    if previous_summary:
        prompt_parts.append(f"\n\n之前的摘要：\n{previous_summary}")
    prompt_parts.append(f"\n\n新的对话内容：\n{conversation}")
    prompt_parts.append("\n\n请生成更新后的完整摘要，不超过 300 字。")

    summary_messages = [
        {"role": "system", "content": "你是一位命理对话摘要助手，擅长提取关键信息并压缩为简洁摘要。"},
        {"role": "user", "content": "".join(prompt_parts)},
    ]
    return await chat_completion(summary_messages, temperature=0.3, max_tokens=512)


def _extract_analysis_context(result: dict) -> dict:
    """Extract analysis context dict used by RAG retrieval."""
    context: dict = {}
    if isinstance(result, dict):
        context["day_master"] = result.get("day_master", "") or result.get("validation", {}).get("day_master", "")
        pillars = result.get("pillars", []) or result.get("shishen", {}).get("pillars", [])
        context["bazi"] = " ".join(p.get("gan", "") + p.get("zhi", "") for p in pillars if p.get("gan") and p.get("zhi"))

    pattern = result.get("pattern", {}) if isinstance(result, dict) else {}
    if isinstance(pattern, dict):
        context["pattern"] = pattern
    else:
        context["pattern"] = {"name": str(pattern) if pattern else ""}

    strength_info = result.get("strength", {}) if isinstance(result, dict) else {}
    if isinstance(strength_info, dict) and "wangshuai" in strength_info:
        context["wangshuai"] = strength_info["wangshuai"]
    else:
        wangshuai = result.get("wangshuai", {}) if isinstance(result, dict) else {}
        if isinstance(wangshuai, dict):
            context["wangshuai"] = wangshuai
        else:
            context["wangshuai"] = {"verdict": str(wangshuai) if wangshuai else ""}

    yongshen = result.get("yongshen", {}) if isinstance(result, dict) else {}
    if isinstance(yongshen, dict):
        context["yongshen"] = yongshen
    else:
        context["yongshen"] = {"yongshen": str(yongshen) if yongshen else ""}

    return context


async def _load_and_parse_analysis(analysis_id: str) -> tuple[dict | None, dict | str | None]:
    """Load analysis record and parse full_result. Returns (record, result) or (None, None) on not-found."""
    record = await get_analysis(analysis_id)
    if not record:
        return None, None

    result = record.get("full_result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}

    return record, result


def _generate_narration(result: dict) -> dict:
    """Generate deterministic narration from analysis result."""
    narration: dict = {}
    if isinstance(result, dict) and result.get("status") == "completed":
        try:
            from bazi_pro.narrator import narrate_analysis
            narration = narrate_analysis(result)
        except Exception:
            pass
    return narration


async def _retrieve_for_chat(
    message: str, result: dict, retrieval_depth: str, analysis_id: str,
) -> tuple[dict | None, str | None]:
    """Perform RAG retrieval for chat context. Returns (retrieval_results, citations)."""
    retrieval_results = None
    citations = None
    if retrieval_depth != "basic" and isinstance(result, dict):
        try:
            from server.rag_engine import _format_retrieval_for_prompt, retrieve_for_chat
            analysis_context = _extract_analysis_context(result)
            retrieval_results = await asyncio.to_thread(retrieve_for_chat, message, analysis_context, k=5)
            citations = _format_retrieval_for_prompt(retrieval_results)
        except Exception as exc:
            logger.warning("RAG retrieval failed for chat %s: %s", analysis_id, exc)
    return retrieval_results, citations


async def _load_chat_context_messages(
    analysis_id: str, school: str,
) -> tuple[str, list[dict]]:
    """Load summary + recent messages, auto-summarize if over budget.

    Returns (summary_content, all_messages).
    """
    summary = await get_latest_summary(analysis_id, school=school)
    summary_id = summary["id"] if summary else 0
    summary_content = summary["content"] if summary else ""

    all_messages = await get_messages_after_id(
        analysis_id, summary_id, school=school, limit=200,
    )

    total_tokens = _estimate_tokens(summary_content)
    for msg in all_messages:
        total_tokens += _estimate_tokens(msg["content"])

    max_context_messages = _MAX_CONTEXT_ROUNDS * 2
    if total_tokens > _TOKEN_BUDGET and len(all_messages) > max_context_messages:
        cutoff = len(all_messages) - max_context_messages
        older_messages = all_messages[:cutoff]
        recent_messages = all_messages[cutoff:]

        try:
            new_summary = await _generate_chat_summary(older_messages, summary_content)
            await insert_chat_summary(analysis_id, new_summary, school=school)
            summary_content = new_summary
            all_messages = recent_messages
        except Exception as e:
            logger.warning("Summary generation failed for chat %s: %s", analysis_id, e)
            all_messages = all_messages[-max_context_messages:]

    return summary_content, all_messages


def _build_messages_list(
    system_prompt: str, summary_content: str, context_messages: list[dict], user_message: str,
) -> list[dict]:
    """Build the LLM messages list from system prompt, summary, context, and new user message."""
    messages = [{"role": "system", "content": system_prompt}]
    if summary_content:
        messages.append({"role": "system", "content": f"【对话历史摘要】\n{summary_content}"})
    for msg in context_messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    return messages


@dataclass
class ChatContext:
    """Fully prepared context for a chat LLM call."""
    result: dict
    narration: dict
    retrieval_results: dict | None = None
    citations: str | None = None
    messages: list[dict] = field(default_factory=list)


async def prepare_chat_context(
    analysis_id: str, message: str, school: str, retrieval_depth: str,
) -> ChatContext | None:
    """Prepare full chat context: load analysis, narrate, retrieve, build messages.

    Returns None if the analysis record is not found (caller should return 404).
    """
    record, result = await _load_and_parse_analysis(analysis_id)
    if record is None:
        return None

    narration = _generate_narration(result)
    retrieval_results, citations = await _retrieve_for_chat(
        message, result, retrieval_depth, analysis_id,
    )

    system_prompt = build_chat_system_prompt(
        result or {}, narration, school=school, retrieval_results=retrieval_results,
    )

    summary_content, context_messages = await _load_chat_context_messages(analysis_id, school)
    messages = _build_messages_list(system_prompt, summary_content, context_messages, message)

    return ChatContext(
        result=result,
        narration=narration,
        retrieval_results=retrieval_results,
        citations=citations,
        messages=messages,
    )


@dataclass
class ReportContext:
    """Fully prepared context for a report LLM call."""
    result: dict
    narration: dict
    dayun_data: dict | None = None
    retrieval_results: dict | None = None
    citations: dict | None = None
    system_prompt: str = ""


async def build_report_context(
    analysis_id: str, school: str, retrieval_depth: str,
) -> tuple[ReportContext | None, str | None]:
    """Prepare report context. Returns (context, error_code).

    error_code is one of: None (success), "NOT_FOUND", "ANALYSIS_NOT_COMPLETED", "INVALID_RESULT".
    """
    record = await get_analysis(analysis_id)
    if not record:
        return None, "NOT_FOUND"

    if record.get("status") != "completed":
        return None, "ANALYSIS_NOT_COMPLETED"

    result = record.get("full_result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}

    if not isinstance(result, dict) or result.get("status") != "completed":
        return None, "INVALID_RESULT"

    narration = _generate_narration(result)

    birth_json = record.get("birth_json", {})
    if isinstance(birth_json, str):
        try:
            birth_json = json.loads(birth_json)
        except (json.JSONDecodeError, TypeError):
            birth_json = {}

    dayun_data = result.get("dayun") or birth_json.get("大运", None)

    retrieval_results = None
    citations = None
    if retrieval_depth != "basic":
        try:
            from server.rag_engine import _format_retrieval_for_prompt, retrieve_for_report
            analysis_context = _extract_analysis_context(result)
            chapter_keys = [
                "overview", "past_validation", "future_luck", "career_wealth",
                "marriage_love", "family", "health", "guidance", "ziwei",
            ]
            retrieval_results = {}
            citations = {}
            for chapter_key in chapter_keys:
                chapter_result = await asyncio.to_thread(retrieve_for_report, chapter_key, analysis_context, k=5)
                retrieval_results[chapter_key] = chapter_result
                citations[chapter_key] = _format_retrieval_for_prompt(chapter_result)
        except Exception as exc:
            logger.warning("RAG retrieval failed for report %s: %s", analysis_id, exc)

    system_prompt = build_report_system_prompt(
        result, narration, dayun_data, school=school, retrieval_results=retrieval_results,
    )

    ctx = ReportContext(
        result=result,
        narration=narration,
        dayun_data=dayun_data,
        retrieval_results=retrieval_results,
        citations=citations,
        system_prompt=system_prompt,
    )
    return ctx, None
