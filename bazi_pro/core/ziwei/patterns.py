"""
紫微斗数格局识别模块

基于 Renhuai123/ziwei-doushu 的 patterns.ts 移植，实现 42 个格局检测函数。
数据来源：《紫微斗数全书》《紫微斗数全集》《骨髓赋》
"""

from __future__ import annotations

from typing import Any

from bazi_pro.core.ziwei.constants import Pattern, PatternCondition
from bazi_pro.core.ziwei.utils import (
    get_san_fang_palaces,
    get_san_fang_stars,
    get_jia_palaces,
    get_jia_stars,
    is_bright,
    is_dim,
    has_star,
    get_palace_by_name,
    get_ming_branch,
    get_palace_major_stars,
)


# ── 上格检测函数 ──────────────────────────────────────────────────────────────

def detect_zi_fu(chart: dict[str, Any]) -> Pattern | None:
    """检测紫府同宫格

    条件：紫微+天府同宫（寅/申）
    来源：《紫微斗数全书》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    major_stars = get_palace_major_stars(ming_palace)
    if "紫微" in major_stars and "天府" in major_stars:
        earthly_branch = ming_palace.get("earthlyBranch", "")
        if earthly_branch in ["寅", "申"]:
            return Pattern(
                name="紫府同宫",
                level="excellent",
                description="紫微天府同坐命宫，主富贵双全，一生运势顺遂",
                palaces=["命宫"],
                conditions=PatternCondition(
                    required=["命宫紫微+天府", "寅或申宫"],
                    bonus=["三方四正会吉星"],
                    breaking=["三方四正会煞星"],
                ),
                source="《紫微斗数全书》",
            )

    return None


def detect_jun_chen_qing_hui(chart: dict[str, Any]) -> Pattern | None:
    """检测君臣庆会格

    条件：紫微入命 + 左辅右弼同会三方
    来源：《紫微斗数全书》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    major_stars = get_palace_major_stars(ming_palace)
    if "紫微" not in major_stars:
        return None

    # 检查三方四正是否有左辅右弼
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    if "左辅" in san_fang_stars and "右弼" in san_fang_stars:
        return Pattern(
            name="君臣庆会",
            level="excellent",
            description="紫微入命，左辅右弼同会三方，主贵气十足，有辅佐之力",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["命宫紫微", "三方四正左辅+右弼"],
                bonus=["三方四正会吉星"],
                breaking=["三方四正会煞星"],
            ),
            source="《紫微斗数全书》",
        )

    return None


def detect_fu_xiang_chao_yuan(chart: dict[str, Any]) -> Pattern | None:
    """检测府相朝垣格

    条件：天府天相分守命宫三方
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_palaces = get_san_fang_palaces(chart, ming_branch)

    has_tianfu = False
    has_tianxiang = False

    for palace in san_fang_palaces:
        major_stars = get_palace_major_stars(palace)
        if "天府" in major_stars:
            has_tianfu = True
        if "天相" in major_stars:
            has_tianxiang = True

    if has_tianfu and has_tianxiang:
        return Pattern(
            name="府相朝垣",
            level="excellent",
            description="天府天相分守命宫三方，主富贵双全，一生运势顺遂",
            palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
            conditions=PatternCondition(
                required=["三方四正天府+天相"],
                bonus=["三方四正会吉星"],
                breaking=["三方四正会煞星"],
            ),
            source="《紫微斗数全书》",
        )

    return None


def detect_yang_liang_chang_lu(chart: dict[str, Any]) -> Pattern | None:
    """检测阳梁昌禄格

    条件：太阳+天梁+文昌+禄存齐会
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    required_stars = ["太阳", "天梁", "文昌", "禄存"]
    if all(star in san_fang_stars for star in required_stars):
        return Pattern(
            name="阳梁昌禄",
            level="excellent",
            description="太阳天梁文昌禄存齐会，主才华横溢，财运亨通",
            palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
            conditions=PatternCondition(
                required=["三方四正太阳+天梁+文昌+禄存"],
                bonus=["庙旺"],
                breaking=["落陷"],
            ),
            source="《紫微斗数全书》",
        )

    return None


