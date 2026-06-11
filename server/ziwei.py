"""紫微斗数排盘与运势模块

基于 iztro-py 库实现，提供完整的紫微斗数命盘排盘和运势查询功能。
iztro-py 是 mingli-mcp 的底层引擎，MIT 协议。

功能：
- 完整十二宫排盘（主星/辅星/杂耀/长生十二神/博士十二神）
- 大限/流年/流月/流日/流时运势
- 宫位详细分析
- 五行局/命主/身主
"""

from __future__ import annotations

from typing import Any

# iztro-py 是可选依赖
try:
    from iztro_py import by_solar
except ImportError:
    by_solar = None  # type: ignore[assignment]

# 紫微斗数分析模块（延迟导入以避免循环依赖）
_ziwei_patterns = None
_ziwei_sihua = None
_ziwei_narrator = None


def _get_ziwei_modules():
    """延迟导入紫微斗数模块"""
    global _ziwei_patterns, _ziwei_sihua, _ziwei_narrator
    if _ziwei_patterns is None:
        from bazi_pro.core.ziwei.narrator import narrate_ziwei
        from bazi_pro.core.ziwei.patterns import detect_patterns
        from bazi_pro.core.ziwei.sihua import analyze_sihua
        _ziwei_patterns = detect_patterns
        _ziwei_sihua = analyze_sihua
        _ziwei_narrator = narrate_ziwei
    return _ziwei_patterns, _ziwei_sihua, _ziwei_narrator


# ── 时辰编号映射 ──────────────────────────────────────────────
# time_index: 0=早子时(0:00-1:00), 1=丑时(1:00-3:00), ..., 12=晚子时(23:00-24:00)
HOUR_TO_TIME_INDEX: dict[int, int] = {
    0: 0,   # 早子时
    1: 1,   # 丑时
    3: 2,   # 寅时
    5: 3,   # 卯时
    7: 4,   # 辰时
    9: 5,   # 巳时
    11: 6,  # 午时
    13: 7,  # 未时
    15: 8,  # 申时
    17: 9,  # 酉时
    19: 10, # 戌时
    21: 11, # 亥时
    23: 12, # 晚子时
}


def hour_to_time_index(hour: int) -> int:
    """将小时(0-23)转换为时辰编号(0-12)。

    时辰划分：
    - 早子时: 0:00-1:00 (index=0)
    - 丑时:   1:00-3:00 (index=1)
    - 寅时:   3:00-5:00 (index=2)
    - ...每2小时一个时辰...
    - 亥时:  21:00-23:00 (index=11)
    - 晚子时: 23:00-24:00 (index=12)
    """
    if hour == 0:
        return 0
    if hour == 23:
        return 12
    # 1-22: (hour + 1) // 2
    return (hour + 1) // 2


def gender_to_chinese(gender: int | str) -> str:
    """将性别转换为中文（iztro-py 要求中文参数）。

    Args:
        gender: 1/\"男\"/\"male\" -> \"男\", 0/\"女\"/\"female\" -> \"女\"

    Returns:
        \"男\" 或 \"女\"
    """
    if isinstance(gender, str):
        if gender in ("男", "1", "male", "Male", "M", "m"):
            return "男"
        return "女"
    return "男" if gender == 1 else "女"


def get_ziwei_chart(
    solar_date: str,
    hour: int,
    gender: int | str = 1,
) -> dict[str, Any]:
    """生成紫微斗数完整命盘。

    Args:
        solar_date: 阳历日期，格式 YYYY-MM-DD
        hour: 出生小时(0-23)
        gender: 性别，1=男/0=女 或 \"男\"/\"女\"

    Returns:
        完整命盘字典，包含十二宫、主星、辅星、四化等信息。
        如果 iztro-py 未安装，返回空字典。
    """
    if by_solar is None:
        return {"error": "iztro-py 未安装，请运行 pip install iztro-py"}

    time_index = hour_to_time_index(hour)
    gender_cn = gender_to_chinese(gender)

    try:
        astrolabe = by_solar(
            solar_date=solar_date,
            time_index=time_index,
            gender=gender_cn,
            language="zh-CN",
        )
        data = astrolabe.to_iztro_dict()

        # 添加额外信息
        data["time_index"] = time_index
        data["hour"] = hour

        return data
    except Exception as e:
        return {"error": f"紫微斗数排盘失败: {e}"}


