# 紫微斗数分析解读功能实现计划

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 为 bazi-pro 添加完整的紫微斗数分析解读功能，包括格局识别、四化分析、星曜解读和确定性叙述器。

**Architecture:** 基于 iztro-py 排盘引擎，移植 Renhuai123/ziwei-doushu 的格局知识库和四化系统，实现与 bazi narrator.py 同架构的确定性叙述器。

**Tech Stack:** Python 3.10+, iztro-py, Pydantic, pytest

---

## 📋 项目概述

### 现状分析

| 组件 | 状态 | 说明 |
|------|------|------|
| `server/ziwei.py` | ✅ 已有 | 基础排盘（get_ziwei_chart/get_ziwei_horoscope/analyze_ziwei_palace） |
| `iztro-py` | ✅ 已安装 | v0.3.4，纯 Python 紫微斗数排盘库 |
| 格局识别 | ❌ 缺失 | 需移植 Renhuai123/ziwei-doushu 的 42 个格局 |
| 四化分析 | ❌ 缺失 | 需实现本命/大限/流年四化分析 |
| 星曜解读 | ❌ 缺失 | 需实现 14 主星 × 12 宫位组合解读 |
| 叙述器 | ❌ 缺失 | 需实现确定性文本生成（对标 narrator.py） |

### 目标架构

```
bazi_pro/core/ziwei/
├── __init__.py           # 模块入口
├── constants.py          # 常量（四化表、星曜性质、宫位定义）
├── patterns.py           # 格局识别（42 个格局检测函数）
├── sihua.py              # 四化分析（本命/大限/流年/流月四化）
├── stars.py              # 星曜解读（14 主星性质 + 宫位组合）
├── narrator.py           # 确定性叙述器（零 LLM）
└── utils.py              # 工具函数（三方四正、夹宫、庙旺判断）

server/ziwei.py           # API 层（扩展现有模块）
tests/test_ziwei.py       # 测试用例
```

---

## 🎯 实施阶段

### Phase 1: 核心数据结构和常量（1天）

**目标：** 建立紫微斗数分析的基础设施

#### Task 1.1: 创建模块结构

**Objective:** 创建 `bazi_pro/core/ziwei/` 模块结构

**Files:**
- Create: `bazi_pro/core/ziwei/__init__.py`
- Create: `bazi_pro/core/ziwei/constants.py`
- Create: `bazi_pro/core/ziwei/utils.py`

**Step 1: 创建模块目录和 __init__.py**

```python
# bazi_pro/core/ziwei/__init__.py
"""
紫微斗数分析模块

基于 iztro-py 排盘引擎，提供格局识别、四化分析、星曜解读和确定性叙述器。
"""

from bazi_pro.core.ziwei.constants import SI_HUA_TABLE, STAR_NATURE
from bazi_pro.core.ziwei.patterns import detect_patterns
from bazi_pro.core.ziwei.sihua import analyze_sihua
from bazi_pro.core.ziwei.stars import analyze_star_in_palace
from bazi_pro.core.ziwei.narrator import narrate_ziwei

__all__ = [
    "SI_HUA_TABLE",
    "STAR_NATURE",
    "detect_patterns",
    "analyze_sihua",
    "analyze_star_in_palace",
    "narrate_ziwei",
]
```

**Step 2: 创建 constants.py**

```python
# bazi_pro/core/ziwei/constants.py
"""
紫微斗数常量定义

包含四化表、星曜性质、宫位定义等核心常量。
数据来源：《紫微斗数全书》《紫微斗数全集》
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ── 四化表 ──────────────────────────────────────────────────────────────────────
# 十天干四化对照表
# 来源：《紫微斗数全书》
SI_HUA_TABLE: dict[str, dict[str, str]] = {
    "甲": {"化禄": "廉贞", "化权": "破军", "化科": "武曲", "化忌": "太阳"},
    "乙": {"化禄": "天机", "化权": "天梁", "化科": "紫微", "化忌": "太阴"},
    "丙": {"化禄": "天同", "化权": "天机", "化科": "文昌", "化忌": "廉贞"},
    "丁": {"化禄": "太阴", "化权": "天同", "化科": "天机", "化忌": "巨门"},
    "戊": {"化禄": "贪狼", "化权": "太阴", "化科": "右弼", "化忌": "天机"},
    "己": {"化禄": "武曲", "化权": "贪狼", "化科": "天梁", "化忌": "文曲"},
    "庚": {"化禄": "太阳", "化权": "武曲", "化科": "天同", "化忌": "太阴"},
    "辛": {"化禄": "巨门", "化权": "太阳", "化科": "文曲", "化忌": "文昌"},
    "壬": {"化禄": "天梁", "化权": "紫微", "化科": "左辅", "化忌": "武曲"},
    "癸": {"化禄": "破军", "化权": "巨门", "化科": "太阴", "化忌": "贪狼"},
}

# ── 十四主星性质 ──────────────────────────────────────────────────────────────
# 来源：《紫微斗数全书》《骨髓赋》
@dataclass
class StarNature:
    """星曜性质"""
    name: str
   五行: str
    性情: str
    象义: str
    吉凶: str  # 吉/凶/中
    宫位影响: dict[str, str]  # 宫位名 -> 影响描述

STAR_NATURE: dict[str, StarNature] = {
    "紫微": StarNature(
        name="紫微",
        五行="土",
        性情="尊贵、权威、领导力",
        象义="帝王之星，主贵气、权力、地位",
        吉凶="吉",
        宫位影响={
            "命宫": "尊贵有权威，领导才能，但易孤高",
            "财帛宫": "财运稳定，有贵人相助",
            "官禄宫": "事业顺利，有升迁机会",
            "夫妻宫": "配偶有气质，但易有压力",
        }
    ),
    # ... 其他 13 主星
}

# ── 十二宫位定义 ──────────────────────────────────────────────────────────────
PALACE_NAMES: list[str] = [
    "命宫", "兄弟宫", "夫妻宫", "子女宫", "财帛宫", "疾厄宫",
    "迁移宫", "交友宫", "官禄宫", "田宅宫", "福德宫", "父母宫",
]

# ── 三方四正宫位索引偏移 ──────────────────────────────────────────────────────
# 命宫(0) + 财帛宫(+4) + 官禄宫(+8) + 迁移宫(+6)
SAN_FANG_OFFSETS: list[int] = [0, 4, 8, 6]

# ── 夹宫索引偏移 ──────────────────────────────────────────────────────────────
# 命宫前后两宫
JIA_OFFSETS: list[int] = [-1, 1]
```

**Step 3: 创建 utils.py**

