#!/usr/bin/env python3
"""
bazi-pro 插件 API v5.0
抽象基类 + 插件发现与加载机制
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaziPlugin(ABC):
    """八字分析插件基类

    所有插件必须继承此类并实现钩子方法。
    插件只能读取、过滤、增强、装饰输出，不得修改核心数据。
    """

    # 插件元数据（子类必须覆盖）
    name: str = ''
    version: str = '1.0.0'
    description: str = ''

    @abstractmethod
    def on_retrieve(self, query: str, results: list[dict]) -> list[dict]:
        """检索后钩子：过滤/增强/重排检索结果"""
        ...

    @abstractmethod
    def on_evidence(self, evidence: dict) -> dict:
        """证据构建后钩子：添加/修改/移除证据"""
        ...

    @abstractmethod
    def on_render(self, html: str, vm) -> str:
        """渲染后钩子：注入/修改 HTML 输出"""
        ...


# ── 插件注册表 ──
_registry: dict[str, BaziPlugin] = {}


def register_plugin(plugin: BaziPlugin) -> None:
    """注册插件"""
    _registry[plugin.name] = plugin


def get_plugin(name: str) -> Optional[BaziPlugin]:
    """获取已注册插件"""
    return _registry.get(name)


def list_plugins() -> list[str]:
    """列出所有已注册插件名称"""
    return list(_registry.keys())
