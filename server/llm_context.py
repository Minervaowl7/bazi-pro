"""
LLM 上下文模块 — 干支计算 + 上下文格式化 + 检索结果格式化 + 学校视角
"""
import json
import logging
from datetime import datetime

from bazi_pro.paipan import DIZHI, TIANGAN

logger = logging.getLogger("bazi-pro.llm")


# ============ 干支计算 ============


def _get_year_ganzhi(year: int) -> str:
    """根据公历年份计算年柱干支"""
    gan_idx = (year - 4) % 10
    zhi_idx = (year - 4) % 12
    return TIANGAN[gan_idx] + DIZHI[zhi_idx]


def _get_month_ganzhi(year: int, month: int) -> str:
    """根据公历年月计算月柱干支（使用排盘引擎确保准确）"""
    try:
        from bazi_pro.paipan import paipan_from_datetime
        solar_str = f"{year:04d}-{month:02d}-15 12:00"
        result = paipan_from_datetime(solar_str, "男")
        if result.get("status") == "completed":
            pillars = result.get("pillars", [])
            if pillars and len(pillars) >= 2:
                return pillars[1].get("gan", "") + pillars[1].get("zhi", "")
    except Exception:
        pass
    # 降级：五虎遁简化计算
    year_gan_idx = (year - 4) % 10
    year_gan = TIANGAN[year_gan_idx]
    # 甲己之年丙作首，乙庚之岁戊为头...
    base_map = {"甲": 2, "己": 2, "乙": 4, "庚": 4, "丙": 6, "辛": 6, "丁": 8, "壬": 8, "戊": 0, "癸": 0}
    base_idx = base_map.get(year_gan, 2)
    gan_idx = (base_idx + month - 1) % 10
    zhi_idx = (month + 1) % 12  # 寅月为正月
    return TIANGAN[gan_idx] + DIZHI[zhi_idx]


def _get_day_ganzhi(d) -> str:
    """根据公历日期计算日柱干支（使用排盘引擎确保准确）"""
    try:
        from datetime import date

        from bazi_pro.paipan import paipan_from_datetime
        if isinstance(d, date):
            solar_str = f"{d.year:04d}-{d.month:02d}-{d.day:02d} 12:00"
            result = paipan_from_datetime(solar_str, "男")
            if result.get("status") == "completed":
                pillars = result.get("pillars", [])
                if pillars and len(pillars) >= 3:
                    return pillars[2].get("gan", "") + pillars[2].get("zhi", "")
    except Exception:
        pass
    # 降级：简化计算（1900-01-01 为甲戌日）
    from datetime import date
    base = date(1900, 1, 1)
    if isinstance(d, date):
        delta = (d - base).days
        gan_idx = (delta + 0) % 10  # 甲=0
        zhi_idx = (delta + 10) % 12  # 戌=10
        return TIANGAN[gan_idx] + DIZHI[zhi_idx]
    return ""


# ============ 派别视角定义 ============

SCHOOL_PERSPECTIVES = {
    "ziping": {
        "name": "传统子平法",
        "core_concepts": ["格局", "用神", "旺衰", "月令", "透干", "通根"],
        "classics": ["《子平真诠》", "《渊海子平》", "《滴天髓》", "《神峰通考》"],
        "methodology": """
以月令取格，看格局成败；以旺衰定用忌，看扶抑得失。
- 格局法：月令透干为格，无格看局，格局清纯为贵
- 旺衰法：得令得地得势，身强身弱定用神方向
- 调候法：寒暖燥湿，调候为先
- 病药法：有病方为贵，无伤不是奇""",
    },
    "mangpai": {
        "name": "盲派",
        "core_concepts": ["宾主", "体用", "做功", "功神", "废神", "贼神捕神", "象法"],
        "classics": ["《盲派初级命理学》", "《命理珍宝》", "《命理瑰宝》"],
        "methodology": """
以宾主体用分定位，以做功论富贵贫贱。
- 宾主：日主为主，他干支为宾；日柱为主，年月时为宾
- 体用：日主、比劫、印禄为体；财官食伤为用
- 做功：制用、化用、生用、合用、墓用、穿用、刑用
- 贼神捕神：寻贼捕贼，制化得宜
- 五党成势：党多势众，顺其气势""",
    },
    "xinpai": {
        "name": "新派",
        "core_concepts": ["百神论", "空亡论", "反断论", "格局分类", "从强从弱", "扶抑"],
        "classics": ["《八字预测真踪》"],
        "methodology": """
以格局分类定大方向，以百神论看六亲，以空亡论看应期。
- 格局分类：扶抑格、从强格、从弱格、化气格
- 百神论：无某六亲时，以其他十神替代看六亲
- 空亡论：空亡支在流年大运出空时发生作用
- 反断论：同宗对反断，旺极反弱、弱极反旺
- 虚实论：天干为虚，地支为实""",
    },
}


