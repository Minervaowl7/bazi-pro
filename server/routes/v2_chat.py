from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from server.db import (
    get_analysis,
    get_chat_messages,
    get_report,
    insert_chat_message,
    save_report,
)
from server.deps import error_response, verify_api_key
from server.llm import (
    chat_completion,
    chat_completion_stream_typed,
    chat_completion_stream_with_tools,
    chat_completion_with_tools,
    is_llm_configured,
)

logger = logging.getLogger("bazi-pro")

router = APIRouter()

from server.chat_service import (  # noqa: E402 — module-level import after router
    build_report_context,
    prepare_chat_context,
)


class ChatRequest(BaseModel):
    analysis_id: str = Field(..., description="分析记录 ID")
    message: str = Field(..., max_length=10000, description="用户消息")
    school: str = Field(default="ziping", description="派别视角: ziping/mangpai/xinpai")
    retrieval_depth: str = Field(default="enhanced", description="检索深度: basic/enhanced")


class ReportRequest(BaseModel):
    analysis_id: str = Field(..., description="分析记录 ID")
    school: str = Field(default="ziping", description="派别视角: ziping/mangpai/xinpai")
    retrieval_depth: str = Field(default="enhanced", description="检索深度: basic/enhanced")


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
async def api_v2_chat(payload: ChatRequest, _auth=Depends(verify_api_key)):
    if not is_llm_configured():
        return error_response(503, "LLM_NOT_CONFIGURED", "LLM 服务未配置。请设置 LLM_API_KEY 环境变量。")

    ctx = await prepare_chat_context(
        payload.analysis_id, payload.message, payload.school, payload.retrieval_depth,
    )
    if ctx is None:
        return error_response(404, "NOT_FOUND", "分析记录不存在")

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
            result = await chat_completion_with_tools(ctx.messages, tools=tools)
            reply = result.get("content", "")
            tool_calls_log = result.get("tool_calls_log", [])

            # 将工具调用日志序列化为可存储的格式
            citations_with_tools = ctx.citations or ""
            if tool_calls_log:
                tool_summary = json.dumps(tool_calls_log, ensure_ascii=False)
                if citations_with_tools:
                    citations_with_tools += "\n" + tool_summary
                else:
                    citations_with_tools = tool_summary
        else:
            reply = await chat_completion(ctx.messages)
            tool_calls_log = []
            citations_with_tools = ctx.citations or ""

        await insert_chat_message(
            payload.analysis_id, "assistant", reply,
            citations=citations_with_tools, school=payload.school,
        )
        response_payload: dict = {"reply": reply}
        if ctx.citations is not None:
            response_payload["citations"] = ctx.citations
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
        return error_response(500, "LLM_ERROR", "LLM 调用失败，请稍后重试")


@router.post("/api/v2/chat/stream")
async def api_v2_chat_stream(payload: ChatRequest, _auth=Depends(verify_api_key)):
    """SSE 流式 Chat 端点 — 逐字输出 + reasoning_content 折叠"""
    if not is_llm_configured():
        return error_response(503, "LLM_NOT_CONFIGURED", "LLM 服务未配置。请设置 LLM_API_KEY 环境变量。")

    ctx = await prepare_chat_context(
        payload.analysis_id, payload.message, payload.school, payload.retrieval_depth,
    )
    if ctx is None:
        return error_response(404, "NOT_FOUND", "分析记录不存在")

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
                async for chunk in chat_completion_stream_with_tools(ctx.messages, tools=tools):
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
                async for chunk in chat_completion_stream_typed(ctx.messages):
                    chunk_type = chunk.get("type", "token")
                    content = chunk.get("content", "")
                    if chunk_type == "token":
                        full_reply += content
                    yield f"data: {json.dumps({'type': chunk_type, 'content': content}, ensure_ascii=False)}\n\n"

            # 流结束，保存助手消息
            if full_reply:
                citations_with_tools = ctx.citations or ""
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
                await insert_chat_message(
                    payload.analysis_id, "assistant", "抱歉，AI 解读过程中出现错误，请稍后重试",
                    school=payload.school,
                )
            except Exception:
                logger.warning("Failed to save error reply for analysis %s", payload.analysis_id)
            yield f"data: {json.dumps({'type': 'error', 'content': 'AI 解读过程中出现错误，请稍后重试'}, ensure_ascii=False)}\n\n"

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
async def api_v2_get_chat(analysis_id: str, school: str = Query(default=None), _auth=Depends(verify_api_key)):
    messages = await get_chat_messages(analysis_id, limit=100, school=school)
    return JSONResponse({"messages": messages})


@router.post("/api/v2/report")
async def api_v2_create_report(payload: ReportRequest, _auth=Depends(verify_api_key)):
    if not is_llm_configured():
        return error_response(503, "LLM_NOT_CONFIGURED", "LLM 服务未配置。请设置 LLM_API_KEY 环境变量。")

    ctx, err = await build_report_context(
        payload.analysis_id, payload.school, payload.retrieval_depth,
    )
    if err == "NOT_FOUND":
        return error_response(404, "NOT_FOUND", "分析记录不存在")
    if err == "ANALYSIS_NOT_COMPLETED":
        return error_response(400, "ANALYSIS_NOT_COMPLETED", "分析尚未完成，无法生成报告")
    if err == "INVALID_RESULT":
        return error_response(400, "INVALID_RESULT", "分析结果数据异常，无法生成报告")

    messages = [{"role": "system", "content": ctx.system_prompt}]

    try:
        raw_reply = await chat_completion(messages, temperature=0.7, max_tokens=8192)
    except Exception as e:
        logger.error("Report LLM call failed for analysis %s: %s", payload.analysis_id, e)
        return error_response(500, "LLM_ERROR", "LLM 调用失败，请稍后重试")

    report_data = _parse_report_json(raw_reply)

    report_id = await save_report(payload.analysis_id, report_data, citations=ctx.citations)

    response_payload = {
        "status": "completed",
        "analysis_id": payload.analysis_id,
        "report_id": report_id,
        "sections": report_data,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if ctx.citations is not None:
        response_payload["citations"] = ctx.citations
    return JSONResponse(response_payload)


@router.get("/api/v2/report/{analysis_id}")
async def api_v2_get_report(analysis_id: str, _auth=Depends(verify_api_key)):
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
async def api_v2_report_pdf(analysis_id: str, _auth=Depends(verify_api_key)):
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
