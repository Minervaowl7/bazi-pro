from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

router = APIRouter()


class ZiweiChartRequest(BaseModel):
    solar_date: str = Field(..., description="阳历出生日期，格式 YYYY-MM-DD")
    hour: int = Field(..., ge=0, le=23, description="出生小时(0-23)")
    gender: int = Field(default=1, description="性别：1=男，0=女")


class ZiweiHoroscopeRequest(BaseModel):
    solar_date: str = Field(..., description="阳历出生日期，格式 YYYY-MM-DD")
    hour: int = Field(..., ge=0, le=23, description="出生小时(0-23)")
    gender: int = Field(default=1, description="性别：1=男，0=女")
    query_date: Optional[str] = Field(default=None, description="查询日期，格式 YYYY-MM-DD，默认今天")


class ZiweiPalaceRequest(BaseModel):
    solar_date: str = Field(..., description="阳历出生日期，格式 YYYY-MM-DD")
    hour: int = Field(..., ge=0, le=23, description="出生小时(0-23)")
    gender: int = Field(default=1, description="性别：1=男，0=女")
    palace_name: str = Field(default="命宫", description="宫位名称")


@router.post("/api/v2/ziwei/chart")
async def api_v2_ziwei_chart(payload: ZiweiChartRequest):
    from server.ziwei import get_ziwei_chart

    result = await asyncio.to_thread(
        get_ziwei_chart,
        solar_date=payload.solar_date,
        hour=payload.hour,
        gender=payload.gender,
    )
    if "error" in result:
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


@router.post("/api/v2/ziwei/horoscope")
async def api_v2_ziwei_horoscope(payload: ZiweiHoroscopeRequest):
    from server.ziwei import get_ziwei_horoscope

    result = await asyncio.to_thread(
        get_ziwei_horoscope,
        solar_date=payload.solar_date,
        hour=payload.hour,
        gender=payload.gender,
        query_date=payload.query_date,
    )
    if "error" in result:
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


@router.post("/api/v2/ziwei/palace")
async def api_v2_ziwei_palace(payload: ZiweiPalaceRequest):
    from server.ziwei import analyze_ziwei_palace

    result = await asyncio.to_thread(
        analyze_ziwei_palace,
        solar_date=payload.solar_date,
        hour=payload.hour,
        gender=payload.gender,
        palace_name=payload.palace_name,
    )
    if "error" in result:
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)
