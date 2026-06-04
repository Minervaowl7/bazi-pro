"""
bazi-pro 确定性报告叙述器 (narrator)

从计算结果直接生成专业命理师风格的中文文本。
零 LLM 依赖，零幻觉风险。每句话都可追溯到确定性计算数据。

核心原则：
    - 零幻觉规则：所有叙述文本必须基于 result dict 中的计算数据生成，
      不可编造任何命理判断或古籍引用。
    - 键名一致性：本模块读取的键名（如 shishen、wangshuai、pattern）
      必须与 core/ 计算模块的输出键名完全一致，不可自行猜测或重命名。
    - 叙述维度：共 9 个维度（总览/旺衰/格局/用神/调候/五行/刑冲/性格/事业），
      每个维度对应一个内部函数，由 narrate_analysis() 统一调度。

关键概念：
    - 旺衰叙述：基于得令/得地/得势三要素，数据来源 strength["wangshuai"]
    - 格局叙述：基于六层格局筛查结果，数据来源 pattern["layer"]/["confidence"]
    - 用神叙述：区分格局用神法(pattern_based)与旺衰扶抑法(wangshuai_fallback)
    - 调候叙述：调用 tiaohou.lookup_tiaohou() 查表，引用《穷通宝鉴》原文
    - 刑冲叙述：基于 relations 列表，区分冲/合/刑/害四类关系

古籍引用：
    - 调候部分引用《穷通宝鉴》（穷通宝鉴，又名《拦江网》）
    - 格局/用神部分隐含《子平真诠》格局理论（由 core/patterns.py 计算）

用法:
    from bazi_pro.narrator import narrate_analysis
    sections = narrate_analysis(result_dict)
    # sections = {"overview": "...", "strength": "...", "pattern": "...", ...}
"""

from bazi_pro.core.constants import GAN_WUXING, ZHI_WUXING
from bazi_pro.core.tiaohou import lookup_tiaohou

# ─── 五行属性描述 ─────────────────────────────────────────────────────────────
# 每个五行对应：性（五常属性）、象（自然意象）、体（脏腑对应）、
# 色（色彩）、方（方位）、personality（性格描述，用于叙述器输出）
# 来源：传统命理学五行类象，非特定古籍单条，属共识性知识

_WUXING_NATURE = {
    "木": {"性": "仁", "象": "生发向上", "体": "肝胆", "色": "青绿", "方": "东方",
           "personality": "心性仁厚，好学上进，有恻隐之心。木主生发，做事有条理，善于规划。"},
    "火": {"性": "礼", "象": "炎上光明", "体": "心脏小肠", "色": "红紫", "方": "南方",
           "personality": "性情急躁，热情奔放，重礼仪面子。火主文明，口才好，善表达。"},
    "土": {"性": "信", "象": "厚重承载", "体": "脾胃", "色": "黄棕", "方": "中央",
           "personality": "为人敦厚，言出必行，重信用。土主信，做事稳重，不喜变动。"},
    "金": {"性": "义", "象": "肃杀收敛", "体": "肺大肠", "色": "白银", "方": "西方",
           "personality": "性格刚毅果断，重义气，有魄力。金主义，处事公正，不畏强权。"},
    "水": {"性": "智", "象": "润下流通", "体": "肾膀胱", "色": "黑蓝", "方": "北方",
           "personality": "聪明机智，善于变通，思维敏捷。水主智，观察力强，善于谋略。"},
}

# 十二长生状态 → 自然语言描述
# 用于旺衰叙述中"得令"部分的十二长生状态转译
# 如：帝旺→"当令极旺"，绝→"绝地无根"
_DELING_DESC = {
    "帝旺": "当令极旺", "临官": "得令而旺", "冠带": "渐入佳境",
    "长生": "得气初生", "沐浴": "得令但不稳", "墓": "入墓收藏",
    "死": "失令无气", "绝": "绝地无根", "胎": "胎中待发",
    "养": "养地蓄势", "衰": "过旺转衰", "病": "气衰力弱",
}

# 月支 → 季节描述（初春/仲春/暮春等）
# 用于叙述中"生于X月"的季节补充说明
_MONTH_ZHI_SEASON = {
    "寅": "初春", "卯": "仲春", "辰": "暮春",
    "巳": "初夏", "午": "仲夏", "未": "暮夏",
    "申": "初秋", "酉": "仲秋", "戌": "暮秋",
    "亥": "初冬", "子": "仲冬", "丑": "暮冬",
}

# PLACEHOLDER_CONTINUE


