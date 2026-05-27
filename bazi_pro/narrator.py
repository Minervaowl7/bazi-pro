"""
bazi-pro 确定性报告叙述器 (narrator)

从计算结果直接生成专业命理师风格的中文文本。
零 LLM 依赖，零幻觉风险。每句话都可追溯到确定性计算数据。

用法:
    from bazi_pro.narrator import narrate_analysis
    sections = narrate_analysis(result_dict)
    # sections = {"strength": "...", "pattern": "...", "yongshen": "...", ...}
"""

from bazi_pro.core.constants import GAN_WUXING, ZHI_WUXING, derive_shishen
from bazi_pro.core.tiaohou import lookup_tiaohou

# ─── 五行属性描述 ─────────────────────────────────────────────────────────────

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

_DELING_DESC = {
    "帝旺": "当令极旺", "临官": "得令而旺", "冠带": "渐入佳境",
    "长生": "得气初生", "沐浴": "得令但不稳", "墓": "入墓收藏",
    "死": "失令无气", "绝": "绝地无根", "胎": "胎中待发",
    "养": "养地蓄势", "衰": "过旺转衰", "病": "气衰力弱",
}

_MONTH_ZHI_SEASON = {
    "寅": "初春", "卯": "仲春", "辰": "暮春",
    "巳": "初夏", "午": "仲夏", "未": "暮夏",
    "申": "初秋", "酉": "仲秋", "戌": "暮秋",
    "亥": "初冬", "子": "仲冬", "丑": "暮冬",
}

# PLACEHOLDER_CONTINUE


def narrate_analysis(result: dict) -> dict:
    """从完整分析结果生成各维度叙述文本。

    Args:
        result: run_analysis() 返回的完整 dict

    Returns:
        {
            "overview": str,       # 命局总览（2-3句）
            "strength": str,       # 旺衰分析段落
            "pattern": str,        # 格局判定段落
            "yongshen": str,       # 喜用神段落
            "tiaohou": str,        # 调候分析段落
            "elements": str,       # 五行分析段落
            "relations": str,      # 刑冲合害段落
            "personality": str,    # 性格推断段落
            "career": str,         # 事业方向段落
            "citations": list,     # 引用的古籍条文
        }
    """
    validation = result.get("validation", {})
    strength = result.get("strength", {})
    pattern_info = result.get("pattern", {})
    yongshen_info = result.get("yongshen", {})
    elements = result.get("elements", {})
    relations = result.get("relations", [])
    shishen = result.get("shishen", {})
    retrieval = result.get("retrieval", {})

    day_master = validation.get("day_master", "")
    bazi = validation.get("bazi", "")
    gender = validation.get("gender", "")
    bazi_parts = bazi.split() if bazi else []
    month_zhi = bazi_parts[1][1] if len(bazi_parts) >= 2 and len(bazi_parts[1]) >= 2 else ""
    dm_wx = GAN_WUXING.get(day_master, "")

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
    ws = strength.get("wangshuai", {})
    verdict = ws.get("verdict", "")
    pattern = pattern_info.get("pattern", "")
    yongshen = yongshen_info.get("yongshen", "")
    season = _MONTH_ZHI_SEASON.get(month_zhi, "")
    month_wx = ZHI_WUXING.get(month_zhi, "")

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
    ws = strength.get("wangshuai", {})
    deling = strength.get("deling", {})
    dedi = strength.get("dedi", {})
    deshi = strength.get("deshi", {})

    deling_status = deling.get("status", "")
    deling_score = deling.get("score", 0)
    dedi_score = dedi.get("score", 0)
    deshi_score = deshi.get("score", 0)
    verdict = ws.get("verdict", "")
    season = _MONTH_ZHI_SEASON.get(month_zhi, "")
    month_wx = ZHI_WUXING.get(month_zhi, "")

    lines = []

    # 得令
    deling_desc = _DELING_DESC.get(deling_status, deling_status)
    if deling_score > 0:
        lines.append(f"【得令】{day_master}{dm_wx}生于{month_zhi}月（{season}），"
                     f"月令{month_wx}气，{day_master}处{deling_status}之地，{deling_desc}（+{deling_score}）。")
    elif deling_score < 0:
        lines.append(f"【得令】{day_master}{dm_wx}生于{month_zhi}月（{season}），"
                     f"月令{month_wx}气，{day_master}处{deling_status}之地，{deling_desc}（{deling_score}）。不得令。")
    else:
        lines.append(f"【得令】{day_master}{dm_wx}生于{month_zhi}月，{day_master}处{deling_status}之地，令气中平。")

    # 得地
    dedi_details = dedi.get("details", [])
    if dedi_details:
        roots = "、".join(f"{d['zhi']}藏{d['canggan_gan']}（{d['qi_level']}）" for d in dedi_details)
        lines.append(f"【得地】地支有根：{roots}。得地分 {dedi_score:.1f}。")
    else:
        lines.append(f"【得地】地支无{dm_wx}之根气，不得地。")

    # 得势
    deshi_details = deshi.get("details", [])
    if deshi_score > 0:
        helpers = "、".join(f"{d.get('gan', '')}{d.get('relation', '')}" for d in deshi_details if d.get("gan"))
        if helpers:
            lines.append(f"【得势】天干有{helpers}帮扶，得势分 {deshi_score:.1f}。")
        else:
            lines.append(f"【得势】得势分 {deshi_score:.1f}。")
    else:
        lines.append(f"【得势】天干无同党帮扶，不得势。")

    # 综合
    lines.append(f"综合三要素：得令{deling_score}，得地{dedi_score:.1f}，得势{deshi_score:.1f}。判定：{verdict}。")

    return "\n".join(lines)


