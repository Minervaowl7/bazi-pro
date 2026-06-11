"""
LLM 服务模块 — re-export shim 保持向后兼容

所有实际实现已拆分至：
- server.llm_client  — 配置管理 + HTTP 调用 + 函数调用
- server.llm_context — 干支计算 + 上下文格式化 + 检索结果格式化 + 学校视角
- server.llm_prompts — 提示词模板 + 构建器
"""
import sys
import types

import server.llm_client as _client_mod
import server.llm_context as _context_mod
from server.llm_client import *  # noqa: F401,F403
from server.llm_context import *  # noqa: F401,F403
from server.llm_prompts import *  # noqa: F401,F403

# Private names that tests and internal code access directly on this module.
# These must be proxied to the actual submodule so that mutations propagate.
_PROXY_CLIENT = frozenset({
    "_LLM_API_KEY", "_LLM_API_BASE", "_LLM_MODEL", "_LLM_TIMEOUT", "_MAX_TOOL_ROUNDS",
})
_PROXY_CONTEXT = frozenset({
    "_get_year_ganzhi", "_get_month_ganzhi", "_get_day_ganzhi",
})


class _ShimModule(types.ModuleType):
    """Module subclass that proxies private name access to submodules."""

    def __getattr__(self, name: str):
        if name in _PROXY_CLIENT:
            return getattr(_client_mod, name)
        if name in _PROXY_CONTEXT:
            return getattr(_context_mod, name)
        raise AttributeError(f"module {self.__name__!r} has no attribute {name!r}")

    def __setattr__(self, name: str, value):
        if name in _PROXY_CLIENT:
            setattr(_client_mod, name, value)
        elif name in _PROXY_CONTEXT:
            setattr(_context_mod, name, value)
        else:
            super().__setattr__(name, value)


# Replace this module's class so __getattr__/__setattr__ work
sys.modules[__name__].__class__ = _ShimModule
