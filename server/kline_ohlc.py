"""K线 OHLC 模型 — 四维度运势评分（事业/财运/感情/健康）

将单值折线图升级为股票 K 线四值模型，每年有四个维度的独立评分。
"""

from bazi_pro import GAN_WUXING, ZHI_WUXING
from bazi_pro.paipan import DIZHI, TIANGAN

DIMENSION_WEIGHTS = {
    "career": {"yongshen_gan": 25, "yongshen_zhi": 20, "jishen_gan": -20, "jishen_zhi": -15},
    "wealth": {"yongshen_gan": 20, "yongshen_zhi": 15, "jishen_gan": -25, "jishen_zhi": -20},
    "love": {"yongshen_gan": 15, "yongshen_zhi": 20, "jishen_gan": -10, "jishen_zhi": -15},
    "health": {"yongshen_gan": 10, "yongshen_zhi": 15, "jishen_gan": -15, "jishen_zhi": -20},
}


def score_liunian_ohlc(dayun_list: list, yongshen_wx: str, jishen_wx,
                       xishen_wx, day_master: str, birth_year: int,
                       qiyun_age: int = 5) -> list[dict]:
    """计算流年 OHLC 四维度评分。

    Returns:
        每年一条记录: {age, year, gan_zhi, career, wealth, love, health, overall}
    """
    if not birth_year:
        return []

    jishen_set = set(jishen_wx) if isinstance(jishen_wx, list) else {jishen_wx}
    xishen_set = set(xishen_wx) if isinstance(xishen_wx, list) else {xishen_wx}

    results = []
    for age in range(1, 101):
        year = birth_year + age - 1
        gan_idx = (year - 4) % 10
        zhi_idx = (year - 4) % 12
        gan = TIANGAN[gan_idx]
        zhi = DIZHI[zhi_idx]
        gan_wx = GAN_WUXING.get(gan, "")
        zhi_wx = ZHI_WUXING.get(zhi, "")

        dims = {}
        for dim, weights in DIMENSION_WEIGHTS.items():
            score = 50
            if gan_wx == yongshen_wx:
                score += weights["yongshen_gan"]
            elif gan_wx in xishen_set:
                score += weights["yongshen_gan"] // 2
            elif gan_wx in jishen_set:
                score += weights["jishen_gan"]

            if zhi_wx == yongshen_wx:
                score += weights["yongshen_zhi"]
            elif zhi_wx in xishen_set:
                score += weights["yongshen_zhi"] // 2
            elif zhi_wx in jishen_set:
                score += weights["jishen_zhi"]

            dims[dim] = max(0, min(100, score))

        overall = round(sum(dims.values()) / 4)

        results.append({
            "age": age,
            "year": year,
            "gan_zhi": f"{gan}{zhi}",
            "career": dims["career"],
            "wealth": dims["wealth"],
            "love": dims["love"],
            "health": dims["health"],
            "overall": overall,
        })

    return results