def _get_school_context(school: str) -> str:
    """获取派别视角上下文"""
    school_info = SCHOOL_PERSPECTIVES.get(school, SCHOOL_PERSPECTIVES["ziping"])
    return f"""
【当前分析视角：{school_info['name']}】

核心概念：{', '.join(school_info['core_concepts'])}

参考典籍：{', '.join(school_info['classics'])}

方法论：{school_info['methodology']}
"""


# ============ 上下文格式化 ============


def _format_analysis_context(analysis_result: dict, narration: dict, school: str = "ziping") -> str:
    """格式化命盘数据为文本上下文，支持不同派别视角"""
    if not isinstance(analysis_result, dict):
        analysis_result = {}
    if not isinstance(narration, dict):
        narration = {}

    validation = analysis_result.get("validation", {}) if isinstance(analysis_result.get("validation"), dict) else {}
    strength = analysis_result.get("strength", {}) if isinstance(analysis_result.get("strength"), dict) else {}
    if not strength and "wangshuai" in analysis_result:
        strength = {"wangshuai": analysis_result["wangshuai"]}
    pattern_info = analysis_result.get("pattern", {}) if isinstance(analysis_result.get("pattern"), dict) else {}
    yongshen_info = analysis_result.get("yongshen", {}) if isinstance(analysis_result.get("yongshen"), dict) else {}
    elements = analysis_result.get("elements", {}) if isinstance(analysis_result.get("elements"), dict) else {}
    if not elements:
        elements = analysis_result.get("element_forces", {}) if isinstance(analysis_result.get("element_forces"), dict) else {}
    relations = analysis_result.get("relations", []) if isinstance(analysis_result.get("relations"), list) else []
    tiaohou = analysis_result.get("tiaohou", {}) if isinstance(analysis_result.get("tiaohou"), dict) else {}
    shishen = analysis_result.get("shishen", {}) if isinstance(analysis_result.get("shishen"), dict) else {}
    shensha = analysis_result.get("shensha", {}) if isinstance(analysis_result.get("shensha"), dict) else {}
    gongwei = analysis_result.get("gongwei", {}) if isinstance(analysis_result.get("gongwei"), dict) else {}

    day_master = validation.get("day_master", "") or analysis_result.get("day_master", "")
    bazi = validation.get("bazi", "")
    if not bazi:
        # full_analysis() 返回 pillars 列表，需重构八字字符串
        pillars_raw = analysis_result.get("pillars", []) or (shishen.get("pillars", []) if isinstance(shishen, dict) else [])
        if pillars_raw:
            bazi = " ".join(p.get("gan", "") + p.get("zhi", "") for p in pillars_raw if isinstance(p, dict) and p.get("gan") and p.get("zhi"))
    gender = validation.get("gender", "") or analysis_result.get("gender", "")

    ws = strength.get("wangshuai", {}) if isinstance(strength, dict) else {}
    pattern = pattern_info.get("pattern", "") if isinstance(pattern_info, dict) else ""
    yongshen = yongshen_info.get("yongshen", "") if isinstance(yongshen_info, dict) else ""
    xishen = yongshen_info.get("xishen", []) if isinstance(yongshen_info, dict) else []
    jishen = yongshen_info.get("jishen", []) if isinstance(yongshen_info, dict) else []

    pillars_info = ""
    for p in (shishen.get("pillars", []) if isinstance(shishen, dict) else []):
        if not isinstance(p, dict):
            continue
        pos = p.get("position", "")
        gan = p.get("gan", "")
        zhi = p.get("zhi", "")
        ss_gan = p.get("shishen_gan", "")
        ss_zhi = p.get("shishen_zhi", "")
        canggan = p.get("canggan", []) if isinstance(p.get("canggan"), list) else []
        cg_str = " ".join(f"{c.get('gan','')}({c.get('shishen','')})" for c in canggan if isinstance(c, dict))
        pillars_info += f"  {pos}: {gan}{zhi} 天干十神={ss_gan} 地支十神={ss_zhi} 藏干={cg_str}\n"

    relations_str = ""
    for r in relations:
        if isinstance(r, dict):
            relations_str += f"  {r.get('type','')}: {r.get('description','')}\n"

    percent = elements.get("percent", {}) if isinstance(elements, dict) else {}
    try:
        elements_str = " ".join(f"{k}:{v:.1f}%" for k, v in sorted(percent.items(), key=lambda x: -x[1]))
    except Exception:
        elements_str = ""

    # 神煞信息
    shensha_str = ""
    if shensha and isinstance(shensha, dict):
        for category, items in shensha.items():
            if items:
                if isinstance(items, list):
                    shensha_str += f"  {category}: {', '.join(str(i) for i in items)}\n"
                elif isinstance(items, dict):
                    shensha_str += f"  {category}: {items}\n"

    # 宫位信息
    gongwei_str = ""
    if gongwei and isinstance(gongwei, dict):
        for key, val in gongwei.items():
            gongwei_str += f"  {key}: {val}\n"

    # 派别特定数据
    school_analyses = analysis_result.get("school_analyses", {}) if isinstance(analysis_result.get("school_analyses"), dict) else {}
    school_data = school_analyses.get(school, {}) if isinstance(school_analyses, dict) else {}
    school_str = ""
    if school_data and isinstance(school_data, dict):
        try:
            school_json = json.dumps(school_data, ensure_ascii=False, indent=2)
            # 将JSON中的 { 和 } 替换为安全字符，避免f-string解析问题
            school_str = "\n## " + school + "派分析数据\n" + school_json + "\n"
        except Exception:
            school_str = ""

    # 安全获取嵌套值
    deling_status = ""
    deling_score = 0
    if isinstance(strength, dict):
        deling = strength.get("deling", {})
        if isinstance(deling, dict):
            deling_status = deling.get("status", "")
            deling_score = deling.get("score", 0)

    dedi_score = 0
    deshi_score = 0
    if isinstance(strength, dict):
        dedi = strength.get("dedi", {})
        deshi = strength.get("deshi", {})
        if isinstance(dedi, dict):
            dedi_score = dedi.get("score", 0)
        if isinstance(deshi, dict):
            deshi_score = deshi.get("score", 0)

    ws_verdict = ""
    if isinstance(ws, dict):
        ws_verdict = ws.get("verdict", "")

    pattern_layer = "?"
    pattern_confidence = 0
    pattern_reason = ""
    if isinstance(pattern_info, dict):
        pattern_layer = pattern_info.get("layer", "?")
        pattern_confidence = pattern_info.get("confidence", 0)
        pattern_reason = pattern_info.get("reason", "")

    tiaohou_gan = []
    tiaohou_wx = []
    if isinstance(tiaohou, dict):
        tiaohou_gan = tiaohou.get("tiaohou_gan", []) if isinstance(tiaohou.get("tiaohou_gan"), list) else []
        tiaohou_wx = tiaohou.get("tiaohou_wx", []) if isinstance(tiaohou.get("tiaohou_wx"), list) else []

    xishen_str = "、".join(str(x) for x in xishen) if isinstance(xishen, list) else ""
    jishen_str = "、".join(str(j) for j in jishen) if isinstance(jishen, list) else ""

    shengxiao = validation.get("生肖", "") if isinstance(validation, dict) else ""

    # 出生年份与年龄计算
    birth_year = analysis_result.get("birth_year", 0)
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    current_day = now.day
    current_hour = now.hour
    current_minute = now.minute
    current_age = current_year - birth_year if birth_year else 0
    current_liunian_gan_zhi = _get_year_ganzhi(current_year)
    current_liuyue_gan_zhi = _get_month_ganzhi(current_year, current_month)
    current_liuri_gan_zhi = _get_day_ganzhi(now.date())

    # 大运数据
    dayun_list = analysis_result.get("dayun", []) if isinstance(analysis_result.get("dayun"), list) else []
    qiyun_age = analysis_result.get("qiyun_age", 0)
    dayun_str = ""
    current_dayun = ""
    for dy in dayun_list:
        if isinstance(dy, dict):
            age_range = dy.get("age_range", "")
            gan_zhi = dy.get("gan_zhi", "")
            dayun_str += f"  {age_range}: {gan_zhi}\n"
            # 判断当前正在走的大运
            if age_range and "-" in age_range:
                try:
                    start, end = age_range.split("-")
                    start_age = int(start.strip())
                    end_age = int(end.strip())
                    if start_age <= current_age <= end_age:
                        current_dayun = gan_zhi
                except (ValueError, TypeError):
                    pass

    narration_str = ""
    try:
        narration_str = json.dumps(narration, ensure_ascii=False, indent=2)
    except Exception:
        narration_str = "{}"

    # 使用字符串拼接而非f-string，避免JSON中的{和}被解析为格式占位符
    parts = [
        "## 命盘数据",
        f"- 八字: {bazi}",
        f"- 日主: {day_master}（{gender}命）",
        f"- 生肖: {shengxiao}",
        f"- 出生年份: {birth_year}年" if birth_year else "",
        f"- 当前时间: {current_year}年{current_month}月{current_day}日 {current_hour:02d}:{current_minute:02d}",
        f"- 当前流年: {current_liunian_gan_zhi}（{current_year}年）",
        f"- 当前流月: {current_liuyue_gan_zhi}（{current_month}月）",
        f"- 当前流日: {current_liuri_gan_zhi}（{current_month}月{current_day}日）",
        f"- 当前年龄: {current_age}岁" if birth_year else "",
        f"- 起运年龄: {qiyun_age}岁" if qiyun_age else "",
        f"- 当前大运: {current_dayun}" if current_dayun else "",
        "",
        "## 四柱详情",
        pillars_info,
        "",
        "## 旺衰判定",
        f"- 得令: {deling_status} (分数: {deling_score})",
        f"- 得地分数: {dedi_score}",
        f"- 得势分数: {deshi_score}",
        f"- 综合判定: {ws_verdict}",
        "",
        "## 格局",
        f"- 格局: {pattern} (第{pattern_layer}层, 置信度: {pattern_confidence:.0%})",
        f"- 判定理由: {pattern_reason}",
        "",
        "## 喜用神",
        f"- 用神: {yongshen}",
        f"- 喜神: {xishen_str}",
        f"- 忌神: {jishen_str}",
        "",
        "## 调候",
        f"- 调候用神: {'、'.join(str(t) for t in tiaohou_gan)} ({'、'.join(str(t) for t in tiaohou_wx)})",
        "",
        "## 五行力量",
        elements_str,
        "",
        "## 刑冲合害",
        relations_str if relations_str else "无",
        "",
        "## 神煞",
        shensha_str if shensha_str else "无",
        "",
        "## 宫位",
        gongwei_str if gongwei_str else "无",
        "",
        "## 大运列表",
        dayun_str if dayun_str else "未提供大运数据",
        "",
        "## 确定性叙述",
        narration_str,
    ]

    # 紫微斗数数据
    ziwei = analysis_result.get("ziwei", {}) if isinstance(analysis_result.get("ziwei"), dict) else {}
    if ziwei:
        ziwei_parts = []
        # 命盘基本信息
        soul = ziwei.get("soul", "")
        body = ziwei.get("body", "")
        five_class = ziwei.get("fiveElementsClass", "")
        if soul or body or five_class:
            ziwei_parts.append(f"- 命主: {soul}, 身主: {body}, 五行局: {five_class}")

        # 宫位主星
        palaces = ziwei.get("palaces", []) if isinstance(ziwei.get("palaces"), list) else []
        if palaces:
            palace_lines = []
            for p in palaces:
                if not isinstance(p, dict):
                    continue
                name = p.get("name", "")
                stars = [s.get("name", "") for s in p.get("majorStars", []) if isinstance(s, dict) and s.get("name")]
                brightness = [s.get("brightness", "") for s in p.get("majorStars", []) if isinstance(s, dict) and s.get("brightness")]
                if stars:
                    star_str = "、".join(stars)
                    bright_str = "、".join(brightness) if brightness else ""
                    palace_lines.append(f"  {name}: {star_str} ({bright_str})" if bright_str else f"  {name}: {star_str}")
            if palace_lines:
                ziwei_parts.append("- 宫位主星:\n" + "\n".join(palace_lines))

        # 四化信息
        sihua = ziwei.get("sihua", {}) if isinstance(ziwei.get("sihua"), dict) else {}
        if sihua:
            sihua_lines = []
            for key, val in sihua.items():
                if val:
                    sihua_lines.append(f"  {key}: {val}")
            if sihua_lines:
                ziwei_parts.append("- 四化:\n" + "\n".join(sihua_lines))

        # 格局
        ziwei_patterns = ziwei.get("patterns", []) if isinstance(ziwei.get("patterns"), list) else []
        if ziwei_patterns:
            pattern_lines = [f"  - {p}" for p in ziwei_patterns if isinstance(p, str)]
            if pattern_lines:
                ziwei_parts.append("- 紫微格局:\n" + "\n".join(pattern_lines))

        # 大限
        dayun_ziwei = ziwei.get("dayun", []) if isinstance(ziwei.get("dayun"), list) else []
        if dayun_ziwei:
            dayun_lines = []
            for d in dayun_ziwei[:8]:
                if isinstance(d, dict):
                    age = d.get("age_range", "")
                    palace = d.get("palace", "")
                    stars = d.get("stars", "")
                    dayun_lines.append(f"  {age}: {palace} {stars}")
            if dayun_lines:
                ziwei_parts.append("- 大限:\n" + "\n".join(dayun_lines))

        if ziwei_parts:
            parts.append("")
            parts.append("## 紫微斗数命盘")
            parts.extend(ziwei_parts)

    if school_str:
        parts.append(school_str)
    # 过滤空字符串
    return "\n".join(p for p in parts if p is not None and p != "")


