"""
紫微斗数确定性叙述器

从计算结果直接生成专业命理师风格的中文文本。
零 LLM 依赖，零幻觉风险。每句话都可追溯到确定性计算数据。

对标 bazi_pro/narrator.py 的架构。
"""

from __future__ import annotations

from typing import Any

from bazi_pro.core.ziwei.patterns import detect_patterns
from bazi_pro.core.ziwei.sihua import analyze_sihua
from bazi_pro.core.ziwei.stars import analyze_ming_palace, analyze_star_in_palace
from bazi_pro.core.ziwei.utils import get_palace_by_name, get_palace_major_stars


def narrate_ming_palace(chart: dict[str, Any]) -> str:
    """生成命宫分析叙述

    Args:
        chart: iztro-py 排盘结果

    Returns:
        命宫分析文本
    """
    # 分析命宫主星
    analysis = analyze_ming_palace(chart)
    if "error" in analysis:
        return f"命宫分析失败：{analysis['error']}"

    # 获取命宫信息
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return "未找到命宫信息"

    # 生成叙述
    text = "【命宫分析】\n\n"

    # 主星分析
    major_stars = analysis.get("major_stars", [])
    if major_stars:
        text += "命宫主星：\n"
        for star in major_stars:
            text += f"- {star.get('star', '')}（{star.get('brightness', '平')}）：{star.get('influence', '')}\n"
    else:
        text += "命宫无主星，借对宫主星之力。\n"

    # 辅星分析
    minor_stars = [s.get("name", "") for s in ming_palace.get("minorStars", [])]
    if minor_stars:
        text += f"\n辅星：{'、'.join(minor_stars)}\n"

    return text


def narrate_patterns(chart: dict[str, Any]) -> str:
    """生成格局分析叙述

    Args:
        chart: iztro-py 排盘结果

    Returns:
        格局分析文本
    """
    # 检测格局
    patterns = detect_patterns(chart)

    if not patterns:
        return "【格局分析】\n\n未检测到特殊格局，以正格论。\n"

    # 生成叙述
    text = "【格局分析】\n\n"

    # 按等级分组
    excellent = [p for p in patterns if p.level == "excellent"]
    good = [p for p in patterns if p.level == "good"]
    caution = [p for p in patterns if p.level == "caution"]

    if excellent:
        text += "上格：\n"
        for p in excellent:
            text += f"- {p.name}：{p.description}\n"
            if p.source:
                text += f"  （出处：{p.source}）\n"

    if good:
        text += "\n中格：\n"
        for p in good:
            text += f"- {p.name}：{p.description}\n"

    if caution:
        text += "\n警示格：\n"
        for p in caution:
            text += f"- {p.name}：{p.description}\n"

    return text


def narrate_sihua(chart: dict[str, Any], query_year: int | None = None) -> str:
    """生成四化分析叙述

    Args:
        chart: iztro-py 排盘结果
        query_year: 查询年份（可选）

    Returns:
        四化分析文本
    """
    # 分析四化
    sihua_analysis = analyze_sihua(chart, query_year)

    text = "【四化分析】\n\n"

    # 本命四化
    benming = sihua_analysis.get("benming", {})
    sihua = benming.get("sihua", {})
    text += "本命四化：\n"
    text += f"- 化禄：{sihua.get('化禄', '无')}\n"
    text += f"- 化权：{sihua.get('化权', '无')}\n"
    text += f"- 化科：{sihua.get('化科', '无')}\n"
    text += f"- 化忌：{sihua.get('化忌', '无')}\n"

    # 流年四化（如果指定了年份）
    if query_year and "liunian" in sihua_analysis:
        liunian = sihua_analysis["liunian"]
        liunian_sihua = liunian.get("sihua", {})
        text += f"\n{query_year}年流年四化：\n"
        text += f"- 化禄：{liunian_sihua.get('化禄', '无')}\n"
        text += f"- 化权：{liunian_sihua.get('化权', '无')}\n"
        text += f"- 化科：{liunian_sihua.get('化科', '无')}\n"
        text += f"- 化忌：{liunian_sihua.get('化忌', '无')}\n"

    return text


def narrate_wealth_palace(chart: dict[str, Any]) -> str:
    """生成财帛宫分析叙述

    Args:
        chart: iztro-py 排盘结果

    Returns:
        财帛宫分析文本
    """
    # 获取财帛宫
    wealth_palace = get_palace_by_name(chart, "财帛宫")
    if not wealth_palace:
        return "未找到财帛宫信息"

    text = "【财帛宫分析】\n\n"

    # 主星分析
    major_stars = get_palace_major_stars(wealth_palace)
    if major_stars:
        text += "财帛宫主星：\n"
        for star in major_stars:
            analysis = analyze_star_in_palace(star, "财帛宫")
            text += f"- {analysis.get('description', '')}\n"
    else:
        text += "财帛宫无主星，借对宫主星之力。\n"

    return text