```python
# bazi_pro/core/ziwei/utils.py
"""
紫微斗数工具函数

包含三方四正、夹宫、庙旺判断等辅助函数。
"""

from __future__ import annotations

from typing import Any

from bazi_pro.core.ziwei.constants import SAN_FANG_OFFSETS, JIA_OFFSETS


def get_san_fang_palaces(chart: dict[str, Any], ming_branch: str) -> list[dict[str, Any]]:
    """获取三方四正宫位（命宫 + 财帛 + 官禄 + 迁移）

    Args:
        chart: iztro-py 排盘结果
        ming_branch: 命宫地支

    Returns:
        三方四正宫位列表
    """
    # TODO: 实现三方四正宫位获取
    pass


def get_jia_palaces(chart: dict[str, Any], branch: str) -> dict[str, dict[str, Any]]:
    """获取夹宫（命宫前后两宫）

    Args:
        chart: iztro-py 排盘结果
        branch: 命宫地支

    Returns:
        {"prev": 前一宫, "next": 后一宫}
    """
    # TODO: 实现夹宫获取
    pass


def is_bright(palace: dict[str, Any], star_name: str) -> bool:
    """判断星曜是否庙旺

    Args:
        palace: 宫位数据
        star_name: 星曜名称

    Returns:
        True 如果庙旺
    """
    # TODO: 实现庙旺判断
    pass


def is_dim(palace: dict[str, Any], star_name: str) -> bool:
    """判断星曜是否落陷

    Args:
        palace: 宫位数据
        star_name: 星曜名称

    Returns:
        True 如果落陷
    """
    # TODO: 实现落陷判断
    pass


def get_palace_by_name(chart: dict[str, Any], palace_name: str) -> dict[str, Any] | None:
    """根据宫位名称获取宫位数据

    Args:
        chart: iztro-py 排盘结果
        palace_name: 宫位名称

    Returns:
        宫位数据，未找到返回 None
    """
    for palace in chart.get("palaces", []):
        if palace.get("name") == palace_name:
            return palace
    return None
```

**Step 4: 运行测试验证模块结构**

```bash
python -m pytest tests/test_ziwei.py -v
```

**Step 5: 提交**

```bash
git add bazi_pro/core/ziwei/
git commit -m "feat(ziwei): 创建紫微斗数分析模块结构"
```

---

### Phase 2: 格局识别模块（2-3天）

**目标：** 移植 Renhuai123/ziwei-doushu 的 42 个格局检测函数

#### Task 2.1: 实现格局数据结构

**Objective:** 定义格局相关的数据结构

**Files:**
- Modify: `bazi_pro/core/ziwei/constants.py`

**Step 1: 添加格局数据结构**

```python
# 在 constants.py 中添加

@dataclass
class PatternCondition:
    """格局条件"""
    required: list[str]   # 必须满足条件
    bonus: list[str]      # 加分项
    breaking: list[str]   # 破格警示

@dataclass
class Pattern:
    """紫微斗数格局"""
    name: str
    level: str  # excellent/good/neutral/caution
    description: str
    palaces: list[str]  # 涉及宫位
    conditions: PatternCondition | None = None
    source: str = ""  # 古籍出处
```

**Step 2: 添加格局常量**

```python
# 在 constants.py 中添加

# 格局等级
PATTERN_LEVELS = {
    "excellent": "上格",
    "good": "中格",
    "neutral": "平格",
    "caution": "警示格",
}

# 格局来源
PATTERN_SOURCES = {
    "紫微斗数全书": "《紫微斗数全书》",
    "紫微斗数全集": "《紫微斗数全集》",
    "骨髓赋": "《骨髓赋》",
}
```

**Step 3: 提交**

```bash
git add bazi_pro/core/ziwei/constants.py
git commit -m "feat(ziwei): 添加格局数据结构"
```

#### Task 2.2: 实现格局检测工具函数

**Objective:** 实现三方四正、夹宫等格局检测辅助函数

**Files:**
- Modify: `bazi_pro/core/ziwei/utils.py`

**Step 1: 实现 get_san_fang_palaces**

```python
def get_san_fang_palaces(chart: dict[str, Any], ming_branch: str) -> list[dict[str, Any]]:
    """获取三方四正宫位（命宫 + 财帛 + 官禄 + 迁移）

    Args:
        chart: iztro-py 排盘结果
        ming_branch: 命宫地支

    Returns:
        三方四正宫位列表
    """
    # 地支索引映射
    branch_index = {
        "子": 0, "丑": 1, "寅": 2, "卯": 3, "辰": 4, "巳": 5,
        "午": 6, "未": 7, "申": 8, "酉": 9, "戌": 10, "亥": 11
    }

    # 获取命宫索引
    ming_idx = branch_index.get(ming_branch, 0)

    # 计算三方四正宫位索引
    san_fang_indices = [(ming_idx + offset) % 12 for offset in SAN_FANG_OFFSETS]

    # 获取宫位数据
    palaces = chart.get("palaces", [])
    result = []
    for idx in san_fang_indices:
        if idx < len(palaces):
            result.append(palaces[idx])

    return result
```

**Step 2: 实现 get_jia_palaces**

```python
def get_jia_palaces(chart: dict[str, Any], branch: str) -> dict[str, dict[str, Any]]:
    """获取夹宫（命宫前后两宫）

    Args:
        chart: iztro-py 排盘结果
        branch: 命宫地支

    Returns:
        {"prev": 前一宫, "next": 后一宫}
    """
    branch_index = {
        "子": 0, "丑": 1, "寅": 2, "卯": 3, "辰": 4, "巳": 5,
        "午": 6, "未": 7, "申": 8, "酉": 9, "戌": 10, "亥": 11
    }

    idx = branch_index.get(branch, 0)
    palaces = chart.get("palaces", [])

    prev_idx = (idx - 1) % 12
    next_idx = (idx + 1) % 12

    return {
        "prev": palaces[prev_idx] if prev_idx < len(palaces) else None,
        "next": palaces[next_idx] if next_idx < len(palaces) else None,
    }
```

**Step 3: 实现 is_bright 和 is_dim**

```python
def is_bright(palace: dict[str, Any], star_name: str) -> bool:
    """判断星曜是否庙旺"""
    for star in palace.get("majorStars", []) + palace.get("minorStars", []):
        if star.get("name") == star_name:
            return star.get("brightness") == "bright"
    return False

def is_dim(palace: dict[str, Any], star_name: str) -> bool:
    """判断星曜是否落陷"""
    for star in palace.get("majorStars", []) + palace.get("minorStars", []):
        if star.get("name") == star_name:
            return star.get("brightness") == "dim"
    return False
```

