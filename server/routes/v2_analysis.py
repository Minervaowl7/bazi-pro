from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from server.db import (
    generate_analysis_id,
    get_analysis,
    insert_analysis,
    update_analysis_result,
    update_analysis_status,
)
from server.deps import (
    error_response,
    verify_api_key,
)
from server.sse import broadcast, buffers, lock, subscribers, v2_active_ids

logger = logging.getLogger("bazi-pro")

router = APIRouter()


class BirthAnalyzeRequest(BaseModel):
    性别: str = Field(..., description="性别: 男/女")
    八字: str = Field(..., description="四柱八字，空格分隔")
    日主: str = Field(..., description="日主天干")
    阳历: Optional[str] = Field(default="", description="阳历日期时间")
    农历: Optional[str] = Field(default="", description="农历日期")
    生肖: Optional[str] = Field(default="", description="生肖")
    大运: Optional[list] = Field(default=None, description="大运列表")
    detail_level: str = Field(default="standard")
    longitude: Optional[float] = Field(default=None, description="出生地经度")
    latitude: Optional[float] = Field(default=None, description="出生地纬度")
    school: Optional[str] = Field(default="ziping", description="解读流派: ziping/ziwei/qiongtong")
    skip_llm_overview: Optional[bool] = Field(default=False, description="跳过 LLM 命盘总览生成")
    name: Optional[str] = Field(default="", description="命主姓名（选填）")


class PaipanRequest(BaseModel):
    性别: str = Field(..., description="性别: 男/女")
    阳历: str = Field(..., description="阳历日期时间，如 2002-05-19 06:14")
    农历: Optional[str] = Field(default="", description="农历日期")


class CompareRequest(BaseModel):
    八字: str = Field(..., description="四柱八字，空格分隔")
    日主: str = Field(..., description="日主天干")
    性别: str = Field(default="男", description="性别: 男/女")
    出生年: Optional[int] = Field(default=None, description="出生年份")
    出生月: Optional[int] = Field(default=None, description="出生月份")
    出生日: Optional[int] = Field(default=None, description="出生日期")


@router.post("/api/v2/paipan")
async def api_v2_paipan(payload: PaipanRequest):
    try:
        from bazi_pro.paipan import paipan_from_datetime
        solar = payload.阳历 or ""
        result = paipan_from_datetime(solar, payload.性别, payload.农历 or "")
        return JSONResponse(result)
    except Exception as e:
        return error_response(400, "PAIPAN_ERROR", str(e))


@router.post("/api/v2/analyze")
async def api_v2_analyze(payload: BirthAnalyzeRequest, _auth=Depends(verify_api_key)):
    analysis_id = generate_analysis_id()
    payload_dict = payload.model_dump(exclude_none=True)
    detail_level = payload_dict.pop("detail_level", "standard")
    school = payload_dict.pop("school", "ziping")
    longitude = payload_dict.pop("longitude", None)
    payload_dict.pop("latitude", None)
    skip_llm_overview = payload_dict.pop("skip_llm_overview", False)

    if longitude is not None and payload_dict.get("阳历"):
        from datetime import datetime as _dt

        from server.true_solar_time import correct_to_true_solar_time
        try:
            solar_str = payload_dict["阳历"] or ""
            if solar_str:
                solar_dt = _dt.fromisoformat(solar_str.replace("/", "-").replace(" ", "T"))
                corrected = correct_to_true_solar_time(solar_dt, longitude)
                payload_dict["阳历"] = corrected.strftime("%Y-%m-%d %H:%M")
                payload_dict["真太阳时校正"] = True
        except (ValueError, TypeError):
            pass

    await insert_analysis(analysis_id, payload_dict, detail_level)

    subscribers[analysis_id] = []
    buffers[analysis_id] = []

    asyncio.create_task(_background_analyze_v2(analysis_id, payload_dict, detail_level, school, skip_llm_overview=skip_llm_overview))

    return JSONResponse(
        status_code=202,
        content={
            "analysis_id": analysis_id,
            "status": "processing",
            "stream_url": f"/api/v2/analysis/{analysis_id}/stream",
        },
    )


@router.post("/api/v2/analyze/compare")
async def api_v2_analyze_compare(payload: CompareRequest):
    try:
        from bazi_pro.core.schools import school_analyze
    except ImportError:
        return error_response(503, "SCHOOL_NOT_AVAILABLE", "流派分析模块不可用")

    mcp_json = {
        "八字": payload.八字,
        "日主": payload.日主,
        "性别": payload.性别,
    }
    if payload.出生年:
        mcp_json["出生年"] = payload.出生年
    if payload.出生月:
        mcp_json["出生月"] = payload.出生月
    if payload.出生日:
        mcp_json["出生日"] = payload.出生日

    try:
        results = school_analyze(mcp_json, "all")
        return JSONResponse({
            "status": "completed",
            "schools": results,
        })
    except Exception as e:
        logger.error("Compare analysis failed: %s", e)
        return error_response(500, "ANALYSIS_ERROR", f"分析失败: {str(e)}")