def narrate_analysis(result: dict) -> dict:
    """从完整分析结果生成各维度叙述文本。

    本函数是叙述器的唯一公开入口，负责从 result dict 中提取各维度数据，
    分发给对应的内部叙述函数，最终汇总为 9 维度文本 + 古籍引用列表。

    零幻觉保证：每个叙述函数只读取 result 中已有的计算结果，
    不做任何额外的命理推断或数据编造。

    Args:
        result: run_analysis() 返回的完整 dict，必须包含以下顶层键：
            - validation: 包含 day_master, bazi, gender 等基础信息
            - strength: 包含 wangshuai(旺衰判定), deling(得令), dedi(得地), deshi(得势)
            - pattern: 包含 pattern(格局名), layer(筛查层级), confidence(置信度)
            - yongshen: 包含 yongshen(用神), xishen(喜神), jishen(忌神), trace(推导路径)
            - elements: 包含 percent(五行百分比) 和 percent_adjusted
            - relations: 刑冲合害关系列表，每项含 type, elements, result
            - retrieval: 古籍检索结果，含 results 列表

    Returns:
        {
            "overview": str,       # 命局总览（2-3句）
            "strength": str,       # 旺衰分析段落（得令/得地/得势三要素）
            "pattern": str,        # 格局判定段落（含层级和置信度）
            "yongshen": str,       # 喜用神段落（含推导方法和方向建议）
            "tiaohou": str,        # 调候分析段落（引用穷通宝鉴）
            "elements": str,       # 五行分析段落（含力量分布可视化）
            "relations": str,      # 刑冲合害段落（逐条列出）
            "personality": str,    # 性格推断段落（基于日主五行+旺衰+格局）
            "career": str,         # 事业方向段落（基于用神五行+格局）
            "citations": list,     # 引用的古籍条文（最多5条，含来源/原文/相关度）
        }
    """
    # ── 提取各维度数据，键名必须与 core 计算模块输出一致 ──
    validation = result.get("validation", {})
    strength = result.get("strength", {})
    pattern_info = result.get("pattern", {})
    yongshen_info = result.get("yongshen", {})
    elements = result.get("elements", {})
    relations = result.get("relations", [])
    retrieval = result.get("retrieval", {})

    # 基础信息提取
    day_master = validation.get("day_master", "")       # 日主天干，如"甲"
    bazi = validation.get("bazi", "")                    # 四柱字符串，如"甲子 丙寅 戊辰 庚午"
    gender = validation.get("gender", "")                # 性别
    bazi_parts = bazi.split() if bazi else []            # 拆分为四柱列表
    month_zhi = bazi_parts[1][1] if len(bazi_parts) >= 2 and len(bazi_parts[1]) >= 2 else ""  # 月支
    dm_wx = GAN_WUXING.get(day_master, "")              # 日主五行，如"木"

    # ── 分发到各维度叙述函数 ──
    sections = {}
    sections["overview"] = _narrate_overview(day_master, dm_wx, month_zhi, gender,
                                             strength, pattern_info, yongshen_info)
    sections["strength"] = _narrate_strength(day_master, dm_wx, month_zhi, strength)
    sections["pattern"] = _narrate_pattern(day_master, dm_wx, bazi_parts, pattern_info)
    sections["yongshen"] = _narrate_yongshen(day_master, dm_wx, month_zhi,
                                              pattern_info, yongshen_info)
    sections["tiaohou"] = _narrate_tiaohou(day_master, month_zhi, dm_wx, bazi_parts)
    sections["elements"] = _narrate_elements(dm_wx, elements)
    sections["relations"] = _narrate_relations(relations, bazi_parts, day_master)
    sections["personality"] = _narrate_personality(dm_wx, day_master, strength, pattern_info)
    sections["career"] = _narrate_career(dm_wx, yongshen_info, pattern_info, gender)
    sections["citations"] = _extract_citations(retrieval)

    return sections


# ─── 各维度叙述函数 ───────────────────────────────────────────────────────────