**Step 4: 提交**

```bash
git add bazi_pro/core/ziwei/utils.py
git commit -m "feat(ziwei): 实现格局检测工具函数"
```

#### Task 2.3: 实现上格检测函数（8个）

**Objective:** 实现 8 个上格检测函数

**Files:**
- Create: `bazi_pro/core/ziwei/patterns.py`

**Step 1: 创建 patterns.py 并实现紫府同宫检测**

```python
# bazi_pro/core/ziwei/patterns.py
"""
紫微斗数格局识别模块

基于 Renhuai123/ziwei-doushu 的 patterns.ts 移植，实现 42 个格局检测函数。
数据来源：《紫微斗数全书》《紫微斗数全集》《骨髓赋》
"""

from __future__ import annotations

from typing import Any

from bazi_pro.core.ziwei.constants import Pattern, PatternCondition
from bazi_pro.core.ziwei.utils import (
    get_san_fang_palaces,
    get_jia_palaces,
    is_bright,
    is_dim,
    get_palace_by_name,
)


def detect_zi_fu(chart: dict[str, Any]) -> Pattern | None:
    """检测紫府同宫格

    条件：紫微+天府同宫（寅/申）
    来源：《紫微斗数全书》
    """
    # 获取命宫
    ming_palace = get_palace_by_name(chart, "命宫")
    if not ming_palace:
        return None

    # 检查命宫是否有紫微和天府
    major_stars = [s.get("name") for s in ming_palace.get("majorStars", [])]
    if "紫微" in major_stars and "天府" in major_stars:
        # 检查是否在寅或申宫
        earthly_branch = ming_palace.get("earthlyBranch", "")
        if earthly_branch in ["寅", "申"]:
            return Pattern(
                name="紫府同宫",
                level="excellent",
                description="紫微天府同坐命宫，主富贵双全，一生运势顺遂",
                palaces=["命宫"],
                conditions=PatternCondition(
                    required=["命宫紫微+天府", "寅或申宫"],
                    bonus=["三方四正会吉星"],
                    breaking=["三方四正会煞星"],
                ),
                source="《紫微斗数全书》",
            )

    return None
```

**Step 2: 实现其他 7 个上格检测函数**

```python
def detect_jun_chen_qing_hui(chart: dict[str, Any]) -> Pattern | None:
    """检测君臣庆会格"""
    # TODO: 实现
    pass

def detect_fu_xiang_chao_yuan(chart: dict[str, Any]) -> Pattern | None:
    """检测府相朝垣格"""
    # TODO: 实现
    pass

def detect_yang_liang_chang_lu(chart: dict[str, Any]) -> Pattern | None:
    """检测阳梁昌禄格"""
    # TODO: 实现
    pass

def detect_huo_tan_ling_tan(chart: dict[str, Any]) -> Pattern | None:
    """检测火贪格/铃贪格"""
    # TODO: 实现
    pass

def detect_wu_tan(chart: dict[str, Any]) -> Pattern | None:
    """检测武贪格"""
    # TODO: 实现
    pass

def detect_sha_po_lang(chart: dict[str, Any]) -> Pattern | None:
    """检测杀破狼格"""
    # TODO: 实现
    pass

def detect_ji_yue_tong_liang(chart: dict[str, Any]) -> Pattern | None:
    """检测机月同梁格"""
    # TODO: 实现
    pass
```

**Step 3: 实现 detect_patterns 主函数**

```python
def detect_patterns(chart: dict[str, Any]) -> list[Pattern]:
    """检测所有格局

    Args:
        chart: iztro-py 排盘结果

    Returns:
        检测到的格局列表
    """
    patterns = []

    # 上格检测
    detectors = [
        detect_zi_fu,
        detect_jun_chen_qing_hui,
        detect_fu_xiang_chao_yuan,
        detect_yang_liang_chang_lu,
        detect_huo_tan_ling_tan,
        detect_wu_tan,
        detect_sha_po_lang,
        detect_ji_yue_tong_liang,
    ]

    for detector in detectors:
        pattern = detector(chart)
        if pattern:
            patterns.append(pattern)

    return patterns
```

**Step 4: 运行测试**

```bash
python -m pytest tests/test_ziwei.py::test_detect_patterns -v
```

**Step 5: 提交**

```bash
git add bazi_pro/core/ziwei/patterns.py
git commit -m "feat(ziwei): 实现上格检测函数（8个）"
```

#### Task 2.4: 实现中格和助力格检测函数（17个）

**Objective:** 实现 9 个中格和 8 个助力格检测函数

**Files:**
- Modify: `bazi_pro/core/ziwei/patterns.py`

**Step 1: 实现中格检测函数**

```python
def detect_lian_xiang(chart: dict[str, Any]) -> Pattern | None:
    """检测廉贞天相格"""
    # TODO: 实现
    pass

def detect_wu_qi_sha(chart: dict[str, Any]) -> Pattern | None:
    """检测武曲七杀格"""
    # TODO: 实现
    pass

# ... 其他 7 个中格
```

**Step 2: 实现助力格检测函数**

```python
def detect_fu_bi_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测辅弼夹命格"""
    # TODO: 实现
    pass

def detect_chang_qu_jia_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测昌曲夹命格"""
    # TODO: 实现
    pass

# ... 其他 6 个助力格
```

**Step 3: 更新 detect_patterns 函数**

```python
def detect_patterns(chart: dict[str, Any]) -> list[Pattern]:
    """检测所有格局"""
    patterns = []

    # 上格检测
    # ... 添加新检测函数

    # 中格检测
    # ... 添加新检测函数

    # 助力格检测
    # ... 添加新检测函数

    return patterns
```

**Step 4: 提交**

```bash
git add bazi_pro/core/ziwei/patterns.py
git commit -m "feat(ziwei): 实现中格和助力格检测函数（17个）"
```

#### Task 2.5: 实现恶格和基础格局检测函数（17个）

**Objective:** 实现 8 个恶格和 9 个基础格局检测函数

**Files:**
- Modify: `bazi_pro/core/ziwei/patterns.py`

**Step 1: 实现恶格检测函数**

```python
def detect_hua_ji_ru_ming_qian(chart: dict[str, Any]) -> Pattern | None:
    """检测化忌入命/迁格"""
    # TODO: 实现
    pass

def detect_yang_tuo_jia_ji(chart: dict[str, Any]) -> Pattern | None:
    """检测羊陀夹忌格"""
    # TODO: 实现
    pass

# ... 其他 6 个恶格
```

**Step 2: 实现基础格局检测函数**