@router.get("/api/v2/analysis/{analysis_id}")
async def api_v2_get_analysis(analysis_id: str):
    if not _validate_analysis_id(analysis_id):
        return error_response(400, "INVALID_FORMAT", "analysis_id 格式不合法")
    record = await get_analysis(analysis_id)
    if not record:
        return error_response(404, "NOT_FOUND", "分析记录不存在")

    result = record.get("full_result")
    if not result:
        return JSONResponse({
            "analysis_id": analysis_id,
            "status": record["status"],
            "message": "分析尚未完成" if record["status"] == "processing" else "无结果数据",
        })

    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            pass

    if isinstance(result, dict) and result.get("status") == "completed" and "tiaohou" not in result:
        try:
            from bazi_pro.core.tiaohou import lookup_tiaohou
            day_master = result.get("day_master", "") or result.get("validation", {}).get("day_master", "")
            pillars = result.get("pillars", []) or result.get("shishen", {}).get("pillars", [])
            bazi_parts = [p.get("gan", "") + p.get("zhi", "") for p in pillars]
            month_zhi = bazi_parts[1][1] if len(bazi_parts) >= 2 and len(bazi_parts[1]) >= 2 else ""
            if day_master and month_zhi:
                result["tiaohou"] = lookup_tiaohou(day_master, month_zhi)
        except Exception:
            pass

    narration = {}
    if isinstance(result, dict) and result.get("status") == "completed":
        try:
            from bazi_pro.narrator import narrate_analysis
            narration = narrate_analysis(result)
        except Exception:
            pass

    effective_status = record["status"]
    effective_error = None
    if isinstance(result, dict):
        if "status" in result:
            effective_status = result["status"]
        if "error" in result:
            effective_error = result["error"]

    response = {
        "analysis_id": analysis_id,
        "status": effective_status,
        "created_at": record.get("created_at"),
        "completed_at": record.get("completed_at"),
        "day_master": record.get("day_master", ""),
        "pattern": record.get("pattern", ""),
        "yongshen": record.get("yongshen", ""),
        "result": result,
        "narration": narration,
    }
    if effective_error:
        response["error"] = effective_error
    return JSONResponse(response)


@router.get("/api/v2/analysis/{analysis_id}/stream")
async def api_v2_stream(analysis_id: str, _auth=Depends(verify_api_key)):
    queue: asyncio.Queue = asyncio.Queue()

    async with lock:
        buffered = buffers.get(analysis_id, [])
        for msg in buffered:
            await queue.put(msg)

        if analysis_id not in subscribers:
            subscribers[analysis_id] = []
        subscribers[analysis_id].append(queue)

    already_done = any(m.startswith("event: done") or m.startswith("event: analysis-error") for m in buffered)

    async def event_generator():
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield msg
                    if msg.startswith("event: done") or msg.startswith("event: analysis-error"):
                        break
                except asyncio.TimeoutError:
                    if already_done:
                        break
                    yield ": keepalive\n\n"
        finally:
            async with lock:
                subs = subscribers.get(analysis_id, [])
                if queue in subs:
                    subs.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _validate_analysis_id(analysis_id: str) -> bool:
    import re
    return bool(re.compile(r'^ana_[0-9a-f]{8,24}$').match(analysis_id))


async def _background_analyze_v2(analysis_id: str, mcp_json: dict, detail_level: str, school: str = 'ziping', *, skip_llm_overview: bool = False):
    from server.analysis import run_analysis
    for key in list(mcp_json.keys()):
        if mcp_json[key] is None:
            mcp_json[key] = ''

    v2_active_ids.add(analysis_id)
    try:
        # 等待 SSE 客户端连接（最多 2 秒），避免首个进度事件丢失
        for _ in range(20):
            async with lock:
                if subscribers.get(analysis_id):
                    break
            await asyncio.sleep(0.1)

        await broadcast(analysis_id, "progress", {
            "step": "0", "name": "启动分析", "status": "running", "message": "正在初始化..."
        })

        result = await run_analysis(mcp_json, analysis_id, detail_level, school, skip_llm_overview=skip_llm_overview)

        if result is None:
            result = {"status": "failed", "error": "分析引擎返回空结果"}

        await update_analysis_result(analysis_id, result)

        actual_status = result.get('status', 'completed')
        if actual_status == 'failed':
            error_msg = result.get('error', '分析失败')
            await broadcast(analysis_id, "analysis-error", {"message": error_msg})
        elif actual_status == 'invalid_input':
            errors = result.get('errors', [])
            error_msg = '; '.join(errors) if isinstance(errors, list) and errors else result.get('error', '输入数据无效')
            await broadcast(analysis_id, "analysis-error", {"message": error_msg})
        else:
            await broadcast(analysis_id, "done", {"analysis_id": analysis_id})

    except Exception as e:
        import traceback as _tb
        logger.error("V2 analysis failed for %s: %s\n%s", analysis_id, e, _tb.format_exc())
        client_msg = str(e) or type(e).__name__
        await update_analysis_status(analysis_id, "failed", client_msg)
        await broadcast(analysis_id, "analysis-error", {"message": client_msg})
    finally:
        v2_active_ids.discard(analysis_id)
        for _ in range(10):
            async with lock:
                subs = subscribers.get(analysis_id, [])
                if not subs:
                    subscribers.pop(analysis_id, None)
                    buffers.pop(analysis_id, None)
                    break
            await asyncio.sleep(0.5)
        else:
            async with lock:
                subscribers.pop(analysis_id, None)
                buffers.pop(analysis_id, None)