def get_ziwei_horoscope(
    solar_date: str,
    hour: int,
    gender: int | str = 1,
    query_date: str | None = None,
) -> dict[str, Any]:
    """查询紫微斗数运势（大限/流年/流月/流日/流时）。

    Args:
        solar_date: 出生阳历日期，格式 YYYY-MM-DD
        hour: 出生小时(0-23)
        gender: 性别
        query_date: 查询日期，格式 YYYY-MM-DD，默认今天

    Returns:
        运势字典，包含大限/小限/流年/流月/流日/流时信息。
    """
    if by_solar is None:
        return {"error": "iztro-py 未安装，请运行 pip install iztro-py"}

    time_index = hour_to_time_index(hour)
    gender_cn = gender_to_chinese(gender)

    if query_date is None:
        from datetime import date
        query_date = date.today().isoformat()

    try:
        astrolabe = by_solar(
            solar_date=solar_date,
            time_index=time_index,
            gender=gender_cn,
            language="zh-CN",
        )
        horoscope = astrolabe.horoscope(
            solar_date=query_date,
            time_index=time_index,
        )
        data = horoscope.model_dump()

        # 同时返回命盘基本信息
        chart = astrolabe.to_iztro_dict()
        data["chart_summary"] = {
            "soul": chart.get("soul", ""),
            "body": chart.get("body", ""),
            "fiveElementsClass": chart.get("fiveElementsClass", ""),
            "earthlyBranchOfSoulPalace": chart.get("earthlyBranchOfSoulPalace", ""),
            "earthlyBranchOfBodyPalace": chart.get("earthlyBranchOfBodyPalace", ""),
        }

        return data
    except Exception as e:
        return {"error": f"紫微斗数运势查询失败: {e}"}


def analyze_ziwei_palace(
    solar_date: str,
    hour: int,
    gender: int | str = 1,
    palace_name: str = "命宫",
) -> dict[str, Any]:
    """分析紫微斗数特定宫位。

    Args:
        solar_date: 出生阳历日期
        hour: 出生小时(0-23)
        gender: 性别
        palace_name: 宫位名称（命宫/兄弟宫/夫妻宫/子女宫/财帛宫/疾厄宫/
                     迁移宫/交友宫/官禄宫/田宅宫/福德宫/父母宫）

    Returns:
        宫位详细分析字典。
    """
    if by_solar is None:
        return {"error": "iztro-py 未安装，请运行 pip install iztro-py"}

    time_index = hour_to_time_index(hour)
    gender_cn = gender_to_chinese(gender)

    # 宫位名称列表（用于查找）
    PALACE_NAMES = [
        "命宫", "兄弟宫", "夫妻宫", "子女宫", "财帛宫", "疾厄宫",
        "迁移宫", "交友宫", "官禄宫", "田宅宫", "福德宫", "父母宫",
    ]

    try:
        astrolabe = by_solar(
            solar_date=solar_date,
            time_index=time_index,
            gender=gender_cn,
            language="zh-CN",
        )
        chart = astrolabe.to_iztro_dict()

        # 查找目标宫位
        target_palace = None
        for palace in chart.get("palaces", []):
            if palace.get("name") == palace_name:
                target_palace = palace
                break

        if target_palace is None:
            if palace_name not in PALACE_NAMES:
                return {"error": f"无效宫位名称: {palace_name}，可选: {', '.join(PALACE_NAMES)}"}
            return {"error": f"未找到宫位: {palace_name}"}

        # 获取对宫信息
        palace_index = None
        for i, p in enumerate(chart.get("palaces", [])):
            if p.get("name") == palace_name:
                palace_index = i
                break

        opposite_palace = None
        palaces_list = chart.get("palaces", [])
        if palace_index is not None and len(palaces_list) == 12:
            opposite_index = (palace_index + 6) % 12
            opposite_palace = palaces_list[opposite_index]

        result = {
            "palace": target_palace,
            "opposite_palace": {
                "name": opposite_palace.get("name", ""),
                "major_stars": [s.get("name", "") for s in opposite_palace.get("majorStars", [])],
            } if opposite_palace else None,
            "chart_info": {
                "soul": chart.get("soul", ""),
                "body": chart.get("body", ""),
                "fiveElementsClass": chart.get("fiveElementsClass", ""),
            },
        }

        return result
    except Exception as e:
        return {"error": f"紫微斗数宫位分析失败: {e}"}


