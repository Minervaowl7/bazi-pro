from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class BaziAnalysisRequest(BaseModel):
    性别: str = Field(..., description="性别", min_length=1)
    八字: str = Field(..., description="四柱八字，空格分隔", min_length=1)
    日主: str = Field(..., description="日主天干", min_length=1)
    detail_level: str = Field(default="standard", pattern="^(standard|detailed|brief)$")
    阳历: Optional[str] = Field(default="", description="阳历日期")
    农历: Optional[str] = Field(default="", description="农历日期")
    生肖: Optional[str] = Field(default="", description="生肖")
    大运: Optional[list] = Field(default=None, description="大运列表")


class AnalysisResponse(BaseModel):
    run_id: str
    status: str
    message: Optional[str] = None


class StatusResponse(BaseModel):
    status: str
    run_id: Optional[str] = None
    error: Optional[str] = None


class ValidationResult(BaseModel):
    valid: bool
    missing_fields: list[str]
    empty_fields: list[str]
    bazi: str
    day_master: str
    gender: str


class DelingResult(BaseModel):
    status: str
    score: int


class WangshuaiResult(BaseModel):
    verdict: str
    deling_score: int
    dedi_score: float
    deshi_score: float
    is_weak: bool
    is_strong: bool
    is_extreme_weak: bool
    is_extreme_strong: bool


class PatternResult(BaseModel):
    pattern: str
    layer: int
    type: str
    confidence: float
    reason: str
    yongshen_direction: str
    candidates: list[dict]


class YongshenResult(BaseModel):
    yongshen: str
    yongshen_gan: str
    xishen: list[str]
    xishen_gan: list[str]
    jishen: list[str]
    jishen_gan: list[str]
    confidence: float
    pattern_basis: str
    note: str


class ElementForcesResult(BaseModel):
    raw: dict[str, float]
    percent: dict[str, float]
    total: float


class PillarResult(BaseModel):
    position: str
    gan: str
    zhi: str
    wuxing_gan: str
    wuxing_zhi: str
    shishen: str
    canggan: list[dict]


class FullAnalysisResult(BaseModel):
    status: str
    day_master: str
    deling: DelingResult
    dedi: dict
    deshi: dict
    wangshuai: WangshuaiResult
    element_forces: ElementForcesResult
    relations: list[dict]
    pattern: PatternResult
    yongshen: YongshenResult
    pillars: list[PillarResult]
