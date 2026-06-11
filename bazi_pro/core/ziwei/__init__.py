"""
紫微斗数分析模块

基于 iztro-py 排盘引擎，提供格局识别、四化分析、星曜解读和确定性叙述器。
"""

from __future__ import annotations

from bazi_pro.core.ziwei.constants import SI_HUA_TABLE, STAR_NATURE, Pattern, PatternCondition
from bazi_pro.core.ziwei.narrator import narrate_ziwei
from bazi_pro.core.ziwei.patterns import detect_patterns
from bazi_pro.core.ziwei.sihua import analyze_sihua, get_sihua_by_stem
from bazi_pro.core.ziwei.stars import analyze_ming_palace, analyze_star_in_palace

__all__ = [
    "SI_HUA_TABLE",
    "STAR_NATURE",
    "Pattern",
    "PatternCondition",
    "detect_patterns",
    "analyze_sihua",
    "get_sihua_by_stem",
    "analyze_star_in_palace",
    "analyze_ming_palace",
    "narrate_ziwei",
]