def get_ziwei_patterns(
    solar_date: str,
    hour: int,
    gender: int | str = 1,
) -> dict[str, Any]:
    """获取紫微斗数格局分析

    Args:
        solar_date: 阳历日期，格式 YYYY-MM-DD
        hour: 出生小时(0-23)
        gender: 性别，1=男/0=女 或 "男"/"女"

    Returns:
        格局分析结果
    """
    if by_solar is None:
        return {"error": "iztro-py 未安装，请运行 pip install iztro-py"}

    time_index = hour_to_time_index(hour)
    gender_cn = gender_to_chinese(gender)

    try:
        astrolabe = by_solar(
            solar_date=solar_date,
            time_index=time_index,
            gender=gender_cn,
            language="zh-CN",
        )
        chart = astrolabe.to_iztro_dict()

        # 检测格局
        _detect_patterns, _, _ = _get_ziwei_modules()
        patterns = _detect_patterns(chart)

        return {
            "patterns": [
                {
                    "name": p.name,
                    "level": p.level,
                    "description": p.description,
                    "source": p.source,
                }
                for p in patterns
            ]
        }
    except Exception as e:
        return {"error": f"格局分析失败: {e}"}


def get_ziwei_sihua(
    solar_date: str,
    hour: int,
    gender: int | str = 1,
    query_year: int | None = None,
) -> dict[str, Any]:
    """获取紫微斗数四化分析

    Args:
        solar_date: 阳历日期，格式 YYYY-MM-DD
        hour: 出生小时(0-23)
        gender: 性别
        query_year: 查询年份（可选）

    Returns:
        四化分析结果
    """
    if by_solar is None:
        return {"error": "iztro-py 未安装，请运行 pip install iztro-py"}

    time_index = hour_to_time_index(hour)
    gender_cn = gender_to_chinese(gender)

    try:
        astrolabe = by_solar(
            solar_date=solar_date,
            time_index=time_index,
            gender=gender_cn,
            language="zh-CN",
        )
        chart = astrolabe.to_iztro_dict()

        # 分析四化
        _, _analyze_sihua, _ = _get_ziwei_modules()
        sihua = _analyze_sihua(chart, query_year)

        return sihua
    except Exception as e:
        return {"error": f"四化分析失败: {e}"}


