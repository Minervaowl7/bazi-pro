"""每日/每月运势计算 — 基于日主与流日/流月五行生克的确定性运势"""

from datetime import date

from bazi_pro import GAN_WUXING, ZHI_WUXING
from bazi_pro.paipan import DIZHI, TIANGAN, paipan_from_datetime

WUXING_SHENGKE = {
    ("木", "火"): "生", ("火", "土"): "生", ("土", "金"): "生",
    ("金", "水"): "生", ("水", "木"): "生",
    ("木", "土"): "克", ("土", "水"): "克", ("水", "火"): "克",
    ("火", "金"): "克", ("金", "木"): "克",
}

DIMENSIONS = ["整体", "事业", "财运", "感情", "健康", "社交"]

LEVEL_MAP = {
    range(80, 101): "大吉",
    range(65, 80): "吉",
    range(50, 65): "中吉",
    range(35, 50): "平",
    range(20, 35): "小凶",
    range(0, 20): "凶",
}


def _score_to_level(score: int) -> str:
    for r, level in LEVEL_MAP.items():
        if score in r:
            return level
    return "平"


def _get_today_pillars(d: date) -> dict:
    """使用排盘引擎获取指定日期的四柱干支（中午12点，性别男）"""
    solar_str = f"{d.year:04d}-{d.month:02d}-{d.day:02d} 12:00"
    result = paipan_from_datetime(solar_str, "男")
    if result.get("status") != "completed":
        gan_idx = (d.year - 4) % 10
        zhi_idx = (d.year - 4) % 12
        return {
            "year": (TIANGAN[gan_idx], DIZHI[zhi_idx]),
            "month": ("", ""),
            "day": ("", ""),
        }
    pillars = result.get("pillars", [])
    if not pillars or len(pillars) < 3:
        return {"year": ("", ""), "month": ("", ""), "day": ("", "")}
    return {
        "year": (pillars[0].get("gan", ""), pillars[0].get("zhi", "")),
        "month": (pillars[1].get("gan", ""), pillars[1].get("zhi", "")),
        "day": (pillars[2].get("gan", ""), pillars[2].get("zhi", "")),
    }


def _get_day_ganzhi(d: date) -> tuple[str, str]:
    """根据日期计算日柱干支，使用排盘引擎"""
    pillars = _get_today_pillars(d)
    return pillars["day"]


def _get_month_ganzhi(year: int, month: int) -> tuple[str, str]:
    """计算某月的天干地支，使用排盘引擎（取该月15日）"""
    d = date(year, month, 15)
    pillars = _get_today_pillars(d)
    return pillars["month"]


def _calc_dimension_scores(day_master_wx: str, gan_wx: str, zhi_wx: str,
                           yongshen_wx: str, jishen_wx: list[str]) -> dict[str, int]:
    """计算六维度运势分数"""
    base = 50
    scores = {}

    overall_mod = 0
    if gan_wx == yongshen_wx:
        overall_mod += 20
    elif gan_wx in jishen_wx:
        overall_mod -= 20
    if zhi_wx == yongshen_wx:
        overall_mod += 15
    elif zhi_wx in jishen_wx:
        overall_mod -= 15

    rel_gan = WUXING_SHENGKE.get((day_master_wx, gan_wx), "")
    rel_zhi = WUXING_SHENGKE.get((day_master_wx, zhi_wx), "")

    scores["整体"] = max(0, min(100, base + overall_mod))
    scores["事业"] = max(0, min(100, base + overall_mod + (5 if rel_gan == "克" else -3 if rel_gan == "生" else 0)))
    scores["财运"] = max(0, min(100, base + overall_mod + (8 if gan_wx in jishen_wx and rel_gan == "克" else 0)))
    scores["感情"] = max(0, min(100, base + (10 if rel_zhi == "生" else -5 if rel_zhi == "克" else 0)))
    scores["健康"] = max(0, min(100, base + (-10 if gan_wx in jishen_wx else 5 if gan_wx == yongshen_wx else 0)))
    scores["社交"] = max(0, min(100, base + (8 if WUXING_SHENGKE.get((gan_wx, day_master_wx)) == "生" else 0)))

    return scores


def calc_daily_fortune(day_master: str, yongshen_wx: str,
                       jishen_wx: list[str], target_date: date | None = None) -> dict:
    """计算某日运势"""
    if not target_date:
        target_date = date.today()

    day_master_wx = GAN_WUXING.get(day_master, "")
    if not day_master_wx:
        return {"error": "日主无效"}

    gan, zhi = _get_day_ganzhi(target_date)
    gan_wx = GAN_WUXING.get(gan, "")
    zhi_wx = ZHI_WUXING.get(zhi, "")

    scores = _calc_dimension_scores(day_master_wx, gan_wx, zhi_wx, yongshen_wx, jishen_wx)

    return {
        "date": target_date.isoformat(),
        "gan_zhi": f"{gan}{zhi}",
        "dimensions": {dim: {"score": s, "level": _score_to_level(s)} for dim, s in scores.items()},
        "overall_level": _score_to_level(scores["整体"]),
    }


def calc_monthly_fortune(day_master: str, yongshen_wx: str,
                         jishen_wx: list[str], year: int, month: int) -> dict:
    """计算某月运势"""
    day_master_wx = GAN_WUXING.get(day_master, "")
    if not day_master_wx:
        return {"error": "日主无效"}

    gan, zhi = _get_month_ganzhi(year, month)
    gan_wx = GAN_WUXING.get(gan, "")
    zhi_wx = ZHI_WUXING.get(zhi, "")

    scores = _calc_dimension_scores(day_master_wx, gan_wx, zhi_wx, yongshen_wx, jishen_wx)

    return {
        "year": year,
        "month": month,
        "gan_zhi": f"{gan}{zhi}",
        "dimensions": {dim: {"score": s, "level": _score_to_level(s)} for dim, s in scores.items()},
        "overall_level": _score_to_level(scores["整体"]),
    }
