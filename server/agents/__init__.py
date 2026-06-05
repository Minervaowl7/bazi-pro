"""多智能体命理分析系统

并行调用八字和紫微斗数子智能体，再由综合智能体生成统一解读。
"""

from server.agents.bazi_agent import BaziAgent
from server.agents.orchestrator import AgentOrchestrator
from server.agents.synthesis_agent import SynthesisAgent
from server.agents.ziwei_agent import ZiweiAgent

__all__ = [
    "AgentOrchestrator",
    "BaziAgent",
    "ZiweiAgent",
    "SynthesisAgent",
]