def get_ziwei_dayun(
    solar_date: str,
    hour: int,
    gender: int | str = 1,
) -> dict[str, Any]:
    """获取紫微斗数大限（大运）数据。

    遍历十二宫，提取每步大限的年龄区间、宫位、主星和四化信息。

    Args:
        solar_date: 阳历日期，格式 YYYY-MM-DD
        hour: 出生小时(0-23)
        gender: 性别，1=男/0=女 或 "男"/"女"

    Returns:
        大限数据字典，包含 dayun 列表（按年龄排序）。
        每步大限包含 age_range, palace, major_stars, sihua_flow。
    """
    if by_solar is None:
        return {"error": "iztro-py 未安装，请运行 pip install iztro-py"}

    time_index = hour_to_time_index(hour)
    gender_cn = gender_to_chinese(gender)

    try:
        astrolabe = by_solar(
            solar_date=solar_date,
            time_index=time_index,
            gender=gender_cn,
            language="zh-CN",
        )
        chart = astrolabe.to_iztro_dict()

        # 构建宫位名到命盘宫位的映射（中文名）
        palace_map: dict[str, dict] = {}
        for p in chart.get("palaces", []):
            palace_map[p["name"]] = p

        # 遍历原始宫位对象，提取大限数据
        dayun_list: list[dict[str, Any]] = []
        for palace in astrolabe.palaces:
            decadal = palace.decadal
            if decadal is None:
                continue

            age_start, age_end = decadal.range
            palace_cn = palace.translate_name()

            # 主星列表
            major_stars = [
                {
                    "name": s.translate_name(),
                    "brightness": s.translate_brightness(),
                }
                for s in palace.major_stars
            ]

            # 四化（mutagen）：顺序为 [化禄, 化权, 化科, 化忌]
            sihua_flow: dict[str, str] = {}
            chart_palace = palace_map.get(palace_cn, {})
            for star in chart_palace.get("majorStars", []):
                if star.get("mutagen"):
                    sihua_flow[star["mutagen"]] = star["name"]
            for star in chart_palace.get("minorStars", []):
                if star.get("mutagen"):
                    sihua_flow[star["mutagen"]] = star["name"]

            dayun_list.append({
                "age_range": f"{age_start}-{age_end}",
                "age_start": age_start,
                "age_end": age_end,
                "palace": palace_cn,
                "heavenly_stem": palace.translate_heavenly_stem(),
                "earthly_branch": palace.translate_earthly_branch(),
                "major_stars": major_stars,
                "sihua_flow": sihua_flow,
            })

        # 按起始年龄排序
        dayun_list.sort(key=lambda x: x["age_start"])

        return {
            "dayun": dayun_list,
            "chart_summary": {
                "soul": chart.get("soul", ""),
                "body": chart.get("body", ""),
                "fiveElementsClass": chart.get("fiveElementsClass", ""),
            },
        }
    except Exception as e:
        return {"error": f"紫微斗数大限查询失败: {e}"}


