"""
紫微斗数星曜解读模块

实现 14 主星在不同宫位的解读。
"""

from __future__ import annotations

from typing import Any

from bazi_pro.core.ziwei.constants import STAR_NATURE, StarNature
from bazi_pro.core.ziwei.utils import get_palace_by_name, get_palace_major_stars


def get_star_nature(star_name: str) -> StarNature | None:
    """获取星曜性质

    Args:
        star_name: 星曜名称

    Returns:
        星曜性质，未找到返回 None
    """
    return STAR_NATURE.get(star_name)


def analyze_star_in_palace(star_name: str, palace_name: str, brightness: str = "") -> dict[str, Any]:
    """分析星曜在宫位的影响

    Args:
        star_name: 星曜名称
        palace_name: 宫位名称
        brightness: 亮度（bright/normal/dim）

    Returns:
        {
            "star": "星曜名称",
            "palace": "宫位名称",
            "brightness": "亮度",
            "nature": "星曜性质",
            "influence": "宫位影响",
            "description": "综合描述"
        }
    """
    star_nature = get_star_nature(star_name)
    if not star_nature:
        return {"error": f"未找到星曜: {star_name}"}

    # 获取宫位影响
    influence = star_nature.palace_effects.get(palace_name, "暂无解读")

    # 根据亮度调整描述
    brightness_desc = ""
    if brightness == "bright":
        brightness_desc = "（庙旺，吉力倍增）"
    elif brightness == "dim":
        brightness_desc = "（落陷，吉力减弱）"

    # 综合描述
    description = f"{star_name}入{palace_name}{brightness_desc}：{influence}"

    return {
        "star": star_name,
        "palace": palace_name,
        "brightness": brightness,
        "nature": star_nature.xingqing,
        "influence": influence,
        "description": description,
    }


def analyze_ming_palace(chart: dict[str, Any]) -> dict[str, Any]:
    """分析命宫主星

    Args:
        chart: iztro-py 排盘结果

    Returns:
        {
            "major_stars": [{"star": "星名", "brightness": "亮度", "analysis": "分析"}, ...],
            "summary": "命宫主星综合分析"
        }
    """
    # 获取命宫
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return {"error": "未找到命宫"}

    # 分析命宫主星
    major_stars = []
    for star in ming_palace.get("majorStars", []):
        star_name = star.get("name", "")
        brightness = star.get("brightness", "")

        analysis = analyze_star_in_palace(star_name, "命宫", brightness)
        major_stars.append(analysis)

    # 综合分析
    summary = "命宫主星："
    for star in major_stars:
        summary += f"\n- {star.get('description', '')}"

    return {
        "major_stars": major_stars,
        "summary": summary,
    }


def analyze_palace(chart: dict[str, Any], palace_name: str) -> dict[str, Any]:
    """分析指定宫位

    Args:
        chart: iztro-py 排盘结果
        palace_name: 宫位名称

    Returns:
        {
            "palace": "宫位名称",
            "major_stars": [{"star": "星名", "brightness": "亮度", "analysis": "分析"}, ...],
            "summary": "宫位主星综合分析"
        }
    """
    # 获取宫位
    palace = get_palace_by_name(chart, palace_name)
    if not palace:
        return {"error": f"未找到{palace_name}"}

    # 分析宫位主星
    major_stars = []
    for star in palace.get("majorStars", []):
        star_name = star.get("name", "")
        brightness = star.get("brightness", "")

        analysis = analyze_star_in_palace(star_name, palace_name, brightness)
        major_stars.append(analysis)

    # 综合分析
    summary = f"{palace_name}主星："
    for star in major_stars:
        summary += f"\n- {star.get('description', '')}"

    return {
        "palace": palace_name,
        "major_stars": major_stars,
        "summary": summary,
    }
