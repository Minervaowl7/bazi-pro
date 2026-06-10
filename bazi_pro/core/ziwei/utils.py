"""
紫微斗数工具函数

包含三方四正、夹宫、庙旺判断等辅助函数。
"""

from __future__ import annotations

from typing import Any

from bazi_pro.core.ziwei.constants import SAN_FANG_OFFSETS, JIA_OFFSETS, BRANCH_INDEX


def get_palace_by_name(chart: dict[str, Any], palace_name: str) -> dict[str, Any] | None:
    """根据宫位名称获取宫位数据

    Args:
        chart: iztro-py 排盘结果
        palace_name: 宫位名称

    Returns:
        宫位数据，未找到返回 None
    """
    for palace in chart.get("palaces", []):
        if palace.get("name") == palace_name:
            return palace
    return None


def get_palace_by_branch(chart: dict[str, Any], branch: str) -> dict[str, Any] | None:
    """根据地支获取宫位数据

    Args:
        chart: iztro-py 排盘结果
        branch: 地支

    Returns:
        宫位数据，未找到返回 None
    """
    for palace in chart.get("palaces", []):
        if palace.get("earthlyBranch") == branch:
            return palace
    return None


def get_san_fang_palaces(chart: dict[str, Any], ming_branch: str) -> list[dict[str, Any]]:
    """获取三方四正宫位（命宫 + 财帛 + 官禄 + 迁移）

    Args:
        chart: iztro-py 排盘结果
        ming_branch: 命宫地支

    Returns:
        三方四正宫位列表
    """
    # 获取命宫索引
    ming_idx = BRANCH_INDEX.get(ming_branch, 0)

    # 计算三方四正宫位索引
    san_fang_indices = [(ming_idx + offset) % 12 for offset in SAN_FANG_OFFSETS]

    # 获取宫位数据
    palaces = chart.get("palaces", [])
    result = []
    for idx in san_fang_indices:
        # 查找对应地支的宫位
        target_branch = list(BRANCH_INDEX.keys())[idx]
        palace = get_palace_by_branch(chart, target_branch)
        if palace:
            result.append(palace)

    return result


def get_san_fang_stars(chart: dict[str, Any], ming_branch: str) -> list[str]:
    """获取三方四正所有星曜名称

    Args:
        chart: iztro-py 排盘结果
        ming_branch: 命宫地支

    Returns:
        三方四正所有星曜名称列表
    """
    palaces = get_san_fang_palaces(chart, ming_branch)
    stars = []
    for palace in palaces:
        # 主星
        for star in palace.get("majorStars", []):
            name = star.get("name", "")
            if name:
                stars.append(name)
        # 辅星
        for star in palace.get("minorStars", []):
            name = star.get("name", "")
            if name:
                stars.append(name)
    return stars


def get_jia_palaces(chart: dict[str, Any], branch: str) -> dict[str, dict[str, Any] | None]:
    """获取夹宫（命宫前后两宫）

    Args:
        chart: iztro-py 排盘结果
        branch: 命宫地支

    Returns:
        {"prev": 前一宫, "next": 后一宫}
    """
    idx = BRANCH_INDEX.get(branch, 0)

    prev_idx = (idx - 1) % 12
    next_idx = (idx + 1) % 12

    prev_branch = list(BRANCH_INDEX.keys())[prev_idx]
    next_branch = list(BRANCH_INDEX.keys())[next_idx]

    return {
        "prev": get_palace_by_branch(chart, prev_branch),
        "next": get_palace_by_branch(chart, next_branch),
    }


def get_jia_stars(chart: dict[str, Any], branch: str) -> list[str]:
    """获取夹宫所有星曜名称

    Args:
        chart: iztro-py 排盘结果
        branch: 命宫地支

    Returns:
        夹宫所有星曜名称列表
    """
    jia = get_jia_palaces(chart, branch)
    stars = []
    for palace in [jia["prev"], jia["next"]]:
        if palace:
            for star in palace.get("majorStars", []):
                name = star.get("name", "")
                if name:
                    stars.append(name)
            for star in palace.get("minorStars", []):
                name = star.get("name", "")
                if name:
                    stars.append(name)
    return stars


def is_bright(palace: dict[str, Any], star_name: str) -> bool:
    """判断星曜是否庙旺

    Args:
        palace: 宫位数据
        star_name: 星曜名称

    Returns:
        True 如果庙旺
    """
    for star in palace.get("majorStars", []) + palace.get("minorStars", []):
        if star.get("name") == star_name:
            return star.get("brightness") == "bright"
    return False


def is_dim(palace: dict[str, Any], star_name: str) -> bool:
    """判断星曜是否落陷

    Args:
        palace: 宫位数据
        star_name: 星曜名称

    Returns:
        True 如果落陷
    """
    for star in palace.get("majorStars", []) + palace.get("minorStars", []):
        if star.get("name") == star_name:
            return star.get("brightness") == "dim"
    return False


def has_star(palace: dict[str, Any], star_name: str) -> bool:
    """判断宫位是否有某星曜

    Args:
        palace: 宫位数据
        star_name: 星曜名称

    Returns:
        True 如果有该星曜
    """
    for star in palace.get("majorStars", []) + palace.get("minorStars", []):
        if star.get("name") == star_name:
            return True
    return False


def get_star_brightness(palace: dict[str, Any], star_name: str) -> str:
    """获取星曜亮度

    Args:
        palace: 宫位数据
        star_name: 星曜名称

    Returns:
        亮度（bright/normal/dim），未找到返回空字符串
    """
    for star in palace.get("majorStars", []) + palace.get("minorStars", []):
        if star.get("name") == star_name:
            return star.get("brightness", "")
    return ""


def get_ming_branch(chart: dict[str, Any]) -> str:
    """获取命宫地支

    Args:
        chart: iztro-py 排盘结果

    Returns:
        命宫地支
    """
    for palace in chart.get("palaces", []):
        if palace.get("name") == "命宫":
            return palace.get("earthlyBranch", "")
    return ""


def get_palace_major_stars(palace: dict[str, Any]) -> list[str]:
    """获取宫位主星名称列表

    Args:
        palace: 宫位数据

    Returns:
        主星名称列表
    """
    return [star.get("name", "") for star in palace.get("majorStars", []) if star.get("name")]


def get_palace_minor_stars(palace: dict[str, Any]) -> list[str]:
    """获取宫位辅星名称列表

    Args:
        palace: 宫位数据

    Returns:
        辅星名称列表
    """
    return [star.get("name", "") for star in palace.get("minorStars", []) if star.get("name")]


def get_palace_all_stars(palace: dict[str, Any]) -> list[str]:
    """获取宫位所有星曜名称列表

    Args:
        palace: 宫位数据

    Returns:
        所有星曜名称列表
    """
    return get_palace_major_stars(palace) + get_palace_minor_stars(palace)
