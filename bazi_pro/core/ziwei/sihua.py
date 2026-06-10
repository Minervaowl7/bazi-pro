"""
紫微斗数四化分析模块

实现本命、大限、流年、流月四化分析。
数据来源：《紫微斗数全书》
"""

from __future__ import annotations

from typing import Any

from bazi_pro.core.ziwei.constants import SI_HUA_TABLE


def get_sihua_by_stem(stem: str) -> dict[str, str]:
    """根据天干获取四化

    Args:
        stem: 天干（甲/乙/丙/...）

    Returns:
        {"化禄": "星名", "化权": "星名", "化科": "星名", "化忌": "星名"}
    """
    return SI_HUA_TABLE.get(stem, {})


def build_star_sihua_map(stem: str) -> dict[str, str]:
    """构建星曜四化反向映射

    Args:
        stem: 天干

    Returns:
        {"星名": "化类型"} 例如 {"廉贞": "化禄", "破军": "化权", ...}
    """
    sihua = get_sihua_by_stem(stem)
    return {v: k for k, v in sihua.items()}


def get_year_stem(year: int) -> str:
    """根据公历年获取年柱天干

    Args:
        year: 公历年

    Returns:
        天干
    """
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    return stems[(year - 4) % 10]


def get_year_branch(year: int) -> str:
    """根据公历年获取年柱地支

    Args:
        year: 公历年

    Returns:
        地支
    """
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    return branches[(year - 4) % 12]


def analyze_benming_sihua(chart: dict[str, Any]) -> dict[str, Any]:
    """分析本命四化

    Args:
        chart: iztro-py 排盘结果

    Returns:
        {
            "sihua": {"化禄": "星名", ...},
            "star_sihua_map": {"星名": "化类型", ...},
            "palace_sihua": {"宫位名": ["化禄", "化权", ...], ...}
        }
    """
    # 获取年干
    year_stem = chart.get("yearStem", "")
    if not year_stem:
        return {"error": "无法获取年干"}

    # 获取四化
    sihua = get_sihua_by_stem(year_stem)
    star_sihua_map = build_star_sihua_map(year_stem)

    # 分析各宫位四化
    palace_sihua: dict[str, list[str]] = {}
    for palace in chart.get("palaces", []):
        palace_name = palace.get("name", "")
        major_stars = [s.get("name", "") for s in palace.get("majorStars", [])]

        # 检查该宫位主星是否有四化
        sihua_in_palace = []
        for star in major_stars:
            if star in star_sihua_map:
                sihua_in_palace.append(star_sihua_map[star])

        if sihua_in_palace:
            palace_sihua[palace_name] = sihua_in_palace

    return {
        "sihua": sihua,
        "star_sihua_map": star_sihua_map,
        "palace_sihua": palace_sihua,
    }


def analyze_daxian_sihua(chart: dict[str, Any], daxian_index: int) -> dict[str, Any]:
    """分析大限四化

    Args:
        chart: iztro-py 排盘结果
        daxian_index: 大限索引（0-11）

    Returns:
        {
            "stem": "大限天干",
            "sihua": {"化禄": "星名", ...},
            "star_sihua_map": {"星名": "化类型", ...},
        }
    """
    # 获取大限宫位
    palaces = chart.get("palaces", [])
    if daxian_index >= len(palaces):
        return {"error": "大限索引超出范围"}

    daxian_palace = palaces[daxian_index]

    # 获取大限天干
    daxian_stem = daxian_palace.get("heavenlyStem", "")
    if not daxian_stem:
        return {"error": "无法获取大限天干"}

    # 获取四化
    sihua = get_sihua_by_stem(daxian_stem)
    star_sihua_map = build_star_sihua_map(daxian_stem)

    return {
        "stem": daxian_stem,
        "sihua": sihua,
        "star_sihua_map": star_sihua_map,
    }


def analyze_liunian_sihua(year: int) -> dict[str, Any]:
    """分析流年四化

    Args:
        year: 流年

    Returns:
        {
            "stem": "流年天干",
            "branch": "流年地支",
            "sihua": {"化禄": "星名", ...},
            "star_sihua_map": {"星名": "化类型", ...},
        }
    """
    # 获取流年天干地支
    year_stem = get_year_stem(year)
    year_branch = get_year_branch(year)

    # 获取四化
    sihua = get_sihua_by_stem(year_stem)
    star_sihua_map = build_star_sihua_map(year_stem)

    return {
        "stem": year_stem,
        "branch": year_branch,
        "sihua": sihua,
        "star_sihua_map": star_sihua_map,
    }


def analyze_sihua(chart: dict[str, Any], query_year: int | None = None) -> dict[str, Any]:
    """综合四化分析

    Args:
        chart: iztro-py 排盘结果
        query_year: 查询年份（可选）

    Returns:
        {
            "benming": 本命四化,
            "daxian": 大限四化列表,
            "liunian": 流年四化（如果指定了年份）
        }
    """
    result = {
        "benming": analyze_benming_sihua(chart),
        "daxian": [],
    }

    # 分析 12 个大限
    for i in range(12):
        daxian = analyze_daxian_sihua(chart, i)
        result["daxian"].append(daxian)

    # 如果指定了查询年份，分析流年四化
    if query_year:
        result["liunian"] = analyze_liunian_sihua(query_year)

    return result