def _narrate_pattern(day_master, dm_wx, bazi_parts, pattern_info):
    pattern = pattern_info.get("pattern", "")
    layer = pattern_info.get("layer", -1)
    ptype = pattern_info.get("type", "")
    confidence = pattern_info.get("confidence", 0)
    reason = pattern_info.get("reason", "")

    if not pattern:
        return "格局未能判定，数据不足。"

    lines = []

    layer_names = {0: "化气格", 1: "专旺格", 2: "从格", 3: "正格（层1）", 4: "正格（层2）", 5: "正格（层3）"}
    layer_desc = layer_names.get(layer, f"第{layer}层")

    lines.append(f"经六层格局筛查，于{layer_desc}确认格局：{pattern}。")

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
    yongshen = yongshen_info.get("yongshen", "")
    xishen = yongshen_info.get("xishen", [])
    jishen = yongshen_info.get("jishen", [])
    pattern_basis = yongshen_info.get("pattern_basis", "")
    confidence = yongshen_info.get("confidence", 0)
    trace = yongshen_info.get("trace", {})
    method = trace.get("method", "")
    trace_reason = trace.get("reason", "")

    if not yongshen:
        return "用神待定，需更多信息。"

    lines = []

    if method == "pattern_based":
        lines.append(f"用神推导基于格局「{pattern_basis}」。{trace_reason}。")
    elif method == "wangshuai_fallback":
        lines.append(f"格局用神不明确，以旺衰扶抑法取用。{trace_reason}。")
    else:
        lines.append(f"用神：{yongshen}。")

    lines.append(f"用神：{yongshen}。")
    if xishen:
        lines.append(f"喜神：{'、'.join(xishen)}（生助用神之五行）。")
    if jishen:
        lines.append(f"忌神：{'、'.join(jishen)}（克泄用神之五行）。")

    # 实用建议
    yongshen_nature = _WUXING_NATURE.get(yongshen, {})
    if yongshen_nature:
        lines.append(f"用神{yongshen}属{yongshen_nature['方']}，利{yongshen_nature['色']}色，"
                     f"宜往{yongshen_nature['方']}发展。")

    return "\n".join(lines)


def _narrate_tiaohou(day_master, month_zhi, dm_wx, bazi_parts):
    tiaohou = lookup_tiaohou(day_master, month_zhi)
    if not tiaohou.get("has_tiaohou"):
        return ""

    tiaohou_gan = tiaohou.get("tiaohou_gan", [])
    tiaohou_wx = tiaohou.get("tiaohou_wx", [])
    season = _MONTH_ZHI_SEASON.get(month_zhi, "")

    lines = []
    lines.append(f"【调候】据《穷通宝鉴》，{day_master}{dm_wx}生于{season}{month_zhi}月：")

    if tiaohou_gan:
        primary = tiaohou_gan[0]
        primary_wx = tiaohou_wx[0] if tiaohou_wx else ""
        lines.append(f"主调候用{primary}（{primary_wx}），")
        if len(tiaohou_gan) > 1:
            secondary = tiaohou_gan[1]
            secondary_wx = tiaohou_wx[1] if len(tiaohou_wx) > 1 else ""
            lines[-1] += f"辅以{secondary}（{secondary_wx}）。"
        else:
            lines[-1] = lines[-1].rstrip("，") + "。"

    # 检查调候用神是否在八字中出现
    all_gan = [p[0] for p in bazi_parts if len(p) >= 1]
    present = [g for g in tiaohou_gan if g in all_gan]
    absent = [g for g in tiaohou_gan if g not in all_gan]

    if present:
        lines.append(f"命局天干见{'、'.join(present)}，调候有情。")
    if absent:
        lines.append(f"命局不见{'、'.join(absent)}，调候不足，需大运补之。")

    return "\n".join(lines)


