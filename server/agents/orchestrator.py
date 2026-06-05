"""多智能体编排器

并行调用八字和紫微斗数子智能体，收集结果后调用综合智能体生成统一解读。
每个子智能体独立运行，失败时优雅降级，不影响其他智能体。
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from server.agents.bazi_agent import BaziAgent
from server.agents.synthesis_agent import SynthesisAgent
from server.agents.ziwei_agent import ZiweiAgent

logger = logging.getLogger("bazi-pro.agents.orchestrator")


def _error_result(agent_name: str, error: Exception) -> dict[str, Any]:
    return {
        "agent": agent_name,
        "status": "error",
        "data": {"error": str(error)},
        "summary": f"{agent_name}智能体异常: {error}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class AgentOrchestrator:
    """多智能体命理分析编排器

    并行执行八字和紫微斗数分析，再综合两者结果生成统一解读。
    """

    def __init__(self) -> None:
        self._bazi = BaziAgent()
        self._ziwei = ZiweiAgent()
        self._synthesis = SynthesisAgent()

    async def analyze(
        self,
        mcp_json: dict,
        knowledge_context: dict | list | None = None,
    ) -> dict[str, Any]:
        """执行多智能体并行分析。

        Args:
            mcp_json: 八字输入数据，遵循 MCP JSON 规范
            knowledge_context: 可选的知识图谱历史数据

        Returns:
            编排结果::

                {
                    "status": "completed" | "partial",
                    "agents": {
                        "bazi": { agent, status, data, summary },
                        "ziwei": { agent, status, data, summary },
                        "synthesis": { agent, status, data, summary },
                    },
                    "summary": "综合一句话总结",
                    "timestamp": "ISO8601"
                }
        """
        bazi_task = asyncio.create_task(self._safe_bazi(mcp_json))
        ziwei_task = asyncio.create_task(self._safe_ziwei(mcp_json))

        bazi_result, ziwei_result = await asyncio.gather(bazi_task, ziwei_task)

        synthesis_result = await self._synthesis.analyze(
            bazi_result, ziwei_result, knowledge_context
        )

        has_success = any(
            r.get("status") == "success"
            for r in (bazi_result, ziwei_result)
        )
        status = "completed" if has_success else "partial"

        return {
            "status": status,
            "agents": {
                "bazi": bazi_result,
                "ziwei": ziwei_result,
                "synthesis": synthesis_result,
            },
            "summary": synthesis_result.get("summary", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _safe_bazi(self, mcp_json: dict) -> dict[str, Any]:
        try:
            return await self._bazi.analyze(mcp_json)
        except Exception as e:
            logger.error("BaziAgent raised: %s", e, exc_info=True)
            return _error_result("bazi", e)

    async def _safe_ziwei(self, mcp_json: dict) -> dict[str, Any]:
        try:
            return await self._ziwei.analyze(mcp_json)
        except Exception as e:
            logger.error("ZiweiAgent raised: %s", e, exc_info=True)
            return _error_result("ziwei", e)