def get_ziwei_liunian(
    solar_date: str,
    hour: int,
    gender: int | str = 1,
    query_year: int | None = None,
) -> dict[str, Any]:
    """获取紫微斗数流年运势数据。

    Args:
        solar_date: 阳历日期，格式 YYYY-MM-DD
        hour: 出生小时(0-23)
        gender: 性别，1=男/0=女 或 "男"/"女"
        query_year: 查询年份，默认当年

    Returns:
        流年数据字典，包含 year, palace, stars, sihua 等信息。
    """
    if by_solar is None:
        return {"error": "iztro-py 未安装，请运行 pip install iztro-py"}

    time_index = hour_to_time_index(hour)
    gender_cn = gender_to_chinese(gender)

    # 确定查询日期
    if query_year is None:
        from datetime import date
        query_year = date.today().year
    query_date = f"{query_year}-06-15"  # 取年中日期代表该年

    SIHUA_LABELS = ["化禄", "化权", "化科", "化忌"]

    try:
        astrolabe = by_solar(
            solar_date=solar_date,
            time_index=time_index,
            gender=gender_cn,
            language="zh-CN",
        )
        chart = astrolabe.to_iztro_dict()
        horoscope = astrolabe.horoscope(
            solar_date=query_date,
            time_index=time_index,
        )
        h_data = horoscope.model_dump()

        # 流年基本信息
        yearly = h_data.get("yearly", {})
        yearly_stem_en = yearly.get("heavenly_stem", "")
        yearly_branch_en = yearly.get("earthly_branch", "")

        # 从命盘宫位映射中翻译流年天干地支
        stem_map: dict[str, str] = {}
        branch_map: dict[str, str] = {}
        for palace in astrolabe.palaces:
            stem_map[palace.heavenly_stem] = palace.translate_heavenly_stem()
            branch_map[palace.earthly_branch] = palace.translate_earthly_branch()

        yearly_stem = stem_map.get(yearly_stem_en, yearly_stem_en)
        yearly_branch = branch_map.get(yearly_branch_en, yearly_branch_en)

        # 构建星曜名翻译辅助函数
        star_name_cache: dict[str, str] = {}
        for pal in astrolabe.palaces:
            for s in pal.major_stars + pal.minor_stars:
                star_name_cache[s.name] = s.translate_name()

        def _translate_star(en_name: str) -> str:
            """将英文星曜名翻译为中文"""
            return star_name_cache.get(en_name, en_name)

        # 流年四化（mutagen 顺序：化禄、化权、化科、化忌）
        mutagen_list = yearly.get("mutagen", [])
        sihua: dict[str, str] = {}
        for i, star_en in enumerate(mutagen_list):
            if i < len(SIHUA_LABELS):
                sihua[SIHUA_LABELS[i]] = _translate_star(star_en)

        # 流年宫位信息（palace_names 顺序对应十二宫）
        palace_names_en = yearly.get("palace_names", [])
        palace_name_map: dict[str, str] = {}
        for palace in astrolabe.palaces:
            palace_name_map[palace.name] = palace.translate_name()

        liunian_palaces = []
        for p_en in palace_names_en:
            liunian_palaces.append(palace_name_map.get(p_en, p_en))

        # 当前大限信息
        decadal = h_data.get("decadal", {})
        decadal_stem = stem_map.get(decadal.get("heavenly_stem", ""), decadal.get("heavenly_stem", ""))
        decadal_branch = branch_map.get(decadal.get("earthly_branch", ""), decadal.get("earthly_branch", ""))

        return {
            "year": query_year,
            "nominal_age": h_data.get("nominal_age"),
            "lunar_date": h_data.get("lunar_date", ""),
            "yearly": {
                "heavenly_stem": yearly_stem,
                "earthly_branch": yearly_branch,
                "ganzhi": f"{yearly_stem}{yearly_branch}",
                "sihua": sihua,
                "palace_names": liunian_palaces,
            },
            "decadal": {
                "heavenly_stem": decadal_stem,
                "earthly_branch": decadal_branch,
                "ganzhi": f"{decadal_stem}{decadal_branch}",
                "mutagen": [_translate_star(m) for m in decadal.get("mutagen", [])],
            },
            "chart_summary": {
                "soul": chart.get("soul", ""),
                "body": chart.get("body", ""),
                "fiveElementsClass": chart.get("fiveElementsClass", ""),
            },
        }
    except Exception as e:
        return {"error": f"紫微斗数流年查询失败: {e}"}


def get_ziwei_analysis(
    solar_date: str,
    hour: int,
    gender: int | str = 1,
    query_year: int | None = None,
) -> dict[str, Any]:
    """获取紫微斗数综合分析（格局+四化+星曜+叙述）

    Args:
        solar_date: 阳历日期，格式 YYYY-MM-DD
        hour: 出生小时(0-23)
        gender: 性别
        query_year: 查询年份（可选）

    Returns:
        综合分析结果
    """
    if by_solar is None:
        return {"error": "iztro-py 未安装，请运行 pip install iztro-py"}

    time_index = hour_to_time_index(hour)
    gender_cn = gender_to_chinese(gender)

    try:
        astrolabe = by_solar(
            solar_date=solar_date,
            time_index=time_index,
            gender=gender_cn,
            language="zh-CN",
        )
        chart = astrolabe.to_iztro_dict()

        # 生成叙述
        _, _, _narrate_ziwei = _get_ziwei_modules()
        narration = _narrate_ziwei(chart, query_year)

        return {
            "chart": chart,
            "narration": narration,
        }
    except Exception as e:
        return {"error": f"综合分析失败: {e}"}
