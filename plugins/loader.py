#!/usr/bin/env python3
"""
bazi-pro 插件加载器 v5.0
自动发现并加载 plugins/ 目录下的插件
"""

import json
import importlib
import os
from pathlib import Path
from typing import Optional
from bazi_pro.plugin_api import BaziPlugin, register_plugin


def load_plugin_from_dir(plugin_dir: str) -> Optional[BaziPlugin]:
    """从插件目录加载插件"""
    plugin_json = os.path.join(plugin_dir, 'plugin.json')
    main_py = os.path.join(plugin_dir, 'main.py')

    if not os.path.exists(plugin_json) or not os.path.exists(main_py):
        return None

    try:
        with open(plugin_json, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

    try:
        spec = importlib.util.spec_from_file_location(
            f'bazi_plugin_{meta.get("name", "unknown")}', main_py
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 查找 BaziPlugin 子类
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and issubclass(attr, BaziPlugin)
                    and attr is not BaziPlugin):
                plugin = attr()
                plugin.name = meta.get('name', plugin.name)
                plugin.version = meta.get('version', plugin.version)
                plugin.description = meta.get('description', plugin.description)
                return plugin
    except Exception as e:
        import logging
        logging.getLogger('bazi_pro.plugins').warning(
            '插件加载失败 [%s]: %s', meta.get('name', 'unknown'), e
        )

    return None


def scan_plugins_dir(plugins_root: str = '') -> list[BaziPlugin]:
    """扫描 plugins/ 目录并加载所有插件"""
    if not plugins_root:
        plugins_root = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'plugins'
        )

    loaded = []
    if not os.path.isdir(plugins_root):
        return loaded

    for entry in os.listdir(plugins_root):
        # 跳过 examples/ 和 __pycache__
        if entry.startswith('_') or entry.startswith('.'):
            continue
        plugin_path = os.path.join(plugins_root, entry)
        if os.path.isdir(plugin_path):
            plugin = load_plugin_from_dir(plugin_path)
            if plugin:
                register_plugin(plugin)
                loaded.append(plugin)

    return loaded


def load_all_plugins() -> list[BaziPlugin]:
    """加载所有可用插件（目录扫描 + entry_points）"""
    plugins = scan_plugins_dir()

    # 也尝试从 entry_points 发现
    try:
        eps = importlib.metadata.entry_points(group='bazi_pro.plugins')
        for ep in eps:
            try:
                plugin_cls = ep.load()
                plugin = plugin_cls()
                register_plugin(plugin)
                plugins.append(plugin)
            except Exception as e:
                import logging
                logging.getLogger('bazi_pro.plugins').warning(
                    'entry_point 插件加载失败 [%s]: %s', ep.name, e
                )
    except Exception:
        pass

    return plugins