# ============ 检索结果格式化 ============


def _format_retrieval_results(retrieval_results: dict | list | str | None) -> str:
    """将检索结果格式化为提示词文本"""
    if not retrieval_results:
        return ""

    if isinstance(retrieval_results, str):
        return f"\n## 古籍检索结果\n{retrieval_results}\n"

    if isinstance(retrieval_results, list):
        lines = ["\n## 古籍检索结果"]
        for idx, item in enumerate(retrieval_results, 1):
            if isinstance(item, dict):
                source = item.get("source", "")
                text = item.get("text", "")
                score = item.get("score", "")
                lines.append(f"{idx}. [{source}] {text}" + (f" (相关度: {score:.2f})" if isinstance(score, (int, float)) else ""))
            else:
                lines.append(f"{idx}. {item}")
        lines.append("")
        return "\n".join(lines)

    if isinstance(retrieval_results, dict):
        # Chat 场景：顶层有 "results" list（来自 retrieve_for_chat）
        if "results" in retrieval_results and isinstance(retrieval_results.get("results"), list):
            lines = ["\n## 古籍检索结果"]
            for idx, item in enumerate(retrieval_results["results"][:5], 1):
                if isinstance(item, dict):
                    source = item.get("source", "")
                    content = item.get("content") or ""
                    topic = item.get("topic", "")
                    label = f"{source}@{topic}" if topic else source
                    lines.append(f"  {idx}. [{label}] {content[:200]}")
                else:
                    lines.append(f"  {idx}. {item}")
            lines.append("")
            return "\n".join(lines)

        # Report 场景：chapter_key -> retrieval_result 映射
        lines = ["\n## 古籍检索结果"]
        for chapter_key, results in retrieval_results.items():
            lines.append(f"\n### {chapter_key}")
            # results 可能是 retrieve_for_report 返回的完整结构（含 results/counter_evidence），
            # 也可能是简单的 list
            items = results
            if isinstance(results, dict) and "results" in results:
                items = results.get("results", [])
            if isinstance(items, list):
                for idx, item in enumerate(items, 1):
                    if isinstance(item, dict):
                        source = item.get("source", "")
                        content = item.get("content") or ""
                        topic = item.get("topic", "")
                        label = f"{source}@{topic}" if topic else source
                        lines.append(f"  {idx}. [{label}] {content[:200]}")
                    else:
                        lines.append(f"  {idx}. {item}")
            else:
                lines.append(f"  {results}")
        lines.append("")
        return "\n".join(lines)

    return ""
