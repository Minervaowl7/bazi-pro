#!/usr/bin/env python3
"""
bazi-pro 插件 API v5.0
抽象基类 + 插件发现与加载机制
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger('bazi_pro.plugins')

PLUGIN_WHITELIST: set[str] = set()

_READONLY_HOOKS: set[str] = {'on_retrieve', 'on_evidence'}
_WRITABLE_HOOKS: set[str] = {'on_render'}

_modification_log: list[dict] = []


class BaziPlugin(ABC):

    name: str = ''
    version: str = '1.0.0'
    description: str = ''
    permissions: list[str] = []

    @abstractmethod
    def on_retrieve(self, query: str, results: list[dict]) -> list[dict]:
        ...

    @abstractmethod
    def on_evidence(self, evidence: dict) -> dict:
        ...

    @abstractmethod
    def on_render(self, html: str, vm) -> str:
        ...


_HOOK_DATA_ARG: dict[str, int] = {
    'on_retrieve': 1,
    'on_evidence': 0,
    'on_render': 0,
}

_registry: dict[str, BaziPlugin] = {}


def register_plugin(plugin: BaziPlugin) -> None:
    if PLUGIN_WHITELIST and plugin.name not in PLUGIN_WHITELIST:
        raise ValueError(
            f'Plugin "{plugin.name}" not in whitelist; '
            f'allowed: {PLUGIN_WHITELIST}'
        )
    _registry[plugin.name] = plugin
    logger.info(
        'Plugin registered: name=%s version=%s permissions=%s',
        plugin.name, plugin.version, plugin.permissions,
    )


def get_plugin(name: str) -> Optional[BaziPlugin]:
    return _registry.get(name)


def list_plugins() -> list[str]:
    return list(_registry.keys())


def invoke_hook(plugin: BaziPlugin, hook_name: str, *args):
    if hook_name not in _READONLY_HOOKS and hook_name not in _WRITABLE_HOOKS:
        raise ValueError(f'Unknown hook: {hook_name}')

    method = getattr(plugin, hook_name, None)
    if method is None:
        data_idx = _HOOK_DATA_ARG.get(hook_name, 0)
        return args[data_idx] if data_idx < len(args) else None

    data_idx = _HOOK_DATA_ARG.get(hook_name, 0)
    original = args[data_idx] if data_idx < len(args) else None
    result = method(*args)

    if hook_name in _READONLY_HOOKS:
        if result is not original:
            logger.warning(
                'Plugin %s returned a different object from read-only hook %s; '
                'using original data',
                plugin.name, hook_name,
            )
            return original

    if hook_name in _WRITABLE_HOOKS:
        if result != original:
            _modification_log.append({
                'plugin': plugin.name,
                'hook': hook_name,
            })

    return result