def _narrate_overview(day_master, dm_wx, month_zhi, gender, strength, pattern_info, yongshen_info):
    """生成命局总览（2-3句），概括日主、旺衰、格局、用神。

    Args:
        day_master: 日主天干（如"甲"）
        dm_wx: 日主五行（如"木"）
        month_zhi: 月支（如"寅"）
        gender: 性别
        strength: 旺衰数据，取 strength["wangshuai"]["verdict"]
        pattern_info: 格局数据，取 pattern_info["pattern"]
        yongshen_info: 用神数据，取 yongshen_info["yongshen"]

    Returns:
        str: 命局总览文本，如"甲木日主，生于初春寅月，木气当令。日主身旺，取正官格。用神取金，以平衡命局。"
    """
    ws = strength.get("wangshuai", {})
    verdict = ws.get("verdict", "")          # 旺衰判定结果，如"身旺"/"身弱"/"极旺"
    pattern = pattern_info.get("pattern", "") # 格局名，如"正官格"
    yongshen = yongshen_info.get("yongshen", "")  # 用神五行，如"金"
    season = _MONTH_ZHI_SEASON.get(month_zhi, "") # 季节描述
    month_wx = ZHI_WUXING.get(month_zhi, "")      # 月令五行

    lines = []
    lines.append(f"{day_master}{dm_wx}日主，生于{season}{month_zhi}月，{month_wx}气当令。")
    if verdict:
        lines.append(f"日主{verdict}，")
    if pattern:
        lines[-1] += f"取{pattern}。"
    if yongshen:
        lines.append(f"用神取{yongshen}，以平衡命局。")
    return "".join(lines)


def _narrate_strength(day_master, dm_wx, month_zhi, strength):
    """生成旺衰分析段落，详细阐述得令/得地/得势三要素。

    叙述结构：
        1. 得令：日主在月令的十二长生状态及得分
        2. 得地：地支藏干中的根气及得分
        3. 得势：天干同党帮扶及得分
        4. 综合：三要素汇总与旺衰判定

    Args:
        day_master: 日主天干
        dm_wx: 日主五行
        month_zhi: 月支
        strength: 旺衰数据，含 wangshuai/deling/dedi/deshi 四个子字典

    Returns:
        str: 旺衰分析多行文本
    """
    ws = strength.get("wangshuai", {})
    deling = strength.get("deling", {})   # 得令数据：status(十二长生), score(得分)
    dedi = strength.get("dedi", {})       # 得地数据：score(得分), details(根气列表)
    deshi = strength.get("deshi", {})     # 得势数据：score(得分), details(帮扶列表)

    deling_status = deling.get("status", "")    # 十二长生状态，如"帝旺"/"绝"
    deling_score = deling.get("score", 0)       # 得令得分，正=得令，负=失令
    dedi_score = dedi.get("score", 0)           # 得地得分
    deshi_score = deshi.get("score", 0)         # 得势得分
    verdict = ws.get("verdict", "")             # 综合判定，如"身旺"/"身弱"
    season = _MONTH_ZHI_SEASON.get(month_zhi, "")
    month_wx = ZHI_WUXING.get(month_zhi, "")

    lines = []

    # 得令叙述：根据得分正负区分得令/失令/中平
    deling_desc = _DELING_DESC.get(deling_status, deling_status)
    if deling_score > 0:
        lines.append(f"【得令】{day_master}{dm_wx}生于{month_zhi}月（{season}），"
                     f"月令{month_wx}气，{day_master}处{deling_status}之地，{deling_desc}（+{deling_score}）。")
    elif deling_score < 0:
        lines.append(f"【得令】{day_master}{dm_wx}生于{month_zhi}月（{season}），"
                     f"月令{month_wx}气，{day_master}处{deling_status}之地，{deling_desc}（{deling_score}）。不得令。")
    else:
        # 得分为0：令气中平（如土日主生于辰戌丑未月的部分情况）
        lines.append(f"【得令】{day_master}{dm_wx}生于{month_zhi}月，{day_master}处{deling_status}之地，令气中平。")

    # 得地叙述：列出地支藏干中的根气
    dedi_details = dedi.get("details", [])  # 每项含 zhi(地支), canggan_gan(藏干), qi_level(气分)
    if dedi_details:
        roots = "、".join(f"{d['zhi']}藏{d['canggan_gan']}（{d['qi_level']}）" for d in dedi_details)
        lines.append(f"【得地】地支有根：{roots}。得地分 {dedi_score:.1f}。")
    else:
        lines.append(f"【得地】地支无{dm_wx}之根气，不得地。")

    # 得势叙述：列出天干同党帮扶
    deshi_details = deshi.get("details", [])  # 每项含 gan(天干), shishen(十神)
    if deshi_score > 0:
        helpers = "、".join(f"{d.get('gan', '')}{d.get('shishen', '')}" for d in deshi_details if d.get("gan"))
        if helpers:
            lines.append(f"【得势】天干有{helpers}帮扶，得势分 {deshi_score:.1f}。")
        else:
            lines.append(f"【得势】得势分 {deshi_score:.1f}。")
    else:
        lines.append("【得势】天干无同党帮扶，不得势。")

    # 综合判定
    lines.append(f"综合三要素：得令{deling_score}，得地{dedi_score:.1f}，得势{deshi_score:.1f}。判定：{verdict}。")

    return "\n".join(lines)