def narrate_career_palace(chart: dict[str, Any]) -> str:
    """生成官禄宫分析叙述

    Args:
        chart: iztro-py 排盘结果

    Returns:
        官禄宫分析文本
    """
    # 获取官禄宫
    career_palace = get_palace_by_name(chart, "官禄宫")
    if not career_palace:
        return "未找到官禄宫信息"

    text = "【官禄宫分析】\n\n"

    # 主星分析
    major_stars = get_palace_major_stars(career_palace)
    if major_stars:
        text += "官禄宫主星：\n"
        for star in major_stars:
            analysis = analyze_star_in_palace(star, "官禄宫")
            text += f"- {analysis.get('description', '')}\n"
    else:
        text += "官禄宫无主星，借对宫主星之力。\n"

    return text


def narrate_marriage_palace(chart: dict[str, Any]) -> str:
    """生成夫妻宫分析叙述

    Args:
        chart: iztro-py 排盘结果

    Returns:
        夫妻宫分析文本
    """
    # 获取夫妻宫
    marriage_palace = get_palace_by_name(chart, "夫妻宫")
    if not marriage_palace:
        return "未找到夫妻宫信息"

    text = "【夫妻宫分析】\n\n"

    # 主星分析
    major_stars = get_palace_major_stars(marriage_palace)
    if major_stars:
        text += "夫妻宫主星：\n"
        for star in major_stars:
            analysis = analyze_star_in_palace(star, "夫妻宫")
            text += f"- {analysis.get('description', '')}\n"
    else:
        text += "夫妻宫无主星，借对宫主星之力。\n"

    return text


def narrate_health_palace(chart: dict[str, Any]) -> str:
    """生成疾厄宫分析叙述

    Args:
        chart: iztro-py 排盘结果

    Returns:
        疾厄宫分析文本
    """
    # 获取疾厄宫
    health_palace = get_palace_by_name(chart, "疾厄宫")
    if not health_palace:
        return "未找到疾厄宫信息"

    text = "【疾厄宫分析】\n\n"

    # 主星分析
    major_stars = get_palace_major_stars(health_palace)
    if major_stars:
        text += "疾厄宫主星：\n"
        for star in major_stars:
            analysis = analyze_star_in_palace(star, "疾厄宫")
            text += f"- {analysis.get('description', '')}\n"
    else:
        text += "疾厄宫无主星，借对宫主星之力。\n"

    return text


def narrate_summary(chart: dict[str, Any], sections: dict[str, str]) -> str:
    """生成综合评述

    Args:
        chart: iztro-py 排盘结果
        sections: 各维度叙述文本

    Returns:
        综合评述文本
    """
    text = "【综合评述】\n\n"

    # 获取命盘基本信息
    soul = chart.get("soul", "")  # 命主
    body = chart.get("body", "")  # 身主
    five_elements_class = chart.get("fiveElementsClass", "")  # 五行局

    text += f"命主：{soul}，身主：{body}，五行局：{five_elements_class}\n\n"

    # 综合各维度分析
    text += "命宫主星决定了命主的基本性格和人生走向。\n"
    text += "格局高低反映了命主的先天禀赋和后天发展潜力。\n"
    text += "四化星曜的动态变化影响着不同阶段的运势起伏。\n"

    return text


def narrate_overview(chart: dict[str, Any], sections: dict[str, str]) -> str:
    """生成命盘总览

    Args:
        chart: iztro-py 排盘结果
        sections: 各维度叙述文本

    Returns:
        命盘总览文本
    """
    text = "【命盘总览】\n\n"

    # 获取基本信息
    soul = chart.get("soul", "")
    body = chart.get("body", "")
    five_elements_class = chart.get("fiveElementsClass", "")

    text += f"命主：{soul}，身主：{body}，五行局：{five_elements_class}\n\n"

    # 生成总述
    text += "命宫主星决定了命主的基本性格和人生走向。\n"
    text += "格局高低反映了命主的先天禀赋和后天发展潜力。\n"
    text += "四化星曜的动态变化影响着不同阶段的运势起伏。\n"

    return text


def narrate_ziwei(chart: dict[str, Any], query_year: int | None = None) -> dict[str, str]:
    """生成紫微斗数确定性叙述

    Args:
        chart: iztro-py 排盘结果
        query_year: 查询年份（可选）

    Returns:
        {
            "overview": "命盘总览",
            "ming_palace": "命宫分析",
            "pattern": "格局分析",
            "sihua": "四化分析",
            "wealth": "财帛宫分析",
            "career": "官禄宫分析",
            "marriage": "夫妻宫分析",
            "health": "疾厄宫分析",
            "summary": "综合评述"
        }
    """
    result = {}

    # 1. 命宫分析
    result["ming_palace"] = narrate_ming_palace(chart)

    # 2. 格局分析
    result["pattern"] = narrate_patterns(chart)

    # 3. 四化分析
    result["sihua"] = narrate_sihua(chart, query_year)

    # 4. 财帛宫分析
    result["wealth"] = narrate_wealth_palace(chart)

    # 5. 官禄宫分析
    result["career"] = narrate_career_palace(chart)

    # 6. 夫妻宫分析
    result["marriage"] = narrate_marriage_palace(chart)

    # 7. 疾厄宫分析
    result["health"] = narrate_health_palace(chart)

    # 8. 综合评述
    result["summary"] = narrate_summary(chart, result)

    # 9. 命盘总览
    result["overview"] = narrate_overview(chart, result)

    return result
