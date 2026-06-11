from __future__ import annotations

import json
import logging
from datetime import date as _date

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from server.db import get_analysis
from server.deps import error_response

logger = logging.getLogger("bazi-pro")

router = APIRouter()


@router.get("/api/v2/fortune/daily/{analysis_id}")
async def api_v2_daily_fortune(analysis_id: str):
    from server.daily_fortune import calc_daily_fortune

    analysis = await get_analysis(analysis_id)
    if not analysis:
        return error_response(404, "NOT_FOUND", "分析不存在")

    result = analysis.get("full_result", {})
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}
    if not isinstance(result, dict):
        result = {}

    day_master = result.get("day_master", "") or result.get("validation", {}).get("day_master", "")
    yongshen_data = result.get("yongshen", {})

    yongshen_wx = yongshen_data.get("yongshen", "")
    jishen_wx = yongshen_data.get("jishen", [])
    if isinstance(jishen_wx, str):
        jishen_wx = [jishen_wx] if jishen_wx else []

    if not day_master:
        return error_response(400, "INVALID", "缺少日主数据")

    fortune = calc_daily_fortune(day_master, yongshen_wx, jishen_wx, _date.today())
    return JSONResponse(fortune)


@router.get("/api/v2/fortune/monthly/{analysis_id}")
async def api_v2_monthly_fortune(analysis_id: str, year: int = Query(default=0), month: int = Query(default=0)):
    from server.daily_fortune import calc_monthly_fortune

    if not year:
        year = _date.today().year
    if not month:
        month = _date.today().month

    analysis = await get_analysis(analysis_id)
    if not analysis:
        return error_response(404, "NOT_FOUND", "分析不存在")

    result = analysis.get("full_result", {})
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}
    if not isinstance(result, dict):
        result = {}

    day_master = result.get("day_master", "") or result.get("validation", {}).get("day_master", "")
    yongshen_data = result.get("yongshen", {})

    yongshen_wx = yongshen_data.get("yongshen", "")
    jishen_wx = yongshen_data.get("jishen", [])
    if isinstance(jishen_wx, str):
        jishen_wx = [jishen_wx] if jishen_wx else []

    if not day_master:
        return error_response(400, "INVALID", "缺少日主数据")

    fortune = calc_monthly_fortune(day_master, yongshen_wx, jishen_wx, year, month)
    return JSONResponse(fortune)


@router.get("/api/v2/dayun-liunian/{analysis_id}")
async def api_v2_dayun_liunian(analysis_id: str):
    from server.dayun_score import score_dayun, score_liunian

    record = await get_analysis(analysis_id)
    if not record:
        return error_response(404, "NOT_FOUND", "分析记录不存在")

    result = record.get("full_result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}

    if not isinstance(result, dict) or result.get("status") != "completed":
        return error_response(400, "ANALYSIS_NOT_COMPLETED", "分析尚未完成，无法获取大运流年评分")

    dayun_list = result.get("dayun", [])
    qiyun_age = result.get("qiyun_age", 5)

    yongshen_info = result.get("yongshen", {})
    if isinstance(yongshen_info, dict):
        yongshen_wx = yongshen_info.get("yongshen", "")
        jishen_wx = yongshen_info.get("jishen", [])
        xishen_wx = yongshen_info.get("xishen", [])
        if isinstance(jishen_wx, str):
            jishen_wx = [jishen_wx] if jishen_wx else []
        if isinstance(xishen_wx, str):
            xishen_wx = [xishen_wx] if xishen_wx else []
    else:
        if isinstance(yongshen_info, list) and yongshen_info:
            yongshen_wx = str(yongshen_info[0]) if yongshen_info[0] else ""
        elif isinstance(yongshen_info, str):
            yongshen_wx = yongshen_info
        else:
            yongshen_wx = str(yongshen_info) if yongshen_info else ""
        jishen_wx = []
        xishen_wx = []

    day_master = result.get("day_master", "") or result.get("validation", {}).get("day_master", "")
    if not day_master:
        day_master = record.get("day_master", "")

    birth_json = record.get("birth_json", {})
    if isinstance(birth_json, str):
        try:
            birth_json = json.loads(birth_json)
        except (json.JSONDecodeError, TypeError):
            birth_json = {}

    birth_year = None
    solar = birth_json.get("阳历", "")
    if solar:
        try:
            birth_year = int(solar.split("-")[0])
        except (ValueError, IndexError):
            birth_year = None

    if not dayun_list or not yongshen_wx or not birth_year:
        return JSONResponse({
            "analysis_id": analysis_id,
            "dayun_scores": [],
            "liunian_scores": [],
            "warning": "缺少大运、用神或出生年份数据，无法评分",
        })

    dayun_scores = score_dayun(dayun_list, yongshen_wx, jishen_wx, day_master)
    liunian_scores = score_liunian(
        dayun_list, yongshen_wx, jishen_wx, xishen_wx, day_master,
        birth_year, qiyun_age,
    )

    # OHLC 四维度评分（事业/财运/感情/健康）
    ohlc_scores = []
    try:
        from server.kline_ohlc import score_liunian_ohlc
        ohlc_scores = score_liunian_ohlc(
            dayun_list, yongshen_wx, jishen_wx, xishen_wx, day_master,
            birth_year, qiyun_age,
        )
    except Exception as exc:
        logger.warning("OHLC scoring failed: %s", exc)

    return JSONResponse({
        "analysis_id": analysis_id,
        "dayun_scores": dayun_scores,
        "liunian_scores": liunian_scores,
        "ohlc_scores": ohlc_scores,
    })
