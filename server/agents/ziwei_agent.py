"""紫微斗数智能体

调用 server.ziwei.get_ziwei_chart() 生成完整命盘，
可选调用 LLM 生成自然语言解读。
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("bazi-pro.agents.ziwei")

AGENT_NAME = "ziwei"


def _extract_summary(chart: dict) -> str:
    parts: list[str] = []

    soul = chart.get("soul", "")
    body = chart.get("body", "")
    if soul:
        parts.append(f"命主{soul}")
    if body:
        parts.append(f"身主{body}")

    five_class = chart.get("fiveElementsClass", "")
    if five_class:
        parts.append(f"五行局{five_class}")

    soul_palace = chart.get("earthlyBranchOfSoulPalace", "")
    if soul_palace:
        parts.append(f"命宫{soul_palace}")

    palaces = chart.get("palaces", [])
    if palaces:
        stars: list[str] = []
        for p in palaces:
            if not isinstance(p, dict):
                continue
            for s in p.get("majorStars", []):
                if isinstance(s, dict) and s.get("name"):
                    stars.append(s["name"])
        if stars:
            parts.append("主星" + "、".join(stars[:4]))

    return "，".join(parts) if parts else "紫微斗数排盘完成"


async def _llm_interpret(chart: dict) -> str | None:
    try:
        from server.llm import is_llm_configured, chat_completion
        if not is_llm_configured():
            return None

        import json
        chart_text = json.dumps(chart, ensure_ascii=False, indent=2)
        if len(chart_text) > 8000:
            chart_text = chart_text[:8000] + "\n...(已截断)"

        messages = [
            {"role": "system", "content": (
                "你是一位精通紫微斗数的资深命理师。"
                "请基于以下紫微斗数命盘数据，为命主提供一段简洁的命理解读（300-500字）。\n"
                "要求：\n"
                "1. 先概括命宫主星和命格特征\n"
                "2. 分析事业宫和财帛宫的关键信息\n"
                "3. 简述夫妻宫和感情走势\n"
                "4. 语言风格专业但易懂\n"
                "5. 不要编造命盘中没有的星曜组合"
            )},
            {"role": "user", "content": f"以下是紫微斗数命盘数据：\n\n{chart_text}"},
        ]
        text = await chat_completion(messages, temperature=0.6, max_tokens=2048)
        return text
    except Exception as e:
        logger.debug("ZiweiAgent LLM interpretation failed: %s", e)
        return None


def _parse_birth_info(mcp_json: dict) -> tuple[str, int, int]:
    """从 mcp_json 提取紫微排盘所需的 (solar_date, hour, gender_num)。"""
    solar = mcp_json.get("阳历", "") or ""
    gender = mcp_json.get("性别", "") or ""

    solar_date = solar.split()[0] if " " in solar else solar
    hour = 12
    if solar and " " in solar:
        try:
            hour = int(solar.split()[1].split(":")[0])
        except (ValueError, IndexError):
            pass

    gender_num = 1 if gender == "男" else 0
    return solar_date, hour, gender_num


class ZiweiAgent:
    """紫微斗数智能体

    调用 iztro-py 排盘引擎，可选调用 LLM 生成解读。
    """

    async def analyze(self, mcp_json: dict) -> dict[str, Any]:
        """执行紫微斗数排盘分析。

        Args:
            mcp_json: 输入数据，需包含「阳历」和「性别」字段

        Returns:
            标准智能体输出::

                {
                    "agent": "ziwei",
                    "status": "success" | "error",
                    "data": { ... },
                    "summary": "一句话总结",
                    "timestamp": "ISO8601"
                }
        """
        try:
            from server.ziwei import get_ziwei_chart

            solar_date, hour, gender_num = _parse_birth_info(mcp_json)

            if not solar_date:
                return {
                    "agent": AGENT_NAME,
                    "status": "error",
                    "data": {"error": "缺少阳历出生日期"},
                    "summary": "紫微斗数排盘失败：缺少阳历出生日期",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            chart = await asyncio.to_thread(
                get_ziwei_chart,
                solar_date=solar_date,
                hour=hour,
                gender=gender_num,
            )

            if "error" in chart:
                return {
                    "agent": AGENT_NAME,
                    "status": "error",
                    "data": chart,
                    "summary": f"紫微斗数排盘失败: {chart['error']}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            llm_text = await _llm_interpret(chart)

            data: dict[str, Any] = {"chart": chart}
            if llm_text:
                data["llm_interpretation"] = llm_text

            return {
                "agent": AGENT_NAME,
                "status": "success",
                "data": data,
                "summary": _extract_summary(chart),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error("ZiweiAgent.analyze failed: %s", e, exc_info=True)
            return {
                "agent": AGENT_NAME,
                "status": "error",
                "data": {"error": str(e)},
                "summary": f"紫微斗数智能体异常: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