```python
def detect_lu_cun_shou_shen(chart: dict[str, Any]) -> Pattern | None:
    """检测禄存守命/守身格"""
    # TODO: 实现
    pass

def detect_tian_ma_ru_ming(chart: dict[str, Any]) -> Pattern | None:
    """检测天马入命/在迁格"""
    # TODO: 实现
    pass

# ... 其他 7 个基础格局
```

**Step 3: 提交**

```bash
git add bazi_pro/core/ziwei/patterns.py
git commit -m "feat(ziwei): 实现恶格和基础格局检测函数（17个）"
```

---

### Phase 3: 四化分析模块（2天）

**目标：** 实现本命、大限、流年四化分析

#### Task 3.1: 实现四化基础函数

**Objective:** 实现四化表查询和天干推算函数

**Files:**
- Create: `bazi_pro/core/ziwei/sihua.py`

**Step 1: 创建 sihua.py 并实现基础函数**

```python
# bazi_pro/core/ziwei/sihua.py
"""
紫微斗数四化分析模块

实现本命、大限、流年、流月四化分析。
数据来源：《紫微斗数全书》
"""

from __future__ import annotations

from typing import Any

from bazi_pro.core.ziwei.constants import SI_HUA_TABLE


def get_sihua_by_stem(stem: str) -> dict[str, str]:
    """根据天干获取四化

    Args:
        stem: 天干（甲/乙/丙/...）

    Returns:
        {"化禄": "星名", "化权": "星名", "化科": "星名", "化忌": "星名"}
    """
    return SI_HUA_TABLE.get(stem, {})


def get_year_stem(year: int) -> str:
    """根据公历年获取年柱天干

    Args:
        year: 公历年

    Returns:
        天干
    """
    # 天干索引：0=甲, 1=乙, ..., 9=癸
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    return stems[(year - 4) % 10]


def get_year_branch(year: int) -> str:
    """根据公历年获取年柱地支

    Args:
        year: 公历年

    Returns:
        地支
    """
    # 地支索引：0=子, 1=丑, ..., 11=亥
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    return branches[(year - 4) % 12]
```

**Step 2: 实现四化反向映射**

```python
def build_star_sihua_map(stem: str) -> dict[str, str]:
    """构建星曜四化反向映射

    Args:
        stem: 天干

    Returns:
        {"星名": "化类型"} 例如 {"廉贞": "化禄", "破军": "化权", ...}
    """
    sihua = get_sihua_by_stem(stem)
    return {v: k for k, v in sihua.items()}
```

**Step 3: 提交**

```bash
git add bazi_pro/core/ziwei/sihua.py
git commit -m "feat(ziwei): 实现四化基础函数"
```

#### Task 3.2: 实现本命四化分析

**Objective:** 实现本命四化分析函数

**Files:**
- Modify: `bazi_pro/core/ziwei/sihua.py`

**Step 1: 实现本命四化分析**

```python
def analyze_benming_sihua(chart: dict[str, Any]) -> dict[str, Any]:
    """分析本命四化

    Args:
        chart: iztro-py 排盘结果

    Returns:
        {
            "sihua": {"化禄": "星名", ...},
            "star_sihua_map": {"星名": "化类型", ...},
            "palace_sihua": {"宫位名": ["化禄", "化权", ...], ...}
        }
    """
    # 获取年干
    year_stem = chart.get("yearStem", "")
    if not year_stem:
        return {"error": "无法获取年干"}

    # 获取四化
    sihua = get_sihua_by_stem(year_stem)
    star_sihua_map = build_star_sihua_map(year_stem)

    # 分析各宫位四化
    palace_sihua: dict[str, list[str]] = {}
    for palace in chart.get("palaces", []):
        palace_name = palace.get("name", "")
        major_stars = [s.get("name") for s in palace.get("majorStars", [])]

        # 检查该宫位主星是否有四化
        sihua_in_palace = []
        for star in major_stars:
            if star in star_sihua_map:
                sihua_in_palace.append(star_sihua_map[star])

        if sihua_in_palace:
            palace_sihua[palace_name] = sihua_in_palace

    return {
        "sihua": sihua,
        "star_sihua_map": star_sihua_map,
        "palace_sihua": palace_sihua,
    }
```

**Step 2: 提交**

```bash
git add bazi_pro/core/ziwei/sihua.py
git commit -m "feat(ziwei): 实现本命四化分析"
```

#### Task 3.3: 实现大限四化分析

**Objective:** 实现大限四化分析函数

**Files:**
- Modify: `bazi_pro/core/ziwei/sihua.py`

**Step 1: 实现大限四化分析**

```python
def analyze_daxian_sihua(chart: dict[str, Any], daxian_index: int) -> dict[str, Any]:
    """分析大限四化

    Args:
        chart: iztro-py 排盘结果
        daxian_index: 大限索引（0-11）

    Returns:
        {
            "stem": "大限天干",
            "sihua": {"化禄": "星名", ...},
            "star_sihua_map": {"星名": "化类型", ...},
        }
    """
    # 获取大限宫位
    palaces = chart.get("palaces", [])
    if daxian_index >= len(palaces):
        return {"error": "大限索引超出范围"}

    daxian_palace = palaces[daxian_index]

    # 获取大限天干
    daxian_stem = daxian_palace.get("heavenlyStem", "")
    if not daxian_stem:
        return {"error": "无法获取大限天干"}

    # 获取四化
    sihua = get_sihua_by_stem(daxian_stem)
    star_sihua_map = build_star_sihua_map(daxian_stem)

    return {
        "stem": daxian_stem,
        "sihua": sihua,
        "star_sihua_map": star_sihua_map,
    }
```

**Step 2: 提交**

```bash
git add bazi_pro/core/ziwei/sihua.py
git commit -m "feat(ziwei): 实现大限四化分析"
```

#### Task 3.4: 实现流年四化分析

**Objective:** 实现流年四化分析函数

**Files:**
- Modify: `bazi_pro/core/ziwei/sihua.py`

**Step 1: 实现流年四化分析**

```python
def analyze_liunian_sihua(year: int) -> dict[str, Any]:
    """分析流年四化

    Args:
        year: 流年

    Returns:
        {
            "stem": "流年天干",
            "branch": "流年地支",
            "sihua": {"化禄": "星名", ...},
            "star_sihua_map": {"星名": "化类型", ...},
        }
    """
    # 获取流年天干地支
    year_stem = get_year_stem(year)
    year_branch = get_year_branch(year)

    # 获取四化
    sihua = get_sihua_by_stem(year_stem)
    star_sihua_map = build_star_sihua_map(year_stem)

    return {
        "stem": year_stem,
        "branch": year_branch,
        "sihua": sihua,
        "star_sihua_map": star_sihua_map,
    }
```