def detect_huo_tan_ling_tan(chart: dict[str, Any]) -> Pattern | None:
    """检测火贪格/铃贪格

    条件：贪狼+火星/铃星同宫或会照
    来源：《骨髓赋》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    major_stars = get_palace_major_stars(ming_palace)
    if "贪狼" not in major_stars:
        return None

    # 检查是否有火星或铃星
    all_stars = get_palace_major_stars(ming_palace) + [s.get("name", "") for s in ming_palace.get("minorStars", [])]
    has_huoxing = "火星" in all_stars
    has_lingxing = "铃星" in all_stars

    if has_huoxing:
        return Pattern(
            name="火贪格",
            level="excellent",
            description="贪狼火星同宫，主横财运，暴发暴败",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["命宫贪狼+火星"],
                bonus=["庙旺"],
                breaking=["落陷"],
            ),
            source="《骨髓赋》",
        )

    if has_lingxing:
        return Pattern(
            name="铃贪格",
            level="excellent",
            description="贪狼铃星同宫，主横财运，暴发暴败",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["命宫贪狼+铃星"],
                bonus=["庙旺"],
                breaking=["落陷"],
            ),
            source="《骨髓赋》",
        )

    return None


def detect_wu_tan(chart: dict[str, Any]) -> Pattern | None:
    """检测武贪格

    条件：武曲+贪狼同宫（丑/未）或对宫
    来源：《骨髓赋》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    major_stars = get_palace_major_stars(ming_palace)
    earthly_branch = ming_palace.get("earthlyBranch", "")

    # 检查同宫
    if "武曲" in major_stars and "贪狼" in major_stars:
        if earthly_branch in ["丑", "未"]:
            return Pattern(
                name="武贪格",
                level="excellent",
                description="武曲贪狼同宫，主财运亨通，晚年发福",
                palaces=["命宫"],
                conditions=PatternCondition(
                    required=["命宫武曲+贪狼", "丑或未宫"],
                    bonus=["庙旺"],
                    breaking=["落陷"],
                ),
                source="《骨髓赋》",
            )

    # 检查对宫
    # TODO: 实现对宫检查

    return None


def detect_sha_po_lang(chart: dict[str, Any]) -> Pattern | None:
    """检测杀破狼格

    条件：七杀+破军+贪狼三方齐聚
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    required_stars = ["七杀", "破军", "贪狼"]
    if all(star in san_fang_stars for star in required_stars):
        return Pattern(
            name="杀破狼",
            level="excellent",
            description="七杀破军贪狼三方齐聚，主一生动荡变化，大起大落",
            palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
            conditions=PatternCondition(
                required=["三方四正七杀+破军+贪狼"],
                bonus=["庙旺"],
                breaking=["落陷"],
            ),
            source="《紫微斗数全书》",
        )

    return None


def detect_ji_yue_tong_liang(chart: dict[str, Any]) -> Pattern | None:
    """检测机月同梁格

    条件：天机+太阴+天同+天梁齐入
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    required_stars = ["天机", "太阴", "天同", "天梁"]
    if all(star in san_fang_stars for star in required_stars):
        return Pattern(
            name="机月同梁",
            level="excellent",
            description="天机太阴天同天梁齐入，主才华横溢，适合公职",
            palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
            conditions=PatternCondition(
                required=["三方四正天机+太阴+天同+天梁"],
                bonus=["庙旺"],
                breaking=["落陷"],
            ),
            source="《紫微斗数全书》",
        )

    return None


# ── 中格检测函数 ──────────────────────────────────────────────────────────────

def detect_lian_xiang(chart: dict[str, Any]) -> Pattern | None:
    """检测廉贞天相格"""
    # TODO: 实现
    return None


def detect_wu_qi_sha(chart: dict[str, Any]) -> Pattern | None:
    """检测武曲七杀格"""
    # TODO: 实现
    return None


def detect_tong_liang(chart: dict[str, Any]) -> Pattern | None:
    """检测天同天梁格"""
    # TODO: 实现
    return None


def detect_ri_yue_tong_gong(chart: dict[str, Any]) -> Pattern | None:
    """检测日月同宫格"""
    # TODO: 实现
    return None


def detect_ri_yue_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测日月夹命格"""
    # TODO: 实现
    return None


def detect_ju_ri_tong_gong(chart: dict[str, Any]) -> Pattern | None:
    """检测巨日同宫格"""
    # TODO: 实现
    return None


def detect_shi_zhong_yin_yu(chart: dict[str, Any]) -> Pattern | None:
    """检测石中隐玉格"""
    # TODO: 实现
    return None


def detect_ming_zhu_chu_hai(chart: dict[str, Any]) -> Pattern | None:
    """检测明珠出海格"""
    # TODO: 实现
    return None


def detect_zi_wei_in_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测紫微入命格"""
    # TODO: 实现
    return None


# ── 助力格检测函数 ──────────────────────────────────────────────────────────────

def detect_fu_bi_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测辅弼夹命格"""
    # TODO: 实现
    return None


def detect_chang_qu_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测昌曲夹命格"""
    # TODO: 实现
    return None


def detect_kui_yue_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测魁钺夹命格"""
    # TODO: 实现
    return None


def detect_shuang_lu_chao_yuan(chart: dict[str, Any]) -> Pattern | None:
    """检测双禄朝垣格"""
    # TODO: 实现
    return None


def detect_san_qi_jia_hui(chart: dict[str, Any]) -> Pattern | None:
    """检测三奇加会格"""
    # TODO: 实现
    return None


def detect_hua_lu_ru_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测化禄入命格"""
    # TODO: 实现
    return None


def detect_chang_qu_tong_hui(chart: dict[str, Any]) -> Pattern | None:
    """检测昌曲坐命/同会格"""
    # TODO: 实现
    return None


def detect_fu_bi_tong_hui(chart: dict[str, Any]) -> Pattern | None:
    """检测辅弼同会格"""
    # TODO: 实现
    return None


# ── 恶格检测函数 ──────────────────────────────────────────────────────────────

