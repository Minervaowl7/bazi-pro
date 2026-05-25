from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

TIANGAN = set('甲乙丙丁戊己庚辛壬癸')
DIZHI = set('子丑寅卯辰巳午未申酉戌亥')
BAZI_PATTERN = re.compile(
    r'^[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]'
    r'\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]'
    r'\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]'
    r'\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]$'
)


class BaziPillars(BaseModel):
    year: str = Field(..., min_length=2, max_length=2, description="年柱，如 壬午")
    month: str = Field(..., min_length=2, max_length=2, description="月柱，如 乙巳")
    day: str = Field(..., min_length=2, max_length=2, description="日柱，如 丁亥")
    hour: str = Field(..., min_length=2, max_length=2, description="时柱，如 癸卯")

    @field_validator('year', 'month', 'day', 'hour')
    @classmethod
    def validate_pillar(cls, v: str) -> str:
        if len(v) != 2:
            raise ValueError(f'柱 "{v}" 必须为2字符（天干+地支）')
        if v[0] not in TIANGAN:
            raise ValueError(f'天干 "{v[0]}" 不合法，必须为 甲乙丙丁戊己庚辛壬癸 之一')
        if v[1] not in DIZHI:
            raise ValueError(f'地支 "{v[1]}" 不合法，必须为 子丑寅卯辰巳午未申酉戌亥 之一')
        return v

    def to_bazi_string(self) -> str:
        return f"{self.year} {self.month} {self.day} {self.hour}"


class DayunItem(BaseModel):
    age_range: str = Field(default="", description="年龄段，如 3-12")
    gan: str = Field(..., min_length=1, max_length=1, description="大运天干")
    zhi: str = Field(..., min_length=1, max_length=1, description="大运地支")

    @field_validator('gan')
    @classmethod
    def validate_gan(cls, v: str) -> str:
        if v not in TIANGAN:
            raise ValueError(f'大运天干 "{v}" 不合法')
        return v

    @field_validator('zhi')
    @classmethod
    def validate_zhi(cls, v: str) -> str:
        if v not in DIZHI:
            raise ValueError(f'大运地支 "{v}" 不合法')
        return v


class BaziAnalysisRequest(BaseModel):
    性别: str = Field(..., description="性别", min_length=1)
    八字: str = Field(..., description="四柱八字，空格分隔", min_length=1)
    日主: str = Field(..., description="日主天干", min_length=1)
    detail_level: str = Field(default="standard", pattern="^(standard|detailed|brief)$")
    阳历: Optional[str] = Field(default="", description="阳历日期")
    农历: Optional[str] = Field(default="", description="农历日期")
    生肖: Optional[str] = Field(default="", description="生肖")
    大运: Optional[list[DayunItem]] = Field(default=None, description="大运列表", max_length=12)

    @field_validator('八字')
    @classmethod
    def validate_bazi(cls, v: str) -> str:
        v = v.strip()
        if not BAZI_PATTERN.match(v):
            raise ValueError(
                '八字格式不合法，必须为4组天干地支以空格分隔，如 "壬午 乙巳 丁亥 癸卯"'
            )
        return v

    @field_validator('日主')
    @classmethod
    def validate_day_master(cls, v: str) -> str:
        v = v.strip()
        if v not in TIANGAN:
            raise ValueError(f'日主 "{v}" 不合法，必须为 甲乙丙丁戊己庚辛壬癸 之一')
        return v

    @field_validator('性别')
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v not in ('男', '女', '其他'):
            raise ValueError('性别必须为 男/女/其他 之一')
        return v


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