**Step 2: 实现综合四化分析**

```python
def analyze_sihua(chart: dict[str, Any], query_year: int | None = None) -> dict[str, Any]:
    """综合四化分析

    Args:
        chart: iztro-py 排盘结果
        query_year: 查询年份（可选）

    Returns:
        {
            "benming": 本命四化,
            "daxian": 大限四化列表,
            "liunian": 流年四化（如果指定了年份）
        }
    """
    result = {
        "benming": analyze_benming_sihua(chart),
        "daxian": [],
    }

    # 分析 12 个大限
    for i in range(12):
        daxian = analyze_daxian_sihua(chart, i)
        result["daxian"].append(daxian)

    # 如果指定了查询年份，分析流年四化
    if query_year:
        result["liunian"] = analyze_liunian_sihua(query_year)

    return result
```

**Step 3: 提交**

```bash
git add bazi_pro/core/ziwei/sihua.py
git commit -m "feat(ziwei): 实现流年四化分析"
```

---

### Phase 4: 星曜解读模块（3天）

**目标：** 实现 14 主星 × 12 宫位组合解读

#### Task 4.1: 实现星曜性质数据

**Objective:** 完善 14 主星性质数据

**Files:**
- Modify: `bazi_pro/core/ziwei/constants.py`

**Step 1: 完善 STAR_NATURE 数据**

```python
# 在 constants.py 中完善 STAR_NATURE

STAR_NATURE: dict[str, StarNature] = {
    "紫微": StarNature(
        name="紫微",
        五行="土",
        性情="尊贵、权威、领导力",
        象义="帝王之星，主贵气、权力、地位",
        吉凶="吉",
        宫位影响={
            "命宫": "尊贵有权威，领导才能，但易孤高",
            "财帛宫": "财运稳定，有贵人相助",
            "官禄宫": "事业顺利，有升迁机会",
            "夫妻宫": "配偶有气质，但易有压力",
            # ... 其他宫位
        }
    ),
    "天机": StarNature(
        name="天机",
        五行="木",
        性情="聪明、机变、多思",
        象义="智慧之星，主谋略、变化、宗教",
        吉凶="吉",
        宫位影响={
            "命宫": "聪明机智，善于谋略，但易多虑",
            # ... 其他宫位
        }
    ),
    # ... 其他 12 主星
}
```

**Step 2: 提交**

```bash
git add bazi_pro/core/ziwei/constants.py
git commit -m "feat(ziwei): 完善 14 主星性质数据"
```

#### Task 4.2: 实现星曜解读函数

**Objective:** 实现星曜在宫位的解读函数

**Files:**
- Create: `bazi_pro/core/ziwei/stars.py`

**Step 1: 创建 stars.py 并实现基础解读函数**

```python
# bazi_pro/core/ziwei/stars.py
"""
紫微斗数星曜解读模块

实现 14 主星在不同宫位的解读。
"""

from __future__ import annotations

from typing import Any

from bazi_pro.core.ziwei.constants import STAR_NATURE, StarNature


def get_star_nature(star_name: str) -> StarNature | None:
    """获取星曜性质

    Args:
        star_name: 星曜名称

    Returns:
        星曜性质，未找到返回 None
    """
    return STAR_NATURE.get(star_name)


def analyze_star_in_palace(star_name: str, palace_name: str, brightness: str = "") -> dict[str, Any]:
    """分析星曜在宫位的影响

    Args:
        star_name: 星曜名称
        palace_name: 宫位名称
        brightness: 亮度（bright/normal/dim）

    Returns:
        {
            "star": "星曜名称",
            "palace": "宫位名称",
            "brightness": "亮度",
            "nature": "星曜性质",
            "influence": "宫位影响",
            "description": "综合描述"
        }
    """
    star_nature = get_star_nature(star_name)
    if not star_nature:
        return {"error": f"未找到星曜: {star_name}"}

    # 获取宫位影响
    influence = star_nature.宫位影响.get(palace_name, "暂无解读")

    # 根据亮度调整描述
    brightness_desc = ""
    if brightness == "bright":
        brightness_desc = "（庙旺，吉力倍增）"
    elif brightness == "dim":
        brightness_desc = "（落陷，吉力减弱）"

    # 综合描述
    description = f"{star_name}入{palace_name}{brightness_desc}：{influence}"

    return {
        "star": star_name,
        "palace": palace_name,
        "brightness": brightness,
        "nature": star_nature.性情,
        "influence": influence,
        "description": description,
    }
```

**Step 2: 实现命宫主星分析**

```python
def analyze_ming_palace(chart: dict[str, Any]) -> dict[str, Any]:
    """分析命宫主星

    Args:
        chart: iztro-py 排盘结果

    Returns:
        {
            "major_stars": [{"star": "星名", "brightness": "亮度", "analysis": "分析"}, ...],
            "summary": "命宫主星综合分析"
        }
    """
    # 获取命宫
    ming_palace = None
    for palace in chart.get("palaces", []):
        if palace.get("name") == "命宫":
            ming_palace = palace
            break

    if not ming_palace:
        return {"error": "未找到命宫"}

    # 分析命宫主星
    major_stars = []
    for star in ming_palace.get("majorStars", []):
        star_name = star.get("name", "")
        brightness = star.get("brightness", "")

        analysis = analyze_star_in_palace(star_name, "命宫", brightness)
        major_stars.append(analysis)

    # 综合分析
    summary = "命宫主星："
    for star in major_stars:
        summary += f"\n- {star.get('description', '')}"

    return {
        "major_stars": major_stars,
        "summary": summary,
    }
```

**Step 3: 提交**

```bash
git add bazi_pro/core/ziwei/stars.py
git commit -m "feat(ziwei): 实现星曜解读函数"
```

---

### Phase 5: 叙述器模块（2天）

**目标：** 实现确定性叙述器（对标 narrator.py）

#### Task 5.1: 实现叙述器框架

**Objective:** 创建叙述器模块框架

**Files:**
- Create: `bazi_pro/core/ziwei/narrator.py`

**Step 1: 创建 narrator.py 并实现框架**