def _narrate_elements(dm_wx, elements):
    percent = elements.get("percent", {})
    if not percent or all(v == 0 for v in percent.values()):
        return ""

    sorted_wx = sorted(percent.items(), key=lambda x: x[1], reverse=True)
    strongest = sorted_wx[0]
    weakest = sorted_wx[-1]

    lines = []
    lines.append("【五行力量分布】")
    for wx, pct in sorted_wx:
        bar = "█" * int(pct / 5) if pct > 0 else "░"
        role = ""
        if wx == dm_wx:
            role = "（日主）"
        lines.append(f"  {wx}{role}: {pct:.1f}% {bar}")

    lines.append("")
    if strongest[1] > 35:
        lines.append(f"{strongest[0]}气偏旺（{strongest[1]:.0f}%），命局偏{strongest[0]}。")
    if weakest[1] < 8:
        lines.append(f"{weakest[0]}气极弱（{weakest[1]:.0f}%），为命局短板。")

    return "\n".join(lines)


def _narrate_relations(relations, bazi_parts, day_master):
    if not relations:
        return "命局地支无明显刑冲合害关系，干支配合平稳。"

    lines = []
    lines.append(f"命局检测到 {len(relations)} 组刑冲合害关系：")

    for rel in relations:
        rtype = rel.get("type", "")
        elements = rel.get("elements", [])
        desc = rel.get("description", "")
        elem_str = "、".join(elements) if elements else ""

        if "冲" in rtype:
            lines.append(f"• {elem_str}相冲 — {desc or '动荡不安，主变动。'}")
        elif "合" in rtype:
            lines.append(f"• {elem_str}相合 — {desc or '合而有情，主和顺。'}")
        elif "刑" in rtype:
            lines.append(f"• {elem_str}相刑 — {desc or '刑主灾厄，需防口舌是非。'}")
        elif "害" in rtype:
            lines.append(f"• {elem_str}相害 — {desc or '暗害伤情，主暗损。'}")
        else:
            lines.append(f"• {elem_str}{rtype} — {desc}")

    return "\n".join(lines)


def _narrate_personality(dm_wx, day_master, strength, pattern_info):
    nature = _WUXING_NATURE.get(dm_wx, {})
    if not nature:
        return ""

    ws = strength.get("wangshuai", {})
    verdict = ws.get("verdict", "")
    pattern = pattern_info.get("pattern", "")

    lines = []
    lines.append(f"日主{day_master}属{dm_wx}，{dm_wx}之性为{nature['性']}。{nature['personality']}")

    if "旺" in verdict or "强" in verdict:
        lines.append(f"日主偏旺，{dm_wx}性更为突出——主见强，不易妥协，行事果敢。")
    elif "弱" in verdict:
        lines.append(f"日主偏弱，{dm_wx}性内敛——心思细腻，善于观察，但决断力稍欠。")

    if "官" in pattern:
        lines.append("格取官星，为人重规矩、守纪律，适合体制内或管理岗位。")
    elif "财" in pattern:
        lines.append("格取财星，务实重利，善于经营，对金钱敏感。")
    elif "食" in pattern or "伤" in pattern:
        lines.append("格取食伤，才华横溢，思维活跃，适合创意、技术或自由职业。")
    elif "印" in pattern:
        lines.append("格取印星，好学深思，重精神世界，适合学术、教育或文化领域。")

    return "\n".join(lines)


def _narrate_career(dm_wx, yongshen_info, pattern_info, gender):
    yongshen = yongshen_info.get("yongshen", "")
    pattern = pattern_info.get("pattern", "")

    if not yongshen:
        return ""

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

    if "官" in pattern or "杀" in pattern:
        lines.append("格局带官杀，适合管理、行政、公职类工作，有领导潜质。")
    elif "食" in pattern or "伤" in pattern:
        lines.append("格局带食伤，适合技术、创作、教学类工作，靠才华立身。")
    elif "财" in pattern:
        lines.append("格局带财星，适合商业、金融、经营类工作，善于积累财富。")

    return "\n".join(lines)


def _extract_citations(retrieval):
    results = retrieval.get("results", [])
    citations = []
    for item in results[:5]:
        source = item.get("source", "")
        text = item.get("text", "")
        score = item.get("score", 0)
        if source and text:
            citations.append({
                "source": source,
                "text": text[:200],
                "relevance": f"{score * 100:.0f}%" if score else "",
            })
    return citations