def _narrate_pattern(day_master, dm_wx, bazi_parts, pattern_info):
    """生成格局判定段落，含筛查层级和置信度评估。

    格局筛查层级（与 patterns.py screen_pattern() 对应）：
        L0: 特殊格局（专旺/化气/从格/两行成象）
        L1: 月令本气透干（正格或建禄月劫）
        L2: 月令中气透干（正格或建禄月劫）
        L3: 暗格/比劫月令（羊刃/比劫月令/暗格）

    置信度阈值（与 patterns.py 的 confidence 语义一致）：
        ≥0.85: 高 — 格局成立条件充分
        ≥0.60: 中 — 格局基本成立
        <0.60: 低 — 需结合大运验证

    Args:
        day_master: 日主天干
        dm_wx: 日主五行
        bazi_parts: 四柱列表
        pattern_info: 格局数据，含 pattern/layer/confidence/reason

    Returns:
        str: 格局判定多行文本
    """
    pattern = pattern_info.get("pattern", "")           # 格局名，如"正官格"/"从财格"
    layer = pattern_info.get("layer", -1)               # 筛查层级 0-3
    confidence = pattern_info.get("confidence", 0)      # 置信度 0-1
    reason = pattern_info.get("reason", "")             # 判定依据文本

    if not pattern:
        return "格局未能判定，数据不足。"

    lines = []

    # 层级名称映射 — 与 patterns.py screen_pattern() 的层级对应
    # L0: 专旺/化气/从格/两行成象（特殊格局）
    # L1: 月令本气透干（正格或建禄月劫）
    # L2: 月令中气透干（正格或建禄月劫）
    # L3: 羊刃/比劫月令/暗格
    layer_names = {0: "特殊格局", 1: "月令本气透干", 2: "月令中气透干", 3: "暗格/比劫月令"}
    layer_desc = layer_names.get(layer, f"第{layer}层")

    lines.append(f"经四层格局筛查，于{layer_desc}确认格局：{pattern}。")

    # 置信度分级叙述
    if confidence >= 0.85:
        lines.append(f"格局成立条件充分，置信度{confidence:.0%}（高）。")
    elif confidence >= 0.6:
        lines.append(f"格局基本成立，置信度{confidence:.0%}（中）。")
    else:
        lines.append(f"格局成立条件不完全充分，置信度{confidence:.0%}（低），需结合大运验证。")

    if reason:
        lines.append(f"判定依据：{reason}")

    return "\n".join(lines)


def _narrate_yongshen(day_master, dm_wx, month_zhi, pattern_info, yongshen_info):
    """生成喜用神段落，区分格局用神法与旺衰扶抑法。

    用神推导有两种路径（由 yongshen_info["trace"]["method"] 标识）：
        - pattern_based: 格局用神法，根据格局类型确定用神方向
          （如正官格取财印为用，七杀格取食伤制杀为用）
        - wangshuai_fallback: 旺衰扶抑法，当格局用神不明确时的兜底方案
          （身旺克泄耗，身弱生扶）

    Args:
        day_master: 日主天干
        dm_wx: 日主五行
        month_zhi: 月支
        pattern_info: 格局数据（用于获取格局名）
        yongshen_info: 用神数据，含 yongshen/xishen/jishen/trace

    Returns:
        str: 用神分析多行文本，含推导方法、喜忌神、方位建议
    """
    yongshen = yongshen_info.get("yongshen", "")            # 用神五行，如"金"
    xishen = yongshen_info.get("xishen", [])                # 喜神五行列表，如["水", "金"]
    jishen = yongshen_info.get("jishen", [])                # 忌神五行列表，如["木", "火"]
    pattern_basis = yongshen_info.get("pattern_basis", "")  # 用神所基于的格局名
    trace = yongshen_info.get("trace", {})                  # 推导路径追踪
    method = trace.get("method", "")                        # 推导方法：pattern_based / wangshuai_fallback
    trace_reason = trace.get("reason", "")                  # 推导原因文本

    if not yongshen:
        return "用神待定，需更多信息。"

    lines = []

    # 根据推导方法生成不同的叙述
    if method == "pattern_based":
        # 格局用神法：如"正官格取财印为用"
        lines.append(f"用神推导基于格局「{pattern_basis}」。{trace_reason}。")
    elif method == "wangshuai_fallback":
        # 旺衰扶抑法：身旺克泄耗，身弱生扶
        lines.append(f"格局用神不明确，以旺衰扶抑法取用。{trace_reason}。")
    else:
        lines.append(f"用神：{yongshen}。")
    if xishen:
        lines.append(f"喜神：{'、'.join(xishen)}（生助用神之五行）。")
    if jishen:
        lines.append(f"忌神：{'、'.join(jishen)}（克泄用神之五行）。")

    # 实用建议：基于用神五行的方位/色彩建议
    yongshen_nature = _WUXING_NATURE.get(yongshen, {})
    if yongshen_nature:
        lines.append(f"用神{yongshen}属{yongshen_nature['方']}，利{yongshen_nature['色']}色，"
                     f"宜往{yongshen_nature['方']}发展。")

    return "\n".join(lines)