```python
# bazi_pro/core/ziwei/narrator.py
"""
紫微斗数确定性叙述器

从计算结果直接生成专业命理师风格的中文文本。
零 LLM 依赖，零幻觉风险。每句话都可追溯到确定性计算数据。

对标 bazi_pro/narrator.py 的架构。
"""

from __future__ import annotations

from typing import Any

from bazi_pro.core.ziwei.patterns import detect_patterns
from bazi_pro.core.ziwei.sihua import analyze_sihua
from bazi_pro.core.ziwei.stars import analyze_ming_palace, analyze_star_in_palace


def narrate_ziwei(chart: dict[str, Any], query_year: int | None = None) -> dict[str, str]:
    """生成紫微斗数确定性叙述

    Args:
        chart: iztro-py 排盘结果
        query_year: 查询年份（可选）

    Returns:
        {
            "overview": "命盘总览",
            "ming_palace": "命宫分析",
            "pattern": "格局分析",
            "sihua": "四化分析",
            "wealth": "财帛宫分析",
            "career": "官禄宫分析",
            "marriage": "夫妻宫分析",
            "health": "疾厄宫分析",
            "summary": "综合评述"
        }
    """
    result = {}

    # 1. 命宫分析
    result["ming_palace"] = narrate_ming_palace(chart)

    # 2. 格局分析
    result["pattern"] = narrate_patterns(chart)

    # 3. 四化分析
    result["sihua"] = narrate_sihua(chart, query_year)

    # 4. 财帛宫分析
    result["wealth"] = narrate_wealth_palace(chart)

    # 5. 官禄宫分析
    result["career"] = narrate_career_palace(chart)

    # 6. 夫妻宫分析
    result["marriage"] = narrate_marriage_palace(chart)

    # 7. 疾厄宫分析
    result["health"] = narrate_health_palace(chart)

    # 8. 综合评述
    result["summary"] = narrate_summary(chart, result)

    # 9. 命盘总览
    result["overview"] = narrate_overview(chart, result)

    return result
```

**Step 2: 提交**

```bash
git add bazi_pro/core/ziwei/narrator.py
git commit -m "feat(ziwei): 创建叙述器框架"
```

#### Task 5.2: 实现命宫叙述函数

**Objective:** 实现命宫分析叙述函数

**Files:**
- Modify: `bazi_pro/core/ziwei/narrator.py`

**Step 1: 实现命宫叙述函数**

```python
def narrate_ming_palace(chart: dict[str, Any]) -> str:
    """生成命宫分析叙述

    Args:
        chart: iztro-py 排盘结果

    Returns:
        命宫分析文本
    """
    # 分析命宫主星
    analysis = analyze_ming_palace(chart)
    if "error" in analysis:
        return f"命宫分析失败：{analysis['error']}"

    # 获取命宫信息
    ming_palace = None
    for palace in chart.get("palaces", []):
        if palace.get("name") == "命宫":
            ming_palace = palace
            break

    if not ming_palace:
        return "未找到命宫信息"

    # 生成叙述
    text = "【命宫分析】\n\n"

    # 主星分析
    major_stars = analysis.get("major_stars", [])
    if major_stars:
        text += "命宫主星：\n"
        for star in major_stars:
            text += f"- {star.get('star', '')}（{star.get('brightness', '平')}）：{star.get('influence', '')}\n"
    else:
        text += "命宫无主星，借对宫主星之力。\n"

    # 辅星分析
    minor_stars = [s.get("name") for s in ming_palace.get("minorStars", [])]
    if minor_stars:
        text += f"\n辅星：{'、'.join(minor_stars)}\n"

    return text
```

**Step 2: 提交**

```bash
git add bazi_pro/core/ziwei/narrator.py
git commit -m "feat(ziwei): 实现命宫叙述函数"
```

#### Task 5.3: 实现格局叙述函数

**Objective:** 实现格局分析叙述函数

**Files:**
- Modify: `bazi_pro/core/ziwei/narrator.py`

**Step 1: 实现格局叙述函数**

```python
def narrate_patterns(chart: dict[str, Any]) -> str:
    """生成格局分析叙述

    Args:
        chart: iztro-py 排盘结果

    Returns:
        格局分析文本
    """
    # 检测格局
    patterns = detect_patterns(chart)

    if not patterns:
        return "【格局分析】\n\n未检测到特殊格局，以正格论。\n"

    # 生成叙述
    text = "【格局分析】\n\n"

    # 按等级分组
    excellent = [p for p in patterns if p.level == "excellent"]
    good = [p for p in patterns if p.level == "good"]
    neutral = [p for p in patterns if p.level == "neutral"]
    caution = [p for p in patterns if p.level == "caution"]

    if excellent:
        text += "上格：\n"
        for p in excellent:
            text += f"- {p.name}：{p.description}\n"
            if p.source:
                text += f"  （出处：{p.source}）\n"

    if good:
        text += "\n中格：\n"
        for p in good:
            text += f"- {p.name}：{p.description}\n"

    if caution:
        text += "\n警示格：\n"
        for p in caution:
            text += f"- {p.name}：{p.description}\n"

    return text
```

**Step 2: 提交**

```bash
git add bazi_pro/core/ziwei/narrator.py
git commit -m "feat(ziwei): 实现格局叙述函数"
```

#### Task 5.4: 实现其他宫位叙述函数

**Objective:** 实现财帛宫、官禄宫、夫妻宫、疾厄宫叙述函数

**Files:**
- Modify: `bazi_pro/core/ziwei/narrator.py`

**Step 1: 实现财帛宫叙述函数**

```python
def narrate_wealth_palace(chart: dict[str, Any]) -> str:
    """生成财帛宫分析叙述"""
    # 获取财帛宫
    wealth_palace = None
    for palace in chart.get("palaces", []):
        if palace.get("name") == "财帛宫":
            wealth_palace = palace
            break

    if not wealth_palace:
        return "未找到财帛宫信息"

    text = "【财帛宫分析】\n\n"

    # 主星分析
    major_stars = [s.get("name") for s in wealth_palace.get("majorStars", [])]
    if major_stars:
        text += "财帛宫主星：\n"
        for star in major_stars:
            analysis = analyze_star_in_palace(star, "财帛宫")
            text += f"- {analysis.get('description', '')}\n"
    else:
        text += "财帛宫无主星，借对宫主星之力。\n"

    return text
```

**Step 2: 实现其他宫位叙述函数**

```python
def narrate_career_palace(chart: dict[str, Any]) -> str:
    """生成官禄宫分析叙述"""
    # TODO: 实现
    pass

def narrate_marriage_palace(chart: dict[str, Any]) -> str:
    """生成夫妻宫分析叙述"""
    # TODO: 实现
    pass

def narrate_health_palace(chart: dict[str, Any]) -> str:
    """生成疾厄宫分析叙述"""
    # TODO: 实现
    pass
```

**Step 3: 提交**

