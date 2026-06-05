"""八字分析智能体

调用 bazi_pro.core.full_analysis() 获取确定性计算结果，
可选调用 LLM 生成自然语言解读。
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("bazi-pro.agents.bazi")

AGENT_NAME = "bazi"


def _extract_summary(result: dict) -> str:
    parts: list[str] = []

    day_master = result.get("day_master", "") or result.get("validation", {}).get("day_master", "")
    bazi = ""
    pillars_raw = result.get("pillars", []) or result.get("shishen", {}).get("pillars", [])
    if pillars_raw:
        bazi = " ".join(
            p.get("gan", "") + p.get("zhi", "")
            for p in pillars_raw
            if isinstance(p, dict) and p.get("gan") and p.get("zhi")
        )
    if day_master:
        parts.append(f"日主{day_master}")
    if bazi:
        parts.append(f"八字{bazi}")

    ws = result.get("strength", {}).get("wangshuai", {})
    verdict = ws.get("verdict", "") or result.get("wangshuai", {}).get("verdict", "")
    if verdict:
        parts.append(verdict)

    pattern_info = result.get("pattern", {})
    pattern_name = pattern_info.get("pattern", "") if isinstance(pattern_info, dict) else ""
    if pattern_name:
        parts.append(pattern_name)

    yongshen = result.get("yongshen", {})
    ys = yongshen.get("yongshen", "") if isinstance(yongshen, dict) else ""
    if ys:
        parts.append(f"用神{ys}")

    return "，".join(parts) if parts else "八字分析完成"


async def _llm_interpret(result: dict, narration: dict) -> str | None:
    try:
        from server.llm import is_llm_configured, chat_completion, build_analysis_system_prompt
        if not is_llm_configured():
            return None

        system_prompt = build_analysis_system_prompt(result, narration)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "请基于以上命盘数据，为命主提供一段简洁的八字命理解读（300-500字）。"},
        ]
        text = await chat_completion(messages, temperature=0.6, max_tokens=2048)
        return text
    except Exception as e:
        logger.debug("BaziAgent LLM interpretation failed: %s", e)
        return None


async def _generate_narration(result: dict) -> dict:
    try:
        from bazi_pro.narrator import narrate_analysis
        narration = narrate_analysis(result)
        return narration if isinstance(narration, dict) else {}
    except Exception as e:
        logger.debug("BaziAgent narration failed: %s", e)
        return {}


class BaziAgent:
    """八字分析智能体

    调用确定性核心计算引擎，可选调用 LLM 生成解读。
    """

    async def analyze(self, mcp_json: dict) -> dict[str, Any]:
        """执行八字分析。

        Args:
            mcp_json: 八字输入数据，遵循 MCP JSON 规范

        Returns:
            标准智能体输出::

                {
                    "agent": "bazi",
                    "status": "success" | "error",
                    "data": { ... },
                    "summary": "一句话总结",
                    "timestamp": "ISO8601"
                }
        """
        try:
            from bazi_pro.core import full_analysis

            result = await asyncio.to_thread(full_analysis, mcp_json)

            if result.get("status") != "completed":
                return {
                    "agent": AGENT_NAME,
                    "status": "error",
                    "data": result,
                    "summary": f"八字分析失败: {result.get('errors', result.get('status', '未知错误'))}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            narration = await _generate_narration(result)

            llm_text = await _llm_interpret(result, narration)

            data: dict[str, Any] = {
                "core": result,
                "narration": narration,
            }
            if llm_text:
                data["llm_interpretation"] = llm_text

            return {
                "agent": AGENT_NAME,
                "status": "success",
                "data": data,
                "summary": _extract_summary(result),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error("BaziAgent.analyze failed: %s", e, exc_info=True)
            return {
                "agent": AGENT_NAME,
                "status": "error",
                "data": {"error": str(e)},
                "summary": f"八字智能体异常: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