def _narrate_tiaohou(day_master, month_zhi, dm_wx, bazi_parts):
    """生成调候分析段落，引用《穷通宝鉴》查表结果。

    调候用神 = 根据日主天干和月令地支查表得到的最急需五行。
    调候是辅助参考，不凌驾于格局用神之上。

    叙述逻辑：
        1. 查表获取主调候/辅调候天干
        2. 检查调候用神是否在命局天干中出现
        3. 出现→"调候有情"，未出现→"调候不足，需大运补之"

    古籍依据：《穷通宝鉴》（又名《拦江网》），全部120条已验证一致。

    Args:
        day_master: 日主天干
        month_zhi: 月支
        dm_wx: 日主五行
        bazi_parts: 四柱列表（用于检查调候用神是否在命局中出现）

    Returns:
        str: 调候分析多行文本，无调候需求时返回空字符串
    """
    tiaohou = lookup_tiaohou(day_master, month_zhi)
    if not tiaohou.get("has_tiaohou"):
        return ""

    tiaohou_gan = tiaohou.get("tiaohou_gan", [])  # 调候用神天干列表，第一位为主
    tiaohou_wx = tiaohou.get("tiaohou_wx", [])     # 对应五行列表
    season = _MONTH_ZHI_SEASON.get(month_zhi, "")

    lines = []
    lines.append(f"【调候】据《穷通宝鉴》，{day_master}{dm_wx}生于{season}{month_zhi}月：")

    # 主调候与辅调候叙述
    if tiaohou_gan:
        primary = tiaohou_gan[0]       # 主调候天干
        primary_wx = tiaohou_wx[0] if tiaohou_wx else ""
        lines.append(f"主调候用{primary}（{primary_wx}），")
        if len(tiaohou_gan) > 1:
            secondary = tiaohou_gan[1]  # 辅调候天干
            secondary_wx = tiaohou_wx[1] if len(tiaohou_wx) > 1 else ""
            lines[-1] += f"辅以{secondary}（{secondary_wx}）。"
        else:
            lines[-1] = lines[-1].rstrip("，") + "。"

    # 检查调候用神是否在八字天干中出现
    all_gan = [p[0] for p in bazi_parts if len(p) >= 1]  # 提取四柱天干
    present = [g for g in tiaohou_gan if g in all_gan]    # 命局中有的调候用神
    absent = [g for g in tiaohou_gan if g not in all_gan] # 命局中缺的调候用神

    if present:
        lines.append(f"命局天干见{'、'.join(present)}，调候有情。")
    if absent:
        lines.append(f"命局不见{'、'.join(absent)}，调候不足，需大运补之。")

    return "\n".join(lines)


def _narrate_elements(dm_wx, elements):
    """生成五行力量分布段落，含可视化条形图和偏旺/偏弱提示。

    可视化方式：每个五行用 █ 字符表示力量，每5%一个█，0%用░表示。
    偏旺阈值：>35% 标记为"偏旺"
    偏弱阈值：<8% 标记为"极弱"/"命局短板"

    注意：使用 percent（原始百分比），不用 percent_adjusted（合化修正后），
    因为叙述面向用户，原始数据更直观。

    Args:
        dm_wx: 日主五行（用于标注"日主"）
        elements: 五行数据，含 percent 子字典 {"木": 25.0, "火": 15.0, ...}

    Returns:
        str: 五行分析多行文本，无数据时返回空字符串
    """
    percent = elements.get("percent", {})
    if not percent or all(v == 0 for v in percent.values()):
        return ""

    # 按力量从大到小排序
    sorted_wx = sorted(percent.items(), key=lambda x: x[1], reverse=True)
    strongest = sorted_wx[0]   # 最旺五行
    weakest = sorted_wx[-1]    # 最弱五行

    lines = []
    lines.append("【五行力量分布】")
    for wx, pct in sorted_wx:
        bar = "█" * int(pct / 5) if pct > 0 else "░"  # 每5%一个█
        role = ""
        if wx == dm_wx:
            role = "（日主）"
        lines.append(f"  {wx}{role}: {pct:.1f}% {bar}")

    lines.append("")
    # 偏旺提示：力量>35%视为偏旺
    if strongest[1] > 35:
        lines.append(f"{strongest[0]}气偏旺（{strongest[1]:.0f}%），命局偏{strongest[0]}。")
    # 偏弱提示：力量<8%视为极弱
    if weakest[1] < 8:
        lines.append(f"{weakest[0]}气极弱（{weakest[1]:.0f}%），为命局短板。")

    return "\n".join(lines)