```bash
git add bazi_pro/core/ziwei/narrator.py
git commit -m "feat(ziwei): 实现其他宫位叙述函数"
```

#### Task 5.5: 实现四化叙述和综合评述

**Objective:** 实现四化分析叙述和综合评述函数

**Files:**
- Modify: `bazi_pro/core/ziwei/narrator.py`

**Step 1: 实现四化叙述函数**

```python
def narrate_sihua(chart: dict[str, Any], query_year: int | None = None) -> str:
    """生成四化分析叙述

    Args:
        chart: iztro-py 排盘结果
        query_year: 查询年份（可选）

    Returns:
        四化分析文本
    """
    # 分析四化
    sihua_analysis = analyze_sihua(chart, query_year)

    text = "【四化分析】\n\n"

    # 本命四化
    benming = sihua_analysis.get("benming", {})
    sihua = benming.get("sihua", {})
    text += "本命四化：\n"
    text += f"- 化禄：{sihua.get('化禄', '无')}\n"
    text += f"- 化权：{sihua.get('化权', '无')}\n"
    text += f"- 化科：{sihua.get('化科', '无')}\n"
    text += f"- 化忌：{sihua.get('化忌', '无')}\n"

    # 流年四化（如果指定了年份）
    if query_year and "liunian" in sihua_analysis:
        liunian = sihua_analysis["liunian"]
        liunian_sihua = liunian.get("sihua", {})
        text += f"\n{query_year}年流年四化：\n"
        text += f"- 化禄：{liunian_sihua.get('化禄', '无')}\n"
        text += f"- 化权：{liunian_sihua.get('化权', '无')}\n"
        text += f"- 化科：{liunian_sihua.get('化科', '无')}\n"
        text += f"- 化忌：{liunian_sihua.get('化忌', '无')}\n"

    return text
```

**Step 2: 实现综合评述函数**

```python
def narrate_summary(chart: dict[str, Any], sections: dict[str, str]) -> str:
    """生成综合评述

    Args:
        chart: iztro-py 排盘结果
        sections: 各维度叙述文本

    Returns:
        综合评述文本
    """
    text = "【综合评述】\n\n"

    # 获取命盘基本信息
    soul = chart.get("soul", "")  # 命主
    body = chart.get("body", "")  # 身主
    five_elements_class = chart.get("fiveElementsClass", "")  # 五行局

    text += f"命主：{soul}，身主：{body}，五行局：{five_elements_class}\n\n"

    # 综合各维度分析
    # TODO: 根据各维度叙述生成综合评述

    return text
```

**Step 3: 实现命盘总览函数**

```python
def narrate_overview(chart: dict[str, Any], sections: dict[str, str]) -> str:
    """生成命盘总览

    Args:
        chart: iztro-py 排盘结果
        sections: 各维度叙述文本

    Returns:
        命盘总览文本
    """
    text = "【命盘总览】\n\n"

    # 获取基本信息
    soul = chart.get("soul", "")
    body = chart.get("body", "")
    five_elements_class = chart.get("fiveElementsClass", "")

    text += f"命主：{soul}，身主：{body}，五行局：{five_elements_class}\n\n"

    # 提取关键信息
    ming_palace_text = sections.get("ming_palace", "")
    pattern_text = sections.get("pattern", "")

    # 生成总述
    text += "命宫主星决定了命主的基本性格和人生走向。\n"
    text += "格局高低反映了命主的先天禀赋和后天发展潜力。\n"
    text += "四化星曜的动态变化影响着不同阶段的运势起伏。\n"

    return text
```

**Step 4: 提交**

```bash
git add bazi_pro/core/ziwei/narrator.py
git commit -m "feat(ziwei): 实现四化叙述和综合评述"
```

---

### Phase 6: API 集成（1天）

**目标：** 将紫微斗数分析功能集成到 server/ziwei.py

#### Task 6.1: 扩展 server/ziwei.py

**Objective:** 扩展现有 API 支持格局、四化、星曜分析

**Files:**
- Modify: `server/ziwei.py`

**Step 1: 添加格局分析 API**

```python
# 在 server/ziwei.py 中添加

def get_ziwei_patterns(
    solar_date: str,
    hour: int,
    gender: int | str = 1,
) -> dict[str, Any]:
    """获取紫微斗数格局分析

    Args:
        solar_date: 阳历日期
        hour: 出生小时
        gender: 性别

    Returns:
        格局分析结果
    """
    if by_solar is None:
        return {"error": "iztro-py 未安装"}

    time_index = hour_to_time_index(hour)
    gender_cn = gender_to_chinese(gender)

    try:
        astrolabe = by_solar(
            solar_date=solar_date,
            time_index=time_index,
            gender=gender_cn,
            language="zh-CN",
        )
        chart = astrolabe.to_iztro_dict()

        # 检测格局
        from bazi_pro.core.ziwei.patterns import detect_patterns
        patterns = detect_patterns(chart)

        return {
            "patterns": [
                {
                    "name": p.name,
                    "level": p.level,
                    "description": p.description,
                    "source": p.source,
                }
                for p in patterns
            ]
        }
    except Exception as e:
        return {"error": f"格局分析失败: {e}"}
```

**Step 2: 添加四化分析 API**

```python
def get_ziwei_sihua(
    solar_date: str,
    hour: int,
    gender: int | str = 1,
    query_year: int | None = None,
) -> dict[str, Any]:
    """获取紫微斗数四化分析

    Args:
        solar_date: 阳历日期
        hour: 出生小时
        gender: 性别
        query_year: 查询年份

    Returns:
        四化分析结果
    """
    if by_solar is None:
        return {"error": "iztro-py 未安装"}

    time_index = hour_to_time_index(hour)
    gender_cn = gender_to_chinese(gender)

    try:
        astrolabe = by_solar(
            solar_date=solar_date,
            time_index=time_index,
            gender=gender_cn,
            language="zh-CN",
        )
        chart = astrolabe.to_iztro_dict()

        # 分析四化
        from bazi_pro.core.ziwei.sihua import analyze_sihua
        sihua = analyze_sihua(chart, query_year)

        return sihua
    except Exception as e:
        return {"error": f"四化分析失败: {e}"}
```

**Step 3: 添加综合分析 API**

