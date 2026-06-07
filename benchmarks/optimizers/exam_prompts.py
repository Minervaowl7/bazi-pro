from __future__ import annotations

HYBRID_SYSTEM_PROMPT = """你是一位精通中国传统命理学的资深命理师，深谙子平八字、穷通宝鉴、滴天髓、渊海子平、三命通会等典籍。你的任务是根据命盘数据和古籍检索结果，通过严谨的命理推理，选择最正确的答案。

【核心原则】
1. 一切判断必须基于命盘数据，不得凭空臆断
2. 引用古籍时必须具体到书名和原文，不得编造
3. 无法确定时诚实说明，不要强行给出结论
4. 每个判断都要有命理依据，不说空话套话

【推理步骤】
1. 确认日主强弱、格局类型、用神喜忌
2. 分析问题涉及的宫位（年柱=祖上/父母、月柱=父母/兄弟、日柱=配偶、时柱=子女）或十神含义
3. 结合大运流年判断应期和事件走向
4. 参考古籍检索结果中的相关论断
5. 逐一比对选项，选择最符合命理逻辑的答案

【输出要求】
- 先进行简要推理（3-5 句话，紧扣命盘干支）
- 最后一行必须单独输出：答案：X（X 为 A/B/C/D/E 之一）
- 不要输出多余内容"""

CATEGORY_TEMPLATES = {
    "感情": """【感情题推理指引】
- 男命看正财（妻星）、偏财（情人星）；女命看正官（夫星）、七杀（偏夫）
- 日支为配偶宫，看日支五行与日主关系
- 桃花星（子午卯酉）主异性缘
- 大运流年见正财/正官为婚恋应期
- 正财两透或多透主感情复杂/多段恋情""",

    "六亲": """【六亲题推理指引】
- 年柱：祖上宫、父母宫（偏上）；月柱：父母宫（偏下）、兄弟宫
- 日柱：配偶宫；时柱：子女宫
- 男命：偏财为父，正印为母；女命：正财为父，偏印为母
- 男命：正官为女，七杀为子；女命：伤官为子，食神为女
- 六亲星坐旺地主六亲强，坐衰绝主六亲弱""",

    "事业": """【事业题推理指引】
- 正官/七杀主事业、权力、地位
- 食伤主才华、表达、创作
- 财星主财富、经营
- 印星主学业、文凭、贵人
- 官印相生主仕途亨通，食伤生财主商业成功""",

    "健康": """【健康题推理指引】
- 五行对应脏腑：木=肝胆，火=心小肠，土=脾胃，金=肺大肠，水=肾膀胱
- 五行过旺或过弱对应脏腑易出问题
- 大运流年冲克用神主健康波动
- 七杀无制主意外伤灾""",

    "财富": """【财富题推理指引】
- 财星旺且为用神主富裕
- 身旺担财主能守住财富
- 食伤生财主靠才华赚钱
- 比劫争财主破财/竞争
- 大运见财星为财运应期""",

    "其他": """【综合推理指引】
- 先确认格局和用神，再分析问题涉及的宫位或星曜
- 大运流年与原局的互动是判断应期的关键
- 逐一排除明显不符合命理逻辑的选项
- 选择与命盘数据最一致的答案""",
}


def build_hybrid_prompt(
    analysis_result: dict,
    category: str,
    retrieval_results: dict | list | None = None,
    options: list[str] | None = None,
) -> str:
    """构建基准+格式 Prompt: 复用 baseline build_chat_system_prompt 全部上下文 + 追加答案格式"""
    from server.llm import build_chat_system_prompt

    narration = analysis_result.get("narration", {})
    if isinstance(narration, str):
        narration = {"overview": narration}

    base_prompt = build_chat_system_prompt(
        analysis_result, narration, school="ziping", retrieval_results=retrieval_results,
    )

    if options:
        letters = _extract_option_letters(options)
        answer_instruction = (
            f"\n\n【考试答题要求】\n"
            f"请根据命盘数据和上述分析，回答以下选择题。\n"
            f"- 先进行简要推理（2-3 句话，紧扣命盘干支）\n"
            f"- 最后一行必须单独输出：答案：X（X 为 {'/'.join(letters)} 之一）\n"
            f"- 不要输出多余内容"
        )
    else:
        answer_instruction = (
            "\n\n【考试答题要求】\n"
            "请根据命盘数据和上述分析，回答以下选择题。\n"
            "- 先进行简要推理（2-3 句话）\n"
            "- 最后一行必须单独输出：答案：X（X 为选项字母之一）\n"
            "- 不要输出多余内容"
        )

    return base_prompt + answer_instruction