def _narrate_relations(relations, bazi_parts, day_master):
    """生成刑冲合害关系段落，逐条列出命局中的干支关系。

    关系类型与默认描述：
        - 冲：主变动，具体吉凶需看所冲之神的喜忌
        - 合：合而有情，具体吉凶需看所合之神的喜忌
        - 刑：刑主纠纷，具体吉凶需看所刑之神的喜忌
        - 害：害主暗损，具体吉凶需看所害之神的喜忌

    注意：relations 列表中每项的 "result" 键存储关系描述，
    若 result 为空则使用默认描述。键名 "result" 与 core/relations.py 输出一致。

    Args:
        relations: 刑冲合害关系列表，每项含 type(关系类型)/elements(参与元素)/result(描述)
        bazi_parts: 四柱列表
        day_master: 日主天干

    Returns:
        str: 刑冲合害多行文本，无关系时返回平稳提示
    """
    if not relations:
        return "命局地支无明显刑冲合害关系，干支配合平稳。"

    lines = []
    lines.append(f"命局检测到 {len(relations)} 组刑冲合害关系：")

    for rel in relations:
        rtype = rel.get("type", "")          # 关系类型：冲/合/刑/害
        elements = rel.get("elements", [])   # 参与的地支列表
        desc = rel.get("result", "")         # 关系描述（键名 result 与 core/relations.py 一致）
        elem_str = "、".join(elements) if elements else ""

        # 根据关系类型生成不同默认描述
        if "冲" in rtype:
            lines.append(f"• {elem_str}相冲 — {desc or '主变动，具体吉凶需看所冲之神的喜忌。'}")
        elif "合" in rtype:
            lines.append(f"• {elem_str}相合 — {desc or '合而有情，具体吉凶需看所合之神的喜忌。'}")
        elif "刑" in rtype:
            lines.append(f"• {elem_str}相刑 — {desc or '刑主纠纷，具体吉凶需看所刑之神的喜忌。'}")
        elif "害" in rtype:
            lines.append(f"• {elem_str}相害 — {desc or '害主暗损，具体吉凶需看所害之神的喜忌。'}")
        else:
            lines.append(f"• {elem_str}{rtype} — {desc}")

    return "\n".join(lines)


