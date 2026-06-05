"""综合解读智能体

综合八字和紫微斗数的分析结果，生成统一解读。
支持知识图谱历史数据引用。LLM 不可用时返回基于规则的简单综合。
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("bazi-pro.agents.synthesis")

AGENT_NAME = "synthesis"


def _rule_based_synthesis(
    bazi_result: dict,
    ziwei_result: dict,
    knowledge_context: dict | list | None = None,
) -> dict[str, Any]:
    """基于规则的简单综合（LLM 不可用时的降级方案）。"""

    sections: list[str] = []

    bazi_data = bazi_result.get("data", {})
    bazi_core = bazi_data.get("core", {})
    ziwei_data = ziwei_result.get("data", {})
    ziwei_chart = ziwei_data.get("chart", {})

    if bazi_core:
        parts: list[str] = []
        day_master = bazi_core.get("day_master", "")
        if day_master:
            parts.append(f"日主{day_master}")

        ws = bazi_core.get("strength", {}).get("wangshuai", {})
        verdict = ws.get("verdict", "")
        if verdict:
            parts.append(f"旺衰{verdict}")

        pattern = bazi_core.get("pattern", {})
        pattern_name = pattern.get("pattern", "") if isinstance(pattern, dict) else ""
        if pattern_name:
            parts.append(f"格局{pattern_name}")

        yongshen = bazi_core.get("yongshen", {})
        ys = yongshen.get("yongshen", "") if isinstance(yongshen, dict) else ""
        if ys:
            parts.append(f"用神{ys}")

        if parts:
            sections.append("【八字命局】" + "，".join(parts))

    if ziwei_chart:
        parts = []
        soul = ziwei_chart.get("soul", "")
        if soul:
            parts.append(f"命主{soul}")
        body = ziwei_chart.get("body", "")
        if body:
            parts.append(f"身主{body}")
        five_class = ziwei_chart.get("fiveElementsClass", "")
        if five_class:
            parts.append(f"五行局{five_class}")

        palaces = ziwei_chart.get("palaces", [])
        palace_stars: list[str] = []
        for p in palaces:
            if not isinstance(p, dict):
                continue
            name = p.get("name", "")
            stars = [
                s.get("name", "")
                for s in p.get("majorStars", [])
                if isinstance(s, dict) and s.get("name")
            ]
            if stars and name:
                palace_stars.append(f"{name}({'、'.join(stars)})")
        if palace_stars:
            parts.append("宫星: " + "; ".join(palace_stars[:6]))

        if parts:
            sections.append("【紫微命盘】" + "，".join(parts))

    bazi_llm = bazi_data.get("llm_interpretation", "")
    ziwei_llm = ziwei_data.get("llm_interpretation", "")
    if bazi_llm:
        sections.append("【八字解读】" + bazi_llm)
    if ziwei_llm:
        sections.append("【紫微解读】" + ziwei_llm)

    if knowledge_context:
        sections.append("【历史参考】已有知识图谱数据可供综合分析参考。")

    text = "\n\n".join(sections) if sections else "八字和紫微斗数数据不足，无法生成综合解读。"

    return {
        "interpretation": text,
        "bazi_highlights": bazi_result.get("summary", ""),
        "ziwei_highlights": ziwei_result.get("summary", ""),
        "method": "rule_based",
    }


def _build_synthesis_prompt(
    bazi_result: dict,
    ziwei_result: dict,
    knowledge_context: dict | list | None = None,
) -> str:
    parts: list[str] = []

    bazi_data = bazi_result.get("data", {})
    bazi_core = bazi_data.get("core", {})
    if bazi_core:
        bazi_text = json.dumps(bazi_core, ensure_ascii=False, indent=2)
        if len(bazi_text) > 6000:
            bazi_text = bazi_text[:6000] + "\n...(已截断)"
        parts.append(f"## 八字分析结果\n{bazi_text}")

    bazi_narration = bazi_data.get("narration", {})
    if bazi_narration:
        narration_text = json.dumps(bazi_narration, ensure_ascii=False, indent=2)
        parts.append(f"## 八字确定性叙述\n{narration_text}")

    ziwei_data = ziwei_result.get("data", {})
    ziwei_chart = ziwei_data.get("chart", {})
    if ziwei_chart:
        ziwei_text = json.dumps(ziwei_chart, ensure_ascii=False, indent=2)
        if len(ziwei_text) > 6000:
            ziwei_text = ziwei_text[:6000] + "\n...(已截断)"
        parts.append(f"## 紫微斗数命盘\n{ziwei_text}")

    if knowledge_context:
        kc_text = json.dumps(knowledge_context, ensure_ascii=False, indent=2)
        if len(kc_text) > 3000:
            kc_text = kc_text[:3000] + "\n...(已截断)"
        parts.append(f"## 知识图谱历史数据\n{kc_text}")

    return "\n\n".join(parts)


class SynthesisAgent:
    """综合解读智能体

    综合八字和紫微斗数结果，生成跨术数的统一解读。
    有 LLM 时调用 LLM 深度综合；无 LLM 时返回规则综合。
    """

    async def analyze(
        self,
        bazi_result: dict,
        ziwei_result: dict,
        knowledge_context: dict | list | None = None,
    ) -> dict[str, Any]:
        """生成综合解读。

        Args:
            bazi_result: 八字智能体的标准输出
            ziwei_result: 紫微斗数智能体的标准输出
            knowledge_context: 可选的知识图谱历史数据

        Returns:
            标准智能体输出::

                {
                    "agent": "synthesis",
                    "status": "success" | "error",
                    "data": { ... },
                    "summary": "综合解读",
                    "timestamp": "ISO8601"
                }
        """
        try:
            from server.llm import is_llm_configured

            if is_llm_configured():
                return await self._llm_synthesis(
                    bazi_result, ziwei_result, knowledge_context
                )
        except ImportError:
            pass

        data = _rule_based_synthesis(bazi_result, ziwei_result, knowledge_context)
        return {
            "agent": AGENT_NAME,
            "status": "success",
            "data": data,
            "summary": data.get("interpretation", "")[:200],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _llm_synthesis(
        self,
        bazi_result: dict,
        ziwei_result: dict,
        knowledge_context: dict | list | None = None,
    ) -> dict[str, Any]:
        from server.llm import chat_completion

        user_prompt = _build_synthesis_prompt(bazi_result, ziwei_result, knowledge_context)

        system_prompt = (
            "你是一位精通八字命理和紫微斗数的资深命理大师。\n"
            "你需要综合八字和紫微斗数两套术数的分析结果，为命主提供统一的命理解读。\n\n"
            "要求：\n"
            "1. 找出八字和紫微斗数的共同指向（如两者都认为事业运好）\n"
            "2. 指出两套术数的互补信息（八字看五行旺衰，紫微看星曜组合）\n"
            "3. 若有矛盾之处，客观说明两套体系的不同视角\n"
            "4. 如有知识图谱历史数据，引用相似命格的历史案例\n"
            "5. 给出综合性的建议\n"
            "6. 语言风格：专业、沉稳、有温度\n"
            "7. 篇幅控制在 500-800 字\n"
            "8. 不要编造命盘中没有的信息"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        llm_text = await chat_completion(messages, temperature=0.6, max_tokens=4096)

        data: dict[str, Any] = {
            "interpretation": llm_text,
            "bazi_highlights": bazi_result.get("summary", ""),
            "ziwei_highlights": ziwei_result.get("summary", ""),
            "method": "llm",
        }
        if knowledge_context:
            data["knowledge_used"] = True

        return {
            "agent": AGENT_NAME,
            "status": "success",
            "data": data,
            "summary": llm_text[:200] if llm_text else "综合解读完成",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