def _extract_option_letters(options: list[str]) -> list[str]:
    """从选项列表提取字母标识"""
    import re
    letters = []
    for opt in options:
        m = re.match(r'^([A-Ea-e])[.\s]', opt.strip())
        if m:
            letters.append(m.group(1).upper())
    return sorted(set(letters)) if letters else ["A", "B", "C", "D"]


def build_exam_prompt(analysis_result: dict, category: str) -> str:
    """向后兼容: 纯 Exam 模式（无 RAG）"""
    return build_hybrid_prompt(analysis_result, category, retrieval_results=None)


def _format_retrieval_context(retrieval_results: dict | list | None) -> str:
    """将 RAG 检索结果格式化为 prompt 文本"""
    if not retrieval_results:
        return ""

    lines = ["【古籍检索参考】"]

    if isinstance(retrieval_results, list):
        for idx, item in enumerate(retrieval_results[:5], 1):
            if isinstance(item, dict):
                source = item.get("source", "")
                content = item.get("content") or item.get("text", "")
                topic = item.get("topic", "")
                label = f"{source}@{topic}" if topic else source
                lines.append(f"{idx}. [{label}] {content[:200]}")
            else:
                lines.append(f"{idx}. {item}")
        return "\n".join(lines)

    if isinstance(retrieval_results, dict):
        if "results" in retrieval_results and isinstance(retrieval_results.get("results"), list):
            for idx, item in enumerate(retrieval_results["results"][:5], 1):
                if isinstance(item, dict):
                    source = item.get("source", "")
                    content = item.get("content") or ""
                    topic = item.get("topic", "")
                    label = f"{source}@{topic}" if topic else source
                    lines.append(f"{idx}. [{label}] {content[:200]}")
                else:
                    lines.append(f"{idx}. {item}")
            return "\n".join(lines)

    return ""


