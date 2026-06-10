"""
紫微斗数格局识别模块

基于 Renhuai123/ziwei-doushu 的 patterns.ts 移植，实现 42 个格局检测函数。
数据来源：《紫微斗数全书》《紫微斗数全集》《骨髓赋》
"""

from __future__ import annotations

from typing import Any

from bazi_pro.core.ziwei.constants import Pattern, PatternCondition, BRANCH_INDEX, BRANCH_ORDER
from bazi_pro.core.ziwei.sihua import get_sihua_by_stem
from bazi_pro.core.ziwei.utils import (
    get_san_fang_palaces,
    get_san_fang_stars,
    get_jia_palaces,
    get_jia_stars,
    is_bright,
    is_dim,
    has_star,
    get_palace_by_name,
    get_palace_by_branch,
    get_ming_branch,
    get_palace_major_stars,
    get_palace_all_stars,
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
    all_stars = get_palace_all_stars(ming_palace)
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

    # 检查对宫（命宫对宫为迁移宫，地支相差6位）
    opposite_branch = BRANCH_ORDER[(BRANCH_INDEX[earthly_branch] + 6) % 12] if earthly_branch else ""
    if opposite_branch:
        opposite_palace = get_palace_by_branch(chart, opposite_branch)
        if opposite_palace:
            opposite_stars = get_palace_major_stars(opposite_palace)
            # 命宫有武曲，对宫有贪狼（或反之）
            if ("武曲" in major_stars and "贪狼" in opposite_stars) or \
               ("贪狼" in major_stars and "武曲" in opposite_stars):
                if earthly_branch in ["丑", "未"]:
                    return Pattern(
                        name="武贪格",
                        level="excellent",
                        description="武曲贪狼对宫会照，主财运亨通，晚年发福",
                        palaces=["命宫", "迁移宫"],
                        conditions=PatternCondition(
                            required=["武曲贪狼对宫会照", "丑或未宫"],
                            bonus=["庙旺"],
                            breaking=["落陷"],
                        ),
                        source="《骨髓赋》",
                    )

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
    """检测廉贞天相格

    条件：廉贞+天相同宫
    来源：《紫微斗数全书》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    major_stars = get_palace_major_stars(ming_palace)
    if "廉贞" in major_stars and "天相" in major_stars:
        return Pattern(
            name="廉贞天相",
            level="good",
            description="廉贞天相同宫，主有才华，但易有是非",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["命宫廉贞+天相"],
                bonus=["三方四正会吉星"],
                breaking=["三方四正会煞星"],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_wu_qi_sha(chart: dict[str, Any]) -> Pattern | None:
    """检测武曲七杀格

    条件：武曲+七杀同宫
    来源：《紫微斗数全书》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    major_stars = get_palace_major_stars(ming_palace)
    if "武曲" in major_stars and "七杀" in major_stars:
        return Pattern(
            name="武曲七杀",
            level="good",
            description="武曲七杀同宫，主有魄力，但易有意外",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["命宫武曲+七杀"],
                bonus=["庙旺"],
                breaking=["落陷"],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_tong_liang(chart: dict[str, Any]) -> Pattern | None:
    """检测天同天梁格

    条件：天同+天梁同宫
    来源：《紫微斗数全书》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    major_stars = get_palace_major_stars(ming_palace)
    if "天同" in major_stars and "天梁" in major_stars:
        return Pattern(
            name="天同天梁",
            level="good",
            description="天同天梁同宫，主有福气，但易有波折",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["命宫天同+天梁"],
                bonus=["庙旺"],
                breaking=["落陷"],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_ri_yue_tong_gong(chart: dict[str, Any]) -> Pattern | None:
    """检测日月同宫格

    条件：太阳+太阴丑/未同宫
    来源：《紫微斗数全书》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    major_stars = get_palace_major_stars(ming_palace)
    earthly_branch = ming_palace.get("earthlyBranch", "")

    if "太阳" in major_stars and "太阴" in major_stars:
        if earthly_branch in ["丑", "未"]:
            return Pattern(
                name="日月同宫",
                level="good",
                description="太阳太阴同宫，主有才华，但易有矛盾",
                palaces=["命宫"],
                conditions=PatternCondition(
                    required=["命宫太阳+太阴", "丑或未宫"],
                    bonus=["庙旺"],
                    breaking=["落陷"],
                ),
                source="《紫微斗数全书》",
            )
    return None


def detect_ri_yue_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测日月夹命格

    条件：太阳太阴分居命宫前后
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    jia = get_jia_palaces(chart, ming_branch)

    if not jia["prev"] or not jia["next"]:
        return None

    prev_stars = get_palace_major_stars(jia["prev"])
    next_stars = get_palace_major_stars(jia["next"])

    has_sun = ("太阳" in prev_stars) or ("太阳" in next_stars)
    has_moon = ("太阴" in prev_stars) or ("太阴" in next_stars)

    if has_sun and has_moon:
        return Pattern(
            name="日月夹命",
            level="good",
            description="太阳太阴夹命，主有贵人相助，一生顺遂",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["太阳太阴夹命"],
                bonus=["庙旺"],
                breaking=["落陷"],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_ju_ri_tong_gong(chart: dict[str, Any]) -> Pattern | None:
    """检测巨日同宫格

    条件：巨门+太阳同入寅/申
    来源：《紫微斗数全书》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    major_stars = get_palace_major_stars(ming_palace)
    earthly_branch = ming_palace.get("earthlyBranch", "")

    if "巨门" in major_stars and "太阳" in major_stars:
        if earthly_branch in ["寅", "申"]:
            return Pattern(
                name="巨日同宫",
                level="good",
                description="巨门太阳同宫，主有口才，但易有是非",
                palaces=["命宫"],
                conditions=PatternCondition(
                    required=["命宫巨门+太阳", "寅或申宫"],
                    bonus=["庙旺"],
                    breaking=["落陷"],
                ),
                source="《紫微斗数全书》",
            )
    return None


def detect_shi_zhong_yin_yu(chart: dict[str, Any]) -> Pattern | None:
    """检测石中隐玉格

    条件：巨门入命于子/午
    来源：《骨髓赋》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    major_stars = get_palace_major_stars(ming_palace)
    earthly_branch = ming_palace.get("earthlyBranch", "")

    if "巨门" in major_stars:
        if earthly_branch in ["子", "午"]:
            return Pattern(
                name="石中隐玉",
                level="good",
                description="巨门入子午宫，主有才华，但需努力发掘",
                palaces=["命宫"],
                conditions=PatternCondition(
                    required=["命宫巨门", "子或午宫"],
                    bonus=["庙旺"],
                    breaking=["落陷"],
                ),
                source="《骨髓赋》",
            )
    return None


def detect_ming_zhu_chu_hai(chart: dict[str, Any]) -> Pattern | None:
    """检测明珠出海格

    条件：命未空宫，对宫日月同辉
    来源：《紫微斗数全集》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    earthly_branch = ming_palace.get("earthlyBranch", "")
    major_stars = get_palace_major_stars(ming_palace)

    # 命宫在未宫且无主星
    if earthly_branch == "未" and not major_stars:
        # 检查对宫（丑宫）是否有太阳太阴
        opposite_branch = "丑"
        opposite_palace = get_palace_by_branch(chart, opposite_branch)
        if opposite_palace:
            opposite_stars = get_palace_major_stars(opposite_palace)
            if "太阳" in opposite_stars and "太阴" in opposite_stars:
                return Pattern(
                    name="明珠出海",
                    level="good",
                    description="命宫空宫，对宫日月同辉，主有才华，但需贵人引荐",
                    palaces=["命宫", "迁移宫"],
                    conditions=PatternCondition(
                        required=["命宫未宫空宫", "对宫太阳+太阴"],
                        bonus=["庙旺"],
                        breaking=["落陷"],
                    ),
                    source="《紫微斗数全集》",
                )
    return None


def detect_zi_wei_in_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测紫微入命格

    条件：紫微独坐命宫
    来源：《紫微斗数全书》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    major_stars = get_palace_major_stars(ming_palace)
    if major_stars == ["紫微"]:
        return Pattern(
            name="紫微独坐",
            level="good",
            description="紫微独坐命宫，主有权威，但易孤高",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["命宫紫微独坐"],
                bonus=["三方四正会吉星"],
                breaking=["三方四正会煞星"],
            ),
            source="《紫微斗数全书》",
        )
    return None


# ── 助力格检测函数 ──────────────────────────────────────────────────────────────

def detect_fu_bi_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测辅弼夹命格

    条件：左辅右弼夹命
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    jia = get_jia_palaces(chart, ming_branch)

    if not jia["prev"] or not jia["next"]:
        return None

    prev_stars = get_palace_all_stars(jia["prev"])
    next_stars = get_palace_all_stars(jia["next"])

    has_fuzuo = ("左辅" in prev_stars) or ("左辅" in next_stars)
    has_youbi = ("右弼" in prev_stars) or ("右弼" in next_stars)

    if has_fuzuo and has_youbi:
        return Pattern(
            name="辅弼夹命",
            level="good",
            description="左辅右弼夹命，主有贵人相助",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["左辅右弼夹命"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_chang_qu_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测昌曲夹命格

    条件：文昌文曲夹命
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    jia = get_jia_palaces(chart, ming_branch)

    if not jia["prev"] or not jia["next"]:
        return None

    prev_stars = get_palace_all_stars(jia["prev"])
    next_stars = get_palace_all_stars(jia["next"])

    has_wenchang = ("文昌" in prev_stars) or ("文昌" in next_stars)
    has_wenqu = ("文曲" in prev_stars) or ("文曲" in next_stars)

    if has_wenchang and has_wenqu:
        return Pattern(
            name="昌曲夹命",
            level="good",
            description="文昌文曲夹命，主有才华，学业有成",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["文昌文曲夹命"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_kui_yue_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测魁钺夹命格

    条件：天魁天钺夹命
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    jia = get_jia_palaces(chart, ming_branch)

    if not jia["prev"] or not jia["next"]:
        return None

    prev_stars = get_palace_all_stars(jia["prev"])
    next_stars = get_palace_all_stars(jia["next"])

    has_tiankui = ("天魁" in prev_stars) or ("天魁" in next_stars)
    has_tianyue = ("天钺" in prev_stars) or ("天钺" in next_stars)

    if has_tiankui and has_tianyue:
        return Pattern(
            name="魁钺夹命",
            level="good",
            description="天魁天钺夹命，主有贵人相助，逢凶化吉",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["天魁天钺夹命"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_shuang_lu_chao_yuan(chart: dict[str, Any]) -> Pattern | None:
    """检测双禄朝垣格

    条件：化禄+禄存同会三方
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    if "禄存" in san_fang_stars:
        # 检查是否有化禄
        # 需要获取年干来判断化禄
        year_stem = chart.get("yearStem", "")
        if year_stem:
            sihua = get_sihua_by_stem(year_stem)
            hua_lu_star = sihua.get("化禄", "")
            if hua_lu_star and hua_lu_star in san_fang_stars:
                return Pattern(
                    name="双禄朝垣",
                    level="good",
                    description="化禄禄存同会三方，主财运亨通",
                    palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
                    conditions=PatternCondition(
                        required=["三方四正化禄+禄存"],
                        bonus=[],
                        breaking=[],
                    ),
                    source="《紫微斗数全书》",
                )
    return None


def detect_san_qi_jia_hui(chart: dict[str, Any]) -> Pattern | None:
    """检测三奇加会格

    条件：化禄+化权+化科齐会
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    # 获取年干四化
    year_stem = chart.get("yearStem", "")
    if not year_stem:
        return None

    sihua = get_sihua_by_stem(year_stem)

    hua_lu_star = sihua.get("化禄", "")
    hua_quan_star = sihua.get("化权", "")
    hua_ke_star = sihua.get("化科", "")

    if (hua_lu_star in san_fang_stars and
        hua_quan_star in san_fang_stars and
        hua_ke_star in san_fang_stars):
        return Pattern(
            name="三奇加会",
            level="good",
            description="化禄化权化科齐会三方，主才华横溢，事业有成",
            palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
            conditions=PatternCondition(
                required=["三方四正化禄+化权+化科"],
                bonus=[],
                breaking=["化忌同会"],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_hua_lu_ru_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测化禄入命格

    条件：主星化禄坐命
    来源：《紫微斗数全书》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    major_stars = get_palace_major_stars(ming_palace)
    year_stem = chart.get("yearStem", "")
    if not year_stem:
        return None

    sihua = get_sihua_by_stem(year_stem)
    hua_lu_star = sihua.get("化禄", "")

    if hua_lu_star in major_stars:
        return Pattern(
            name="化禄入命",
            level="good",
            description="主星化禄坐命，主有福气，财运亨通",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["命宫主星化禄"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_chang_qu_tong_hui(chart: dict[str, Any]) -> Pattern | None:
    """检测昌曲坐命/同会格

    条件：文昌文曲同会三方
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    if "文昌" in san_fang_stars and "文曲" in san_fang_stars:
        return Pattern(
            name="昌曲同会",
            level="good",
            description="文昌文曲同会三方，主有才华，学业有成",
            palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
            conditions=PatternCondition(
                required=["三方四正文昌+文曲"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_fu_bi_tong_hui(chart: dict[str, Any]) -> Pattern | None:
    """检测辅弼同会格

    条件：左辅右弼同会三方
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    if "左辅" in san_fang_stars and "右弼" in san_fang_stars:
        return Pattern(
            name="辅弼同会",
            level="good",
            description="左辅右弼同会三方，主有贵人相助",
            palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
            conditions=PatternCondition(
                required=["三方四正左辅+右弼"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )
    return None


# ── 恶格检测函数 ──────────────────────────────────────────────────────────────

def detect_hua_ji_ru_ming_qian(chart: dict[str, Any]) -> Pattern | None:
    """检测化忌入命/迁格

    条件：主星化忌坐命/迁
    来源：《紫微斗数全书》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    qian_palace = get_palace_by_name(chart, "迁移宫")

    year_stem = chart.get("yearStem", "")
    if not year_stem:
        return None

    sihua = get_sihua_by_stem(year_stem)
    hua_ji_star = sihua.get("化忌", "")

    if not hua_ji_star:
        return None

    # 检查命宫
    if ming_palace:
        ming_stars = get_palace_major_stars(ming_palace)
        if hua_ji_star in ming_stars:
            return Pattern(
                name="化忌入命",
                level="caution",
                description="主星化忌坐命，主有波折，需注意口舌是非",
                palaces=["命宫"],
                conditions=PatternCondition(
                    required=["命宫主星化忌"],
                    bonus=[],
                    breaking=[],
                ),
                source="《紫微斗数全书》",
            )

    # 检查迁移宫
    if qian_palace:
        qian_stars = get_palace_major_stars(qian_palace)
        if hua_ji_star in qian_stars:
            return Pattern(
                name="化忌入迁",
                level="caution",
                description="主星化忌坐迁移宫，主外出不顺，易有波折",
                palaces=["迁移宫"],
                conditions=PatternCondition(
                    required=["迁移宫主星化忌"],
                    bonus=[],
                    breaking=[],
                ),
                source="《紫微斗数全书》",
            )

    return None


def detect_yang_tuo_jia_ji(chart: dict[str, Any]) -> Pattern | None:
    """检测羊陀夹忌格

    条件：化忌坐命，羊陀夹
    来源：《骨髓赋》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    # 检查命宫是否有化忌
    year_stem = chart.get("yearStem", "")
    if not year_stem:
        return None

    sihua = get_sihua_by_stem(year_stem)
    hua_ji_star = sihua.get("化忌", "")

    ming_stars = get_palace_major_stars(ming_palace)
    if hua_ji_star not in ming_stars:
        return None

    # 检查羊陀夹
    ming_branch = get_ming_branch(chart)
    jia = get_jia_palaces(chart, ming_branch)

    if not jia["prev"] or not jia["next"]:
        return None

    prev_stars = get_palace_all_stars(jia["prev"])
    next_stars = get_palace_all_stars(jia["next"])

    has_qingyang = ("擎羊" in prev_stars) or ("擎羊" in next_stars)
    has_tuoluo = ("陀罗" in prev_stars) or ("陀罗" in next_stars)

    if has_qingyang and has_tuoluo:
        return Pattern(
            name="羊陀夹忌",
            level="caution",
            description="化忌坐命，羊陀夹，主有波折，需注意意外",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["命宫化忌", "擎羊陀罗夹命"],
                bonus=[],
                breaking=[],
            ),
            source="《骨髓赋》",
        )
    return None


def detect_huo_ling_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测火铃夹命格

    条件：火星铃星夹命
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    jia = get_jia_palaces(chart, ming_branch)

    if not jia["prev"] or not jia["next"]:
        return None

    prev_stars = get_palace_all_stars(jia["prev"])
    next_stars = get_palace_all_stars(jia["next"])

    has_huoxing = ("火星" in prev_stars) or ("火星" in next_stars)
    has_lingxing = ("铃星" in prev_stars) or ("铃星" in next_stars)

    if has_huoxing and has_lingxing:
        return Pattern(
            name="火铃夹命",
            level="caution",
            description="火星铃星夹命，主有波折，需注意意外",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["火星铃星夹命"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_kong_jie_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测空劫夹命格

    条件：地空地劫夹命
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    jia = get_jia_palaces(chart, ming_branch)

    if not jia["prev"] or not jia["next"]:
        return None

    prev_stars = get_palace_all_stars(jia["prev"])
    next_stars = get_palace_all_stars(jia["next"])

    has_dikong = ("地空" in prev_stars) or ("地空" in next_stars)
    has_dijie = ("地劫" in prev_stars) or ("地劫" in next_stars)

    if has_dikong and has_dijie:
        return Pattern(
            name="空劫夹命",
            level="caution",
            description="地空地劫夹命，主有波折，需注意破耗",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["地空地劫夹命"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_lian_sha_yang(chart: dict[str, Any]) -> Pattern | None:
    """检测廉杀羊格

    条件：廉贞+七杀+擎羊会照
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    required_stars = ["廉贞", "七杀", "擎羊"]
    if all(star in san_fang_stars for star in required_stars):
        return Pattern(
            name="廉杀羊",
            level="caution",
            description="廉贞七杀擎羊会照，主有波折，需注意意外",
            palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
            conditions=PatternCondition(
                required=["三方四正廉贞+七杀+擎羊"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_ju_huo_yang(chart: dict[str, Any]) -> Pattern | None:
    """检测巨火羊格

    条件：巨门+火星+擎羊会照
    来源：《骨髓赋》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    required_stars = ["巨门", "火星", "擎羊"]
    if all(star in san_fang_stars for star in required_stars):
        return Pattern(
            name="巨火羊",
            level="caution",
            description="巨门火星擎羊会照，主有是非，需注意口舌",
            palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
            conditions=PatternCondition(
                required=["三方四正巨门+火星+擎羊"],
                bonus=[],
                breaking=[],
            ),
            source="《骨髓赋》",
        )
    return None


def detect_ling_chang_tuo_wu(chart: dict[str, Any]) -> Pattern | None:
    """检测铃昌陀武格

    条件：铃星+文昌+陀罗+武曲
    来源：《骨髓赋》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    required_stars = ["铃星", "文昌", "陀罗", "武曲"]
    if all(star in san_fang_stars for star in required_stars):
        return Pattern(
            name="铃昌陀武",
            level="caution",
            description="铃星文昌陀罗武曲会照，主有波折，需注意意外",
            palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
            conditions=PatternCondition(
                required=["三方四正铃星+文昌+陀罗+武曲"],
                bonus=[],
                breaking=[],
            ),
            source="《骨髓赋》",
        )
    return None


def detect_ma_tou_dai_jian(chart: dict[str, Any]) -> Pattern | None:
    """检测马头带箭格

    条件：擎羊在午宫坐命
    来源：《骨髓赋》
    """
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    earthly_branch = ming_palace.get("earthlyBranch", "")
    if earthly_branch != "午":
        return None

    all_stars = get_palace_all_stars(ming_palace)
    if "擎羊" in all_stars:
        return Pattern(
            name="马头带箭",
            level="caution",
            description="擎羊在午宫坐命，主有波折，需注意意外",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["命宫午宫", "擎羊坐命"],
                bonus=[],
                breaking=[],
            ),
            source="《骨髓赋》",
        )
    return None


# ── 基础格局检测函数 ──────────────────────────────────────────────────────────────

def detect_lu_cun_shou_shen(chart: dict[str, Any]) -> Pattern | None:
    """检测禄存守命/守身格

    条件：禄存入命/身宫
    来源：《紫微斗数全书》
    """
    # 检查命宫
    ming_palace = get_palace_by_name(chart, "命宫")
    if ming_palace and has_star(ming_palace, "禄存"):
        return Pattern(
            name="禄存守命",
            level="good",
            description="禄存坐命，主有财运，一生不愁吃穿",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["命宫禄存"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )

    # 检查身宫
    shen_palace = get_palace_by_name(chart, "身宫")
    if shen_palace and has_star(shen_palace, "禄存"):
        return Pattern(
            name="禄存守身",
            level="good",
            description="禄存坐身宫，主有财运，晚年安享",
            palaces=["身宫"],
            conditions=PatternCondition(
                required=["身宫禄存"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )

    return None


def detect_tian_ma_ru_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测天马入命/在迁格

    条件：天马入命/迁宫
    来源：《紫微斗数全书》
    """
    # 检查命宫
    ming_palace = get_palace_by_name(chart, "命宫")
    if ming_palace and has_star(ming_palace, "天马"):
        return Pattern(
            name="天马入命",
            level="good",
            description="天马坐命，主有行动力，适合外出发展",
            palaces=["命宫"],
            conditions=PatternCondition(
                required=["命宫天马"],
                bonus=["禄存同宫"],
                breaking=["空劫同宫"],
            ),
            source="《紫微斗数全书》",
        )

    # 检查迁移宫
    qian_palace = get_palace_by_name(chart, "迁移宫")
    if qian_palace and has_star(qian_palace, "天马"):
        return Pattern(
            name="天马在迁",
            level="good",
            description="天马坐迁移宫，主有行动力，适合外出发展",
            palaces=["迁移宫"],
            conditions=PatternCondition(
                required=["迁移宫天马"],
                bonus=["禄存同宫"],
                breaking=["空劫同宫"],
            ),
            source="《紫微斗数全书》",
        )

    return None


def detect_hua_lu_ru_cai(chart: dict[str, Any]) -> Pattern | None:
    """检测化禄入财格

    条件：财帛宫主星化禄
    来源：《紫微斗数全书》
    """
    cai_palace = get_palace_by_name(chart, "财帛宫")
    if not cai_palace:
        return None

    major_stars = get_palace_major_stars(cai_palace)
    year_stem = chart.get("yearStem", "")
    if not year_stem:
        return None

    sihua = get_sihua_by_stem(year_stem)
    hua_lu_star = sihua.get("化禄", "")

    if hua_lu_star in major_stars:
        return Pattern(
            name="化禄入财",
            level="good",
            description="财帛宫主星化禄，主财运亨通",
            palaces=["财帛宫"],
            conditions=PatternCondition(
                required=["财帛宫主星化禄"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_hua_quan_ru_guan(chart: dict[str, Any]) -> Pattern | None:
    """检测化权入官格

    条件：官禄宫主星化权
    来源：《紫微斗数全书》
    """
    guan_palace = get_palace_by_name(chart, "官禄宫")
    if not guan_palace:
        return None

    major_stars = get_palace_major_stars(guan_palace)
    year_stem = chart.get("yearStem", "")
    if not year_stem:
        return None

    sihua = get_sihua_by_stem(year_stem)
    hua_quan_star = sihua.get("化权", "")

    if hua_quan_star in major_stars:
        return Pattern(
            name="化权入官",
            level="good",
            description="官禄宫主星化权，主事业有成，有权力",
            palaces=["官禄宫"],
            conditions=PatternCondition(
                required=["官禄宫主星化权"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_hua_ke_ru_ming_shen(chart: dict[str, Any]) -> Pattern | None:
    """检测化科入命/身格

    条件：命/身宫主星化科
    来源：《紫微斗数全书》
    """
    year_stem = chart.get("yearStem", "")
    if not year_stem:
        return None

    sihua = get_sihua_by_stem(year_stem)
    hua_ke_star = sihua.get("化科", "")

    # 检查命宫
    ming_palace = get_palace_by_name(chart, "命宫")
    if ming_palace:
        ming_stars = get_palace_major_stars(ming_palace)
        if hua_ke_star in ming_stars:
            return Pattern(
                name="化科入命",
                level="good",
                description="命宫主星化科，主有才华，学业有成",
                palaces=["命宫"],
                conditions=PatternCondition(
                    required=["命宫主星化科"],
                    bonus=[],
                    breaking=[],
                ),
                source="《紫微斗数全书》",
            )

    # 检查身宫
    shen_palace = get_palace_by_name(chart, "身宫")
    if shen_palace:
        shen_stars = get_palace_major_stars(shen_palace)
        if hua_ke_star in shen_stars:
            return Pattern(
                name="化科入身",
                level="good",
                description="身宫主星化科，主有才华，晚年安享",
                palaces=["身宫"],
                conditions=PatternCondition(
                    required=["身宫主星化科"],
                    bonus=[],
                    breaking=[],
                ),
                source="《紫微斗数全书》",
            )

    return None


def detect_ji_yue_tong_liang_partial(chart: dict[str, Any]) -> Pattern | None:
    """检测机月同梁三星会格

    条件：天机+太阴+天同+天梁中3星齐入三方
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    required_stars = ["天机", "太阴", "天同", "天梁"]
    found_count = sum(1 for star in required_stars if star in san_fang_stars)

    if found_count == 3:
        return Pattern(
            name="机月同梁三星会",
            level="good",
            description="机月同梁三星会三方，主有才华，适合公职",
            palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
            conditions=PatternCondition(
                required=["三方四正机月同梁3星"],
                bonus=["庙旺"],
                breaking=["落陷"],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_kui_yue_tong_hui(chart: dict[str, Any]) -> Pattern | None:
    """检测魁钺同会格

    条件：天魁天钺同会三方
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    if "天魁" in san_fang_stars and "天钺" in san_fang_stars:
        return Pattern(
            name="魁钺同会",
            level="good",
            description="天魁天钺同会三方，主有贵人相助",
            palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
            conditions=PatternCondition(
                required=["三方四正天魁+天钺"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )
    return None


def detect_ke_quan_shuang_hui(chart: dict[str, Any]) -> Pattern | None:
    """检测科权双会格

    条件：化科+化权同会三方
    来源：《紫微斗数全书》
    """
    ming_branch = get_ming_branch(chart)
    san_fang_stars = get_san_fang_stars(chart, ming_branch)

    year_stem = chart.get("yearStem", "")
    if not year_stem:
        return None

    sihua = get_sihua_by_stem(year_stem)

    hua_ke_star = sihua.get("化科", "")
    hua_quan_star = sihua.get("化权", "")

    if hua_ke_star in san_fang_stars and hua_quan_star in san_fang_stars:
        return Pattern(
            name="科权双会",
            level="good",
            description="化科化权同会三方，主有才华和权力",
            palaces=["命宫", "财帛宫", "官禄宫", "迁移宫"],
            conditions=PatternCondition(
                required=["三方四正化科+化权"],
                bonus=[],
                breaking=[],
            ),
            source="《紫微斗数全书》",
        )
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
