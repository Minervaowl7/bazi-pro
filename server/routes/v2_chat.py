from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from server.db import (
    get_analysis,
    get_chat_messages,
    get_latest_summary,
    get_messages_after_id,
    get_report,
    insert_chat_message,
    insert_chat_summary,
    save_report,
)
from server.deps import error_response
from server.llm import (
    build_chat_system_prompt,
    build_report_system_prompt,
    chat_completion,
    chat_completion_stream_typed,
    chat_completion_stream_with_tools,
    chat_completion_with_tools,
    is_llm_configured,
)

logger = logging.getLogger("bazi-pro")

router = APIRouter()

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


class ChatRequest(BaseModel):
    analysis_id: str = Field(..., description="分析记录 ID")
    message: str = Field(..., description="用户消息")
    school: str = Field(default="ziping", description="派别视角: ziping/mangpai/xinpai")
    retrieval_depth: str = Field(default="enhanced", description="检索深度: basic/enhanced")


class ReportRequest(BaseModel):
    analysis_id: str = Field(..., description="分析记录 ID")
    school: str = Field(default="ziping", description="派别视角: ziping/mangpai/xinpai")
    retrieval_depth: str = Field(default="enhanced", description="检索深度: basic/enhanced")


def _extract_analysis_context(result: dict) -> dict:
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


def _parse_report_json(raw_reply: str) -> dict:
    try:
        cleaned = raw_reply.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):]
        if cleaned.startswith("```"):
            cleaned = cleaned[len("```"):]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-len("```")]
        cleaned = cleaned.strip()
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            new_keys = {"overview", "past_validation", "future_luck", "career_wealth", "marriage_love", "family", "health", "guidance", "ziwei"}
            old_keys = {"overview", "personality", "career", "marriage", "health", "dayun_analysis", "lucky"}

            if new_keys.issubset(parsed.keys()):
                return parsed
            if old_keys.issubset(parsed.keys()):
                return {
                    "overview": parsed.get("overview", ""),
                    "past_validation": "",
                    "future_luck": parsed.get("dayun_analysis", ""),
                    "career_wealth": parsed.get("career", ""),
                    "marriage_love": parsed.get("marriage", ""),
                    "family": "",
                    "health": parsed.get("health", ""),
                    "guidance": parsed.get("lucky", ""),
                    "ziwei": "",
                }
            return {
                "overview": parsed.get("overview", ""),
                "past_validation": parsed.get("past_validation", ""),
                "future_luck": parsed.get("future_luck", parsed.get("dayun_analysis", "")),
                "career_wealth": parsed.get("career_wealth", parsed.get("career", "")),
                "marriage_love": parsed.get("marriage_love", parsed.get("marriage", "")),
                "family": parsed.get("family", ""),
                "health": parsed.get("health", ""),
                "guidance": parsed.get("guidance", parsed.get("lucky", "")),
                "ziwei": parsed.get("ziwei", ""),
            }
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse report JSON: %s", e)

    return {
        "overview": raw_reply,
        "past_validation": "",
        "future_luck": "",
        "career_wealth": "",
        "marriage_love": "",
        "family": "",
        "health": "",
        "guidance": "",
        "ziwei": "",
    }