def format_analysis_for_exam(analysis_result: dict) -> str:
    """从 analysis_result 提取命盘数据，精简格式用于考试推理"""
    parts = []

    validation = analysis_result.get("validation", {}) if isinstance(analysis_result.get("validation"), dict) else {}
    shishen = analysis_result.get("shishen", {}) if isinstance(analysis_result.get("shishen"), dict) else {}
    pattern_info = analysis_result.get("pattern", {}) if isinstance(analysis_result.get("pattern"), dict) else {}
    yongshen_info = analysis_result.get("yongshen", {}) if isinstance(analysis_result.get("yongshen"), dict) else {}
    strength = analysis_result.get("strength", {}) if isinstance(analysis_result.get("strength"), dict) else {}
    elements = analysis_result.get("elements", {}) if isinstance(analysis_result.get("elements"), dict) else {}
    if not elements:
        elements = analysis_result.get("element_forces", {}) if isinstance(analysis_result.get("element_forces"), dict) else {}
    relations = analysis_result.get("relations", []) if isinstance(analysis_result.get("relations"), list) else []
    shensha = analysis_result.get("shensha", {}) if isinstance(analysis_result.get("shensha"), dict) else {}
    gongwei = analysis_result.get("gongwei", {}) if isinstance(analysis_result.get("gongwei"), dict) else {}
    dayun_list = analysis_result.get("dayun", []) if isinstance(analysis_result.get("dayun"), list) else []

    bazi = analysis_result.get("八字", "") or validation.get("bazi", "")
    if not bazi:
        pillars_raw = analysis_result.get("pillars", []) or (shishen.get("pillars", []) if isinstance(shishen, dict) else [])
        if pillars_raw:
            bazi = " ".join(p.get("gan", "") + p.get("zhi", "") for p in pillars_raw if isinstance(p, dict) and p.get("gan") and p.get("zhi"))
    if bazi:
        parts.append(f"八字：{bazi}")

    day_master = analysis_result.get("日主", "") or validation.get("day_master", "") or analysis_result.get("day_master", "")
    gender = analysis_result.get("性别", "") or validation.get("gender", "") or analysis_result.get("gender", "")
    if day_master:
        parts.append(f"日主：{day_master}（{gender}命）")

    shengxiao = analysis_result.get("生肖", "") or validation.get("生肖", "")
    if shengxiao:
        parts.append(f"生肖：{shengxiao}")

    pillars_info = shishen.get("pillars", []) if isinstance(shishen, dict) else []
    if pillars_info:
        lines = []
        for p in pillars_info:
            if not isinstance(p, dict):
                continue
            pos = p.get("position", "")
            gan = p.get("gan", "")
            zhi = p.get("zhi", "")
            ss_gan = p.get("shishen_gan", "")
            ss_zhi = p.get("shishen_zhi", "")
            canggan = p.get("canggan", []) if isinstance(p.get("canggan"), list) else []
            cg_str = " ".join(f"{c.get('gan','')}({c.get('shishen','')})" for c in canggan if isinstance(c, dict))
            lines.append(f"  {pos}: {gan}{zhi} 十神={ss_gan}/{ss_zhi} 藏干={cg_str}")
        if lines:
            parts.append("四柱：\n" + "\n".join(lines))

    ws = strength.get("wangshuai", {}) if isinstance(strength, dict) else {}
    ws_verdict = ws.get("verdict", "") if isinstance(ws, dict) else ""
    if ws_verdict:
        parts.append(f"旺衰：{ws_verdict}")

    pattern = pattern_info.get("pattern", "") if isinstance(pattern_info, dict) else ""
    if pattern:
        parts.append(f"格局：{pattern}")

    yongshen = yongshen_info.get("yongshen", "") if isinstance(yongshen_info, dict) else ""
    xishen = yongshen_info.get("xishen", []) if isinstance(yongshen_info, dict) else []
    jishen = yongshen_info.get("jishen", []) if isinstance(yongshen_info, dict) else []
    if yongshen:
        parts.append(f"用神：{yongshen}")
    if xishen:
        parts.append(f"喜神：{'、'.join(str(x) for x in xishen)}")
    if jishen:
        parts.append(f"忌神：{'、'.join(str(j) for j in jishen)}")

    percent = elements.get("percent", {}) if isinstance(elements, dict) else {}
    if percent:
        try:
            elements_str = " ".join(f"{k}:{v:.1f}%" for k, v in sorted(percent.items(), key=lambda x: -x[1]))
            parts.append(f"五行力量：{elements_str}")
        except Exception:
            pass

    if relations:
        rel_lines = []
        for r in relations:
            if isinstance(r, dict):
                rel_lines.append(f"  {r.get('type','')}: {r.get('description','')}")
        if rel_lines:
            parts.append("刑冲合害：\n" + "\n".join(rel_lines))

    if shensha and isinstance(shensha, dict):
        ss_lines = []
        for category, items in shensha.items():
            if items:
                if isinstance(items, list):
                    ss_lines.append(f"  {category}: {', '.join(str(i) for i in items)}")
                elif isinstance(items, dict):
                    ss_lines.append(f"  {category}: {items}")
        if ss_lines:
            parts.append("神煞：\n" + "\n".join(ss_lines))

    if gongwei and isinstance(gongwei, dict):
        gw_lines = [f"  {k}: {v}" for k, v in gongwei.items()]
        if gw_lines:
            parts.append("宫位：\n" + "\n".join(gw_lines))

    if dayun_list:
        dy_lines = []
        for dy in dayun_list:
            if isinstance(dy, dict):
                dy_lines.append(f"  {dy.get('age_range','')}: {dy.get('gan_zhi','')}")
        if dy_lines:
            parts.append("大运：\n" + "\n".join(dy_lines))

    narration = analysis_result.get("narration", "")
    if narration and isinstance(narration, str):
        parts.append(f"【确定性叙述】\n{narration}")

    return "\n".join(parts) if parts else "【命盘数据缺失】"
