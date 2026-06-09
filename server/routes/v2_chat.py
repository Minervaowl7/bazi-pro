from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from server.db import (
    get_analysis,
    get_chat_messages,
    get_report,
    insert_chat_message,
    save_report,
)
from server.deps import error_response
from server.llm import (
    build_chat_system_prompt,
    build_report_system_prompt,
    chat_completion,
    is_llm_configured,
)

logger = logging.getLogger("bazi-pro")

router = APIRouter()


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
            new_keys = {"overview", "past_validation", "future_luck", "career_wealth", "marriage_love", "family", "health", "guidance"}
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

    history = await get_chat_messages(payload.analysis_id, limit=20, school=payload.school)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": payload.message})

    await insert_chat_message(payload.analysis_id, "user", payload.message, school=payload.school)

    try:
        reply = await chat_completion(messages)
        await insert_chat_message(payload.analysis_id, "assistant", reply, citations=citations or "", school=payload.school)
        response_payload = {"reply": reply}
        if citations is not None:
            response_payload["citations"] = citations
        return JSONResponse(response_payload)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error("Chat failed for analysis %s: %s\n%s", payload.analysis_id, e, tb)
        err_msg = str(e) or type(e).__name__
        return error_response(500, "LLM_ERROR", f"LLM 调用失败: {err_msg}")


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
                "marriage_love", "family", "health", "guidance",
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