@router.post("/api/v2/chat")
async def api_v2_chat(payload: ChatRequest):
    if not is_llm_configured():
        return error_response(503, "LLM_NOT_CONFIGURED", "LLM 服务未配置。请设置 LLM_API_KEY 环境变量。")

    record = await get_analysis(payload.analysis_id)
    if not record:
        return error_response(404, "NOT_FOUND", "分析记录不存在")

    result = record.get("full_result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}

    narration = {}
    if isinstance(result, dict) and result.get("status") == "completed":
        try:
            from bazi_pro.narrator import narrate_analysis
            narration = narrate_analysis(result)
        except Exception:
            pass

    retrieval_results = None
    citations = None
    if payload.retrieval_depth != "basic" and isinstance(result, dict):
        try:
            from server.rag_engine import _format_retrieval_for_prompt, retrieve_for_chat
            analysis_context = _extract_analysis_context(result)
            retrieval_results = await asyncio.to_thread(retrieve_for_chat, payload.message, analysis_context, k=5)
            citations = _format_retrieval_for_prompt(retrieval_results)
        except Exception as exc:
            logger.warning("RAG retrieval failed for chat %s: %s", payload.analysis_id, exc)

    system_prompt = build_chat_system_prompt(result or {}, narration, school=payload.school, retrieval_results=retrieval_results)

    # === 对话上下文管理：摘要 + 最近 N 轮 ===
    # 1. 加载最新摘要
    summary = await get_latest_summary(payload.analysis_id, school=payload.school)
    summary_id = summary["id"] if summary else 0
    summary_content = summary["content"] if summary else ""

    # 2. 加载摘要之后的所有用户/助手消息
    all_messages = await get_messages_after_id(
        payload.analysis_id, summary_id, school=payload.school, limit=200
    )

    # 3. 估算 token 数量
    total_tokens = _estimate_tokens(summary_content)
    for msg in all_messages:
        total_tokens += _estimate_tokens(msg["content"])

    # 4. 超过 token 预算时自动生成摘要
    max_context_messages = _MAX_CONTEXT_ROUNDS * 2  # 每轮 = user + assistant
    if total_tokens > _TOKEN_BUDGET and len(all_messages) > max_context_messages:
        cutoff = len(all_messages) - max_context_messages
        older_messages = all_messages[:cutoff]
        recent_messages = all_messages[cutoff:]

        try:
            new_summary = await _generate_chat_summary(older_messages, summary_content)
            await insert_chat_summary(payload.analysis_id, new_summary, school=payload.school)
            summary_content = new_summary
            all_messages = recent_messages
        except Exception as e:
            logger.warning("Summary generation failed for chat %s: %s", payload.analysis_id, e)
            # 摘要失败时降级：只保留最近 N 轮
            all_messages = all_messages[-max_context_messages:]

    # 5. 构建 LLM 消息列表
    messages = [{"role": "system", "content": system_prompt}]
    if summary_content:
        messages.append({"role": "system", "content": f"【对话历史摘要】\n{summary_content}"})
    for msg in all_messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": payload.message})

    await insert_chat_message(payload.analysis_id, "user", payload.message, school=payload.school)

    # === 加载命理工具集 ===
    tools = None
    try:
        from server.agents.tools import BAZI_TOOLS
        tools = BAZI_TOOLS
    except ImportError:
        logger.debug("命理工具集不可用，跳过 function calling")

    try:
        if tools:
            # 带工具的 LLM 调用（自动处理工具调用循环）
            result = await chat_completion_with_tools(messages, tools=tools)
            reply = result.get("content", "")
            tool_calls_log = result.get("tool_calls_log", [])

            # 将工具调用日志序列化为可存储的格式
            citations_with_tools = citations or ""
            if tool_calls_log:
                tool_summary = json.dumps(tool_calls_log, ensure_ascii=False)
                if citations_with_tools:
                    citations_with_tools += "\n" + tool_summary
                else:
                    citations_with_tools = tool_summary
        else:
            reply = await chat_completion(messages)
            tool_calls_log = []
            citations_with_tools = citations or ""

        await insert_chat_message(
            payload.analysis_id, "assistant", reply,
            citations=citations_with_tools, school=payload.school,
        )
        response_payload: dict = {"reply": reply}
        if citations is not None:
            response_payload["citations"] = citations
        if tool_calls_log:
            response_payload["tool_calls"] = [
                {"name": tc["name"], "arguments": tc["arguments"], "result": tc.get("result", "")}
                for tc in tool_calls_log
            ]
        return JSONResponse(response_payload)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error("Chat failed for analysis %s: %s\n%s", payload.analysis_id, e, tb)
        err_msg = str(e) or type(e).__name__
        return error_response(500, "LLM_ERROR", f"LLM 调用失败: {err_msg}")


@router.post("/api/v2/chat/stream")
async def api_v2_chat_stream(payload: ChatRequest):
    """SSE 流式 Chat 端点 — 逐字输出 + reasoning_content 折叠"""
    if not is_llm_configured():
        return error_response(503, "LLM_NOT_CONFIGURED", "LLM 服务未配置。请设置 LLM_API_KEY 环境变量。")

    record = await get_analysis(payload.analysis_id)
    if not record:
        return error_response(404, "NOT_FOUND", "分析记录不存在")

    result = record.get("full_result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}

    narration = {}
    if isinstance(result, dict) and result.get("status") == "completed":
        try:
            from bazi_pro.narrator import narrate_analysis
            narration = narrate_analysis(result)
        except Exception:
            pass

    retrieval_results = None
    citations = None
    if payload.retrieval_depth != "basic" and isinstance(result, dict):
        try:
            from server.rag_engine import _format_retrieval_for_prompt, retrieve_for_chat
            analysis_context = _extract_analysis_context(result)
            retrieval_results = await asyncio.to_thread(retrieve_for_chat, payload.message, analysis_context, k=5)
            citations = _format_retrieval_for_prompt(retrieval_results)
        except Exception as exc:
            logger.warning("RAG retrieval failed for chat %s: %s", payload.analysis_id, exc)

    system_prompt = build_chat_system_prompt(result or {}, narration, school=payload.school, retrieval_results=retrieval_results)

    # === 对话上下文管理：摘要 + 最近 N 轮 ===
    summary = await get_latest_summary(payload.analysis_id, school=payload.school)
    summary_id = summary["id"] if summary else 0
    summary_content = summary["content"] if summary else ""

    all_messages = await get_messages_after_id(
        payload.analysis_id, summary_id, school=payload.school, limit=200
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
            await insert_chat_summary(payload.analysis_id, new_summary, school=payload.school)
            summary_content = new_summary
            all_messages = recent_messages
        except Exception as e:
            logger.warning("Summary generation failed for chat %s: %s", payload.analysis_id, e)
            all_messages = all_messages[-max_context_messages:]

    messages = [{"role": "system", "content": system_prompt}]
    if summary_content:
        messages.append({"role": "system", "content": f"【对话历史摘要】\n{summary_content}"})
    for msg in all_messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": payload.message})

    # 保存用户消息
    await insert_chat_message(payload.analysis_id, "user", payload.message, school=payload.school)

    # === 加载命理工具集 ===
    tools = None
    try:
        from server.agents.tools import BAZI_TOOLS
        tools = BAZI_TOOLS
    except ImportError:
        logger.debug("命理工具集不可用，跳过 function calling")

    async def _sse_generator():
        """SSE 生成器：逐块推送 token/reasoning/tool_call/tool_result/done/error"""
        full_reply = ""
        tool_calls_log = []
        try:
            if tools:
                # 带工具的流式调用
                async for chunk in chat_completion_stream_with_tools(messages, tools=tools):
                    chunk_type = chunk.get("type", "token")
                    content = chunk.get("content", "")
                    if chunk_type == "token":
                        full_reply += content
                    elif chunk_type == "tool_call":
                        try:
                            tc_data = json.loads(content)
                            tool_calls_log.append(tc_data)
                        except (json.JSONDecodeError, TypeError):
                            pass
                    yield f"data: {json.dumps({'type': chunk_type, 'content': content}, ensure_ascii=False)}\n\n"
            else:
                # 无工具的普通流式调用
                async for chunk in chat_completion_stream_typed(messages):
                    chunk_type = chunk.get("type", "token")
                    content = chunk.get("content", "")
                    if chunk_type == "token":
                        full_reply += content
                    yield f"data: {json.dumps({'type': chunk_type, 'content': content}, ensure_ascii=False)}\n\n"

            # 流结束，保存助手消息
            if full_reply:
                citations_with_tools = citations or ""
                if tool_calls_log:
                    tool_summary = json.dumps(tool_calls_log, ensure_ascii=False)
                    if citations_with_tools:
                        citations_with_tools += "\n" + tool_summary
                    else:
                        citations_with_tools = tool_summary
                await insert_chat_message(
                    payload.analysis_id, "assistant", full_reply,
                    citations=citations_with_tools, school=payload.school,
                )
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error("Chat stream failed for analysis %s: %s", payload.analysis_id, e)
            # 保存错误消息作为助手回复，避免孤立用户消息
            try:
                err_reply = f"抱歉，AI 解读过程中出现错误：{str(e) or type(e).__name__}"
                await insert_chat_message(
                    payload.analysis_id, "assistant", err_reply,
                    school=payload.school,
                )
            except Exception:
                logger.warning("Failed to save error reply for analysis %s", payload.analysis_id)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e) or type(e).__name__}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/v2/chat/{analysis_id}")
async def api_v2_get_chat(analysis_id: str, school: str = Query(default=None)):
    messages = await get_chat_messages(analysis_id, limit=100, school=school)
    return JSONResponse({"messages": messages})


@router.post("/api/v2/report")
async def api_v2_create_report(payload: ReportRequest):
    if not is_llm_configured():
        return error_response(503, "LLM_NOT_CONFIGURED", "LLM 服务未配置。请设置 LLM_API_KEY 环境变量。")

    record = await get_analysis(payload.analysis_id)
    if not record:
        return error_response(404, "NOT_FOUND", "分析记录不存在")

    if record.get("status") != "completed":
        return error_response(400, "ANALYSIS_NOT_COMPLETED", "分析尚未完成，无法生成报告")

    result = record.get("full_result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}

    if not isinstance(result, dict) or result.get("status") != "completed":
        return error_response(400, "INVALID_RESULT", "分析结果数据异常，无法生成报告")

    narration = {}
    try:
        from bazi_pro.narrator import narrate_analysis
        narration = narrate_analysis(result)
    except Exception:
        pass

    birth_json = record.get("birth_json", {})
    if isinstance(birth_json, str):
        try:
            birth_json = json.loads(birth_json)
        except (json.JSONDecodeError, TypeError):
            birth_json = {}

    dayun_data = result.get("dayun") or birth_json.get("大运", None)

    retrieval_results = None
    citations = None
    if payload.retrieval_depth != "basic":
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
            logger.warning("RAG retrieval failed for report %s: %s", payload.analysis_id, exc)

    system_prompt = build_report_system_prompt(result, narration, dayun_data, school=payload.school, retrieval_results=retrieval_results)
    messages = [{"role": "system", "content": system_prompt}]

    try:
        raw_reply = await chat_completion(messages, temperature=0.7, max_tokens=8192)
    except Exception as e:
        logger.error("Report LLM call failed for analysis %s: %s", payload.analysis_id, e)
        err_msg = str(e) or type(e).__name__
        return error_response(500, "LLM_ERROR", f"LLM 调用失败: {err_msg}")

    report_data = _parse_report_json(raw_reply)

    report_id = await save_report(payload.analysis_id, report_data, citations=citations)

    response_payload = {
        "status": "completed",
        "analysis_id": payload.analysis_id,
        "report_id": report_id,
        "sections": report_data,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if citations is not None:
        response_payload["citations"] = citations
    return JSONResponse(response_payload)


@router.get("/api/v2/report/{analysis_id}")
async def api_v2_get_report(analysis_id: str):
    record = await get_report(analysis_id)
    if not record:
        return error_response(404, "NOT_FOUND", "报告不存在，请先通过 POST /api/v2/report 生成")

    return JSONResponse({
        "status": "completed",
        "analysis_id": record["analysis_id"],
        "report_id": record["id"],
        "sections": record["report_data"],
        "citations": record.get("citations"),
        "created_at": record["created_at"],
    })


@router.get("/api/v2/report/{analysis_id}/pdf")
async def api_v2_report_pdf(analysis_id: str):
    """下载详批报告 PDF"""
    from fastapi.responses import Response

    # 获取报告数据
    record = await get_report(analysis_id)
    if not record:
        return error_response(404, "NOT_FOUND", "报告不存在，请先通过 POST /api/v2/report 生成")

    # 获取分析数据
    analysis = await get_analysis(analysis_id)
    if not analysis:
        return error_response(404, "NOT_FOUND", "分析记录不存在")

    # 提取姓名
    birth_json = analysis.get("birth_json") or {}
    if isinstance(birth_json, str):
        try:
            birth_json = json.loads(birth_json)
        except Exception:
            birth_json = {}
    name = birth_json.get("name") or ""

    # 构造报告数据
    report_data = {
        "sections": record.get("report_data") or {},
        "citations": record.get("citations") or {},
        "created_at": record.get("created_at"),
    }

    try:
        from server.report_pdf import generate_report_pdf
        pdf_bytes = generate_report_pdf(report_data, analysis, name=name)
    except Exception as e:
        logger.error("PDF generation failed for analysis %s: %s", analysis_id, e)
        return error_response(500, "PDF_ERROR", f"PDF 生成失败: {e}")

    display_name = name or "命主"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="report_{display_name}.pdf"',
        },
    )