```python
def get_ziwei_analysis(
    solar_date: str,
    hour: int,
    gender: int | str = 1,
    query_year: int | None = None,
) -> dict[str, Any]:
    """获取紫微斗数综合分析（格局+四化+星曜+叙述）

    Args:
        solar_date: 阳历日期
        hour: 出生小时
        gender: 性别
        query_year: 查询年份

    Returns:
        综合分析结果
    """
    if by_solar is None:
        return {"error": "iztro-py 未安装"}

    time_index = hour_to_time_index(hour)
    gender_cn = gender_to_chinese(gender)

    try:
        astrolabe = by_solar(
            solar_date=solar_date,
            time_index=time_index,
            gender=gender_cn,
            language="zh-CN",
        )
        chart = astrolabe.to_iztro_dict()

        # 生成叙述
        from bazi_pro.core.ziwei.narrator import narrate_ziwei
        narration = narrate_ziwei(chart, query_year)

        return {
            "chart": chart,
            "narration": narration,
        }
    except Exception as e:
        return {"error": f"综合分析失败: {e}"}
```

**Step 4: 提交**

```bash
git add server/ziwei.py
git commit -m "feat(ziwei): 扩展 API 支持格局、四化、星曜分析"
```

---

### Phase 7: 测试（1天）

**目标：** 编写测试用例确保功能正确

#### Task 7.1: 编写格局识别测试

**Objective:** 编写格局识别模块的测试用例

**Files:**
- Create: `tests/test_ziwei.py`

**Step 1: 创建测试文件并编写格局识别测试**

```python
# tests/test_ziwei.py
"""
紫微斗数模块测试
"""

import pytest
from bazi_pro.core.ziwei.patterns import detect_patterns, detect_zi_fu
from bazi_pro.core.ziwei.sihua import analyze_sihua, get_sihua_by_stem
from bazi_pro.core.ziwei.stars import analyze_star_in_palace, analyze_ming_palace
from bazi_pro.core.ziwei.narrator import narrate_ziwei


class TestPatterns:
    """格局识别测试"""

    def test_detect_zi_fu(self):
        """测试紫府同宫格检测"""
        # 模拟紫微天府同宫寅宫的排盘数据
        chart = {
            "palaces": [
                {
                    "name": "命宫",
                    "earthlyBranch": "寅",
                    "majorStars": [
                        {"name": "紫微", "brightness": "bright"},
                        {"name": "天府", "brightness": "bright"},
                    ],
                },
                # ... 其他宫位
            ]
        }

        pattern = detect_zi_fu(chart)
        assert pattern is not None
        assert pattern.name == "紫府同宫"
        assert pattern.level == "excellent"

    def test_detect_patterns(self):
        """测试格局检测主函数"""
        # 模拟排盘数据
        chart = {
            "palaces": [
                # ... 宫位数据
            ]
        }

        patterns = detect_patterns(chart)
        assert isinstance(patterns, list)
```

**Step 2: 运行测试**

```bash
python -m pytest tests/test_ziwei.py::TestPatterns -v
```

**Step 3: 提交**

```bash
git add tests/test_ziwei.py
git commit -m "test(ziwei): 添加格局识别测试"
```

#### Task 7.2: 编写四化分析测试

**Objective:** 编写四化分析模块的测试用例

**Files:**
- Modify: `tests/test_ziwei.py`

**Step 1: 添加四化分析测试**

```python
class TestSihua:
    """四化分析测试"""

    def test_get_sihua_by_stem(self):
        """测试天干四化查询"""
        sihua = get_sihua_by_stem("甲")
        assert sihua == {
            "化禄": "廉贞",
            "化权": "破军",
            "化科": "武曲",
            "化忌": "太阳",
        }

    def test_analyze_benming_sihua(self):
        """测试本命四化分析"""
        # 模拟排盘数据
        chart = {
            "yearStem": "甲",
            "palaces": [
                {
                    "name": "命宫",
                    "majorStars": [
                        {"name": "廉贞", "brightness": "bright"},
                    ],
                },
                # ... 其他宫位
            ]
        }

        result = analyze_sihua(chart)
        assert "benming" in result
        assert "sihua" in result["benming"]
```

**Step 2: 运行测试**

```bash
python -m pytest tests/test_ziwei.py::TestSihua -v
```

**Step 3: 提交**

```bash
git add tests/test_ziwei.py
git commit -m "test(ziwei): 添加四化分析测试"
```

#### Task 7.3: 编写叙述器测试

**Objective:** 编写叙述器模块的测试用例

**Files:**
- Modify: `tests/test_ziwei.py`

**Step 1: 添加叙述器测试**

```python
class TestNarrator:
    """叙述器测试"""

    def test_narrate_ziwei(self):
        """测试紫微斗数叙述器"""
        # 模拟排盘数据
        chart = {
            "soul": "紫微",
            "body": "天机",
            "fiveElementsClass": "水二局",
            "palaces": [
                {
                    "name": "命宫",
                    "majorStars": [
                        {"name": "紫微", "brightness": "bright"},
                    ],
                    "minorStars": [],
                },
                # ... 其他宫位
            ]
        }

        result = narrate_ziwei(chart)
        assert "ming_palace" in result
        assert "pattern" in result
        assert "sihua" in result
        assert "overview" in result
```

**Step 2: 运行测试**

```bash
python -m pytest tests/test_ziwei.py::TestNarrator -v
```

**Step 3: 提交**

```bash
git add tests/test_ziwei.py
git commit -m "test(ziwei): 添加叙述器测试"
```

---

## 📋 验证命令

完成所有任务后，运行以下验证命令：

```bash
# 1. 编译检查
python -m compileall bazi_pro/core/ziwei server/ziwei.py -q

# 2. 运行测试
python -m pytest tests/test_ziwei.py -v

# 3. 集成测试
python -c "from bazi_pro.core.ziwei import narrate_ziwei; print('✅ 紫微斗数模块导入成功')"
```

---

## 🎯 里程碑

| 阶段 | 任务 | 预计时间 | 交付物 |
|------|------|----------|--------|
| Phase 1 | 核心数据结构 | 1天 | constants.py, utils.py |
| Phase 2 | 格局识别 | 2-3天 | patterns.py (42格局) |
| Phase 3 | 四化分析 | 2天 | sihua.py |
| Phase 4 | 星曜解读 | 3天 | stars.py |
| Phase 5 | 叙述器 | 2天 | narrator.py |
| Phase 6 | API集成 | 1天 | server/ziwei.py 扩展 |
| Phase 7 | 测试 | 1天 | test_ziwei.py |
| **总计** | | **12-14天** | 完整紫微斗数分析功能 |

---

## 📚 参考资料

- **iztro-py 文档**: https://github.com/spyfree/iztro-py
- **Renhuai123/ziwei-doushu**: https://github.com/Renhuai123/ziwei-doushu
- **《紫微斗数全书》**: 古籍原文
- **《骨髓赋》**: 格局判定依据
- **bazi_pro/narrator.py**: 叙述器架构参考