def _narrate_personality(dm_wx, day_master, strength, pattern_info):
    """生成性格推断段落，基于日主五行属性、旺衰状态和格局类型。

    叙述逻辑：
        1. 日主五行→基本性格（来自 _WUXING_NATURE）
        2. 旺衰状态→性格倾向修正（旺则突出，弱则内敛）
        3. 格局类型→格局性格（精确匹配，避免子串误匹配）

    格局匹配规则（重要）：
        - 必须先匹配更具体的格局名（如"伤官格"含"官"，须先于"正官"匹配）
        - "伤官"须在"官"之前检查，"七杀/偏官"须在"正官"之前检查
        - "偏财"须在"正财"之前检查，"偏印/枭神"须在"正印"之前检查
        - has_tou 判断：'，透' in pattern 表示有透干取用（如"建禄格，透财"）
        - 排除"无...透出"的情况

    Args:
        dm_wx: 日主五行
        day_master: 日主天干
        strength: 旺衰数据
        pattern_info: 格局数据

    Returns:
        str: 性格推断多行文本
    """
    nature = _WUXING_NATURE.get(dm_wx, {})
    if not nature:
        return ""

    ws = strength.get("wangshuai", {})
    verdict = ws.get("verdict", "")
    pattern = pattern_info.get("pattern", "")

    lines = []
    # 基本性格：基于日主五行
    lines.append(f"日主{day_master}属{dm_wx}，{dm_wx}之性为{nature['性']}。{nature['personality']}")

    # 旺衰性格修正：旺则五行之性更突出，弱则内敛
    if "旺" in verdict or "强" in verdict:
        lines.append(f"日主偏旺，{dm_wx}性更为突出——主见强，不易妥协，行事果敢。")
    elif "弱" in verdict:
        lines.append(f"日主偏弱，{dm_wx}性内敛——心思细腻，善于观察，但决断力稍欠。")

    # 格局性格描述 — 必须精确匹配，避免子串误匹配（如"伤官格"含"官"）
    # 先匹配更具体的格局名，再匹配通用
    # 注意排除"无...透出"的情况（如"建禄格，无财官煞食透出"）
    has_tou = '，透' in pattern  # 有透干取用
    if "伤官" in pattern:
        lines.append("格取伤官，才华横溢，思维活跃，适合创意、技术或自由职业。")
    elif "七杀" in pattern or "偏官" in pattern:
        lines.append("格取七杀，性格刚毅，有魄力，适合竞争性强的领域。")
    elif "正官" in pattern:
        lines.append("格取官星，为人重规矩、守纪律，适合体制内或管理岗位。")
    elif "官" in pattern and has_tou and "伤" not in pattern and "杀" not in pattern:
        # 兜底：含"官"但有透干且非伤官/七杀（如"建禄格，透官"）
        lines.append("格取官星，为人重规矩、守纪律，适合体制内或管理岗位。")
    elif "偏财" in pattern:
        lines.append("格取偏财，善于交际，灵活多变，适合商业投资。")
    elif "正财" in pattern:
        lines.append("格取财星，务实重利，善于经营，对金钱敏感。")
    elif "财" in pattern and has_tou and "偏" not in pattern:
        # 兜底：含"财"但有透干且非偏财
        lines.append("格取财星，务实重利，善于经营，对金钱敏感。")
    elif "食神" in pattern:
        lines.append("格取食神，温和有礼，才华内敛，适合文艺、餐饮或教育。")
    elif "偏印" in pattern or "枭神" in pattern:
        lines.append("格取偏印，思维独特，善于钻研，适合研究或偏门领域。")
    elif "正印" in pattern:
        lines.append("格取印星，好学深思，重精神世界，适合学术、教育或文化领域。")
    elif "印" in pattern and has_tou and "偏" not in pattern:
        # 兜底：含"印"但有透干且非偏印
        lines.append("格取印星，好学深思，重精神世界，适合学术、教育或文化领域。")
    elif "建禄" in pattern or "月劫" in pattern:
        # 建禄月劫格：《子平真诠》"建禄月劫，无官煞则用食伤"
        lines.append("格取建禄月劫，身旺有力，须看透干取用，宜开拓进取。")
    elif "羊刃" in pattern:
        # 羊刃格：《子平真诠》"阳刃喜官杀制伏"
        lines.append("格取羊刃，刚毅果决，需官杀制伏，宜武职或竞争性领域。")
    elif "从财" in pattern:
        lines.append("格取从财，顺势而为，善于把握机遇，适合商业投资。")
    elif "从官" in pattern or "从杀" in pattern:
        lines.append("格取从官杀，顺从权威，适合体制内或大平台发展。")
    elif "从儿" in pattern:
        lines.append("格取从儿，才华外露，适合创作、技术或自由职业。")
    elif "从势" in pattern:
        lines.append("格取从势，随势而动，适合顺势行业，不宜逆势。")
    elif "从强" in pattern:
        lines.append("格取从强，印比成势，适合自主创业或深耕专业。")
    elif "专旺" in pattern or "润下" in pattern or "炎上" in pattern or "稼穑" in pattern or "从革" in pattern or "曲直" in pattern:
        lines.append("格取专旺，一行独秀，气势磅礴，适合深耕本行或自主创业。")
    elif "化气" in pattern or "化木" in pattern or "化火" in pattern or "化土" in pattern or "化金" in pattern or "化水" in pattern:
        lines.append("格取化气，变化之象，适合创新领域或跨界发展。")
    elif "成象" in pattern:
        lines.append("格取两行成象，双行并立，适合复合型领域。")

    return "\n".join(lines)