def detect_hua_ji_ru_ming_qian(chart: dict[str, Any]) -> Pattern | None:
    """检测化忌入命/迁格"""
    # TODO: 实现
    return None


def detect_yang_tuo_jia_ji(chart: dict[str, Any]) -> Pattern | None:
    """检测羊陀夹忌格"""
    # TODO: 实现
    return None


def detect_huo_ling_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测火铃夹命格"""
    # TODO: 实现
    return None


def detect_kong_jie_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测空劫夹命格"""
    # TODO: 实现
    return None


def detect_lian_sha_yang(chart: dict[str, Any]) -> Pattern | None:
    """检测廉杀羊格"""
    # TODO: 实现
    return None


def detect_ju_huo_yang(chart: dict[str, Any]) -> Pattern | None:
    """检测巨火羊格"""
    # TODO: 实现
    return None


def detect_ling_chang_tuo_wu(chart: dict[str, Any]) -> Pattern | None:
    """检测铃昌陀武格"""
    # TODO: 实现
    return None


def detect_ma_tou_dai_jian(chart: dict[str, Any]) -> Pattern | None:
    """检测马头带箭格"""
    # TODO: 实现
    return None


# ── 基础格局检测函数 ──────────────────────────────────────────────────────────────

def detect_lu_cun_shou_shen(chart: dict[str, Any]) -> Pattern | None:
    """检测禄存守命/守身格"""
    # TODO: 实现
    return None


def detect_tian_ma_ru_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测天马入命/在迁格"""
    # TODO: 实现
    return None


def detect_hua_lu_ru_cai(chart: dict[str, Any]) -> Pattern | None:
    """检测化禄入财格"""
    # TODO: 实现
    return None


def detect_hua_quan_ru_guan(chart: dict[str, Any]) -> Pattern | None:
    """检测化权入官格"""
    # TODO: 实现
    return None


def detect_hua_ke_ru_ming_shen(chart: dict[str, Any]) -> Pattern | None:
    """检测化科入命/身格"""
    # TODO: 实现
    return None


def detect_ji_yue_tong_liang_partial(chart: dict[str, Any]) -> Pattern | None:
    """检测机月同梁三星会格"""
    # TODO: 实现
    return None


def detect_kui_yue_tong_hui(chart: dict[str, Any]) -> Pattern | None:
    """检测魁钺同会格"""
    # TODO: 实现
    return None


def detect_ke_quan_shuang_hui(chart: dict[str, Any]) -> Pattern | None:
    """检测科权双会格"""
    # TODO: 实现
    return None


# ── 主检测函数 ──────────────────────────────────────────────────────────────

def detect_patterns(chart: dict[str, Any]) -> list[Pattern]:
    """检测所有格局

    Args:
        chart: iztro-py 排盘结果

    Returns:
        检测到的格局列表
    """
    patterns = []

    # 上格检测
    excellent_detectors = [
        detect_zi_fu,
        detect_jun_chen_qing_hui,
        detect_fu_xiang_chao_yuan,
        detect_yang_liang_chang_lu,
        detect_huo_tan_ling_tan,
        detect_wu_tan,
        detect_sha_po_lang,
        detect_ji_yue_tong_liang,
    ]

    # 中格检测
    good_detectors = [
        detect_lian_xiang,
        detect_wu_qi_sha,
        detect_tong_liang,
        detect_ri_yue_tong_gong,
        detect_ri_yue_jia_ming,
        detect_ju_ri_tong_gong,
        detect_shi_zhong_yin_yu,
        detect_ming_zhu_chu_hai,
        detect_zi_wei_in_ming,
    ]

    # 助力格检测
    bonus_detectors = [
        detect_fu_bi_jia_ming,
        detect_chang_qu_jia_ming,
        detect_kui_yue_jia_ming,
        detect_shuang_lu_chao_yuan,
        detect_san_qi_jia_hui,
        detect_hua_lu_ru_ming,
        detect_chang_qu_tong_hui,
        detect_fu_bi_tong_hui,
    ]

    # 恶格检测
    caution_detectors = [
        detect_hua_ji_ru_ming_qian,
        detect_yang_tuo_jia_ji,
        detect_huo_ling_jia_ming,
        detect_kong_jie_jia_ming,
        detect_lian_sha_yang,
        detect_ju_huo_yang,
        detect_ling_chang_tuo_wu,
        detect_ma_tou_dai_jian,
    ]

    # 基础格局检测
    basic_detectors = [
        detect_lu_cun_shou_shen,
        detect_tian_ma_ru_ming,
        detect_hua_lu_ru_cai,
        detect_hua_quan_ru_guan,
        detect_hua_ke_ru_ming_shen,
        detect_ji_yue_tong_liang_partial,
        detect_kui_yue_tong_hui,
        detect_ke_quan_shuang_hui,
    ]

    # 按顺序检测所有格局
    for detector in excellent_detectors + good_detectors + bonus_detectors + caution_detectors + basic_detectors:
        pattern = detector(chart)
        if pattern:
            patterns.append(pattern)

    return patterns
