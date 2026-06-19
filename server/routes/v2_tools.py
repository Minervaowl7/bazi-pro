from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from server.db import list_analyses
from server.deps import error_response, verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter()


class HehunRequest(BaseModel):
    八字A: str = Field(description="甲方八字，空格分隔四柱")
    日主A: str = Field(description="甲方日主天干")
    性别A: str = Field(description="甲方性别")
    八字B: str = Field(description="乙方八字，空格分隔四柱")
    日主B: str = Field(description="乙方日主天干")
    性别B: str = Field(description="乙方性别")


class ReverseLookupRequest(BaseModel):
    day_pillar: str = Field(description="日柱干支，如 '戊辰'")
    start_year: int = Field(default=2020)
    end_year: int = Field(default=2030)


@router.post("/api/v2/hehun")
async def api_v2_hehun(payload: HehunRequest, _auth=Depends(verify_api_key)):
    try:
        from bazi_pro.compare_engine import CompareEngine

        from bazi_pro.core import full_analysis
    except ImportError:
        return error_response(503, "MODULE_NOT_AVAILABLE", "合婚模块不可用")

    try:
        chart_a = full_analysis({"八字": payload.八字A, "日主": payload.日主A, "性别": payload.性别A})
        chart_b = full_analysis({"八字": payload.八字B, "日主": payload.日主B, "性别": payload.性别B})

        engine = CompareEngine()
        engine.load_chart_a_dict(chart_a)
        engine.load_chart_b_dict(chart_b)
        result = engine.compare()

        from dataclasses import asdict
        return JSONResponse({"status": "completed", "result": asdict(result)})
    except Exception as e:
        logger.error("Hehun analysis failed: %s", e)
        return error_response(500, "ANALYSIS_ERROR", f"合婚分析失败: {str(e)}")


@router.post("/api/v2/reverse-lookup")
async def api_v2_reverse_lookup(payload: ReverseLookupRequest, _auth=Depends(verify_api_key)):
    from server.reverse_lookup import reverse_lookup_day_pillar

    results = reverse_lookup_day_pillar(payload.day_pillar, payload.start_year, payload.end_year)
    return JSONResponse({"dates": results, "day_pillar": payload.day_pillar})


@router.get("/api/v2/cities")
async def api_v2_cities():
    from server.true_solar_time import CHINA_CITIES
    cities = [{"name": name, "longitude": coords[0], "latitude": coords[1]}
              for name, coords in CHINA_CITIES.items()]
    return JSONResponse(content={"cities": cities})


@router.get("/api/v2/history")
async def api_v2_history(page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), _auth=Depends(verify_api_key)):
    data = await list_analyses(page=page, page_size=page_size)
    return JSONResponse(data)