def _narrate_career(dm_wx, yongshen_info, pattern_info, gender):
    """生成事业方向段落，基于用神五行和格局类型。

    事业方向推导逻辑：
        1. 用神五行→方位建议 + 适合行业（来自 _WUXING_INDUSTRY）
        2. 格局类型→职业倾向（与性格叙述的格局匹配规则一致）

    行业分类基于五行类象的传统对应关系，非特定古籍单条。

    Args:
        dm_wx: 日主五行
        yongshen_info: 用神数据
        pattern_info: 格局数据
        gender: 性别

    Returns:
        str: 事业方向多行文本，无用神时返回空字符串
    """
    yongshen = yongshen_info.get("yongshen", "")
    pattern = pattern_info.get("pattern", "")

    if not yongshen:
        return ""

    # 用神五行→行业对应表（基于五行类象的传统对应关系）
    _WUXING_INDUSTRY = {
        "木": "教育、出版、文化、园林、中医、服装、家具",
        "火": "科技、电子、传媒、餐饮、能源、美容、演艺",
        "土": "房地产、建筑、农业、矿业、仓储、殡葬、陶瓷",
        "金": "金融、法律、机械、汽车、军警、五金、IT硬件",
        "水": "贸易、物流、旅游、水利、渔业、酒水、咨询",
    }

    lines = []
    industry = _WUXING_INDUSTRY.get(yongshen, "")
    nature = _WUXING_NATURE.get(yongshen, {})

    lines.append(f"用神为{yongshen}，事业宜往{nature.get('方', '')}方向发展。")
    if industry:
        lines.append(f"适合行业：{industry}。")

    # 格局事业描述 — 精确匹配，避免子串误匹配（规则同性格叙述）
    has_tou = '，透' in pattern  # 有透干取用
    if "伤官" in pattern:
        lines.append("格局带伤官，适合技术、创作、教学类工作，靠才华立身。")
    elif "食神" in pattern:
        lines.append("格局带食神，适合文艺、餐饮、教育类工作，温和立身。")
    elif "七杀" in pattern or "偏官" in pattern:
        lines.append("格局带七杀，适合竞争性强的领域，有魄力。")
    elif "正官" in pattern:
        lines.append("格局带官杀，适合管理、行政、公职类工作，有领导潜质。")
    elif "官" in pattern and has_tou and "伤" not in pattern and "杀" not in pattern:
        lines.append("格局带官杀，适合管理、行政、公职类工作，有领导潜质。")
    elif "偏财" in pattern:
        lines.append("格局带偏财，适合投资、贸易类工作，善于交际。")
    elif "正财" in pattern:
        lines.append("格局带财星，适合商业、金融、经营类工作，善于积累财富。")
    elif "财" in pattern and has_tou and "偏" not in pattern:
        lines.append("格局带财星，适合商业、金融、经营类工作，善于积累财富。")
    elif "建禄" in pattern or "月劫" in pattern:
        lines.append("格局带建禄月劫，身旺有力，适合自主创业或技术专长类工作。")
    elif "羊刃" in pattern:
        lines.append("格局带羊刃，刚毅果决，适合军警、法律或竞争性强的领域。")
    elif "从财" in pattern:
        lines.append("格局从财，适合商业投资、金融贸易类工作。")
    elif "从官" in pattern or "从杀" in pattern:
        lines.append("格局从官杀，适合体制内、大平台或管理类工作。")
    elif "从儿" in pattern:
        lines.append("格局从儿，适合创作、技术或自由职业类工作。")
    elif "从势" in pattern:
        lines.append("格局从势，适合顺势行业，不宜逆势创业。")
    elif "从强" in pattern:
        lines.append("格局从强，适合自主创业或深耕专业领域。")
    elif "专旺" in pattern or "润下" in pattern or "炎上" in pattern or "稼穑" in pattern or "从革" in pattern or "曲直" in pattern:
        lines.append("格局专旺，适合深耕本行或自主创业。")
    elif "化气" in pattern or "化木" in pattern or "化火" in pattern or "化土" in pattern or "化金" in pattern or "化水" in pattern:
        lines.append("格局化气，适合创新领域或跨界发展。")
    elif "成象" in pattern:
        lines.append("格局两行成象，适合复合型领域。")

    return "\n".join(lines)


def _extract_citations(retrieval):
    """从古籍检索结果中提取引用条文，最多5条。

    每条引用包含：source（来源典籍名）、text（原文片段，截断至200字）、
    relevance（相关度百分比）。

    Args:
        retrieval: 古籍检索数据，含 results 列表，
            每项含 source(典籍名)/text(原文)/score(相关度0-1)

    Returns:
        list[dict]: 引用条文列表，每项含 source/text/relevance
    """
    results = retrieval.get("results", [])
    citations = []
    for item in results[:5]:  # 最多提取5条引用
        source = item.get("source", "")
        text = item.get("text", "")
        score = item.get("score", 0)
        if source and text:
            citations.append({
                "source": source,
                "text": text[:200],     # 截断至200字，避免过长
                "relevance": f"{score * 100:.0f}%" if score else "",
            })
    return citations
