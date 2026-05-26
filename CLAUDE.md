# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project identity

`bazi-pro` v5.0 — 确定性八字命理计算引擎 + LLM 解读框架。

核心原则：**算析分离** — `bazi_pro/core/` 做所有确定性命理计算（十神、藏干、五行力量、旺衰、格局、喜用神、刑冲合害），LLM 只负责解读，不参与计算。

## Build and test commands

```bash
pip install -e .                              # 最小安装（核心 + 检索）
pip install -e ".[all]"                       # 完整安装（含 hybrid、report、pdf、tui）

# 主测试 — 98 golden-case 边界回归测试
python tests/run_golden.py

# 全量 pytest（排除 server 依赖测试）
python -m pytest tests/ -v

# 环境诊断（15 项检查）
python scripts/doctor.py

# Lint
ruff check bazi_pro/ tests/ scripts/

# Trace 管线验证
python -m bazi_pro.trace demo > trace.json && python -m bazi_pro.trace validate trace.json

# 版本一致性检查（CI 使用）
python scripts/check_version_consistency.py

# 编译检查（捕获语法错误）
python -m compileall bazi_pro scripts tests -q
```

## Architecture

```
Bazi MCP JSON input
       │
       ▼
┌─────────────────────────────────────────┐
│  Deterministic Core (bazi_pro/core/)    │  ← 13 模块，纯数据变换
│  full_analysis() → dict                 │     绝不含 LLM 逻辑
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Classical Retrieval (BM25 + FAISS)     │  ← 2964 条古籍，6 部经典
│  retrieve_classical.py / hybrid_search  │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Evidence + Trace Pipeline              │  ← evidence.py → trace.py → view_model.py
│  Structured JSON: claim + confidence    │
└─────────────────────────────────────────┘
       │
       ├──→ UI renderers (bazi_pro/ui/)   ← 接受 DashboardVM
       └──→ Plugin hooks (plugins/)
```

**数据流**: `full_analysis(mcp_json)` → `TraceBuilder` → `analysis_trace.json` → `build_vm_from_trace()` → `DashboardVM` → UI 渲染器。

**两个导入路径**:
- `bazi_pro.core.full_analysis` — 正式路径
- `bazi_pro.core_rules.full_analysis` — 已废弃 shim，会发 DeprecationWarning

**SDK 入口**: `bazi_pro.AnalysisEngine` 封装 core + retrieval + report 生成。

## Key modules

| 模块 | 职责 |
|------|------|
| `bazi_pro/core/constants.py` | 天干地支映射、十神推导 |
| `bazi_pro/core/patterns.py` | 六层格局筛查（化气→专旺→从格→层1→层2→层3） |
| `bazi_pro/core/yongshen.py` | 用神/喜神/忌神推导 |
| `bazi_pro/core/strength.py` | 旺衰判定（得令/得地/得势） |
| `bazi_pro/core/relations.py` | 刑冲合害检测 + 天干合化 |
| `bazi_pro/core/disease.py` | 格局之病检测（5 类） |
| `bazi_pro/core/tiaohou.py` | 调候用神查表（穷通宝鉴 120 条） |
| `bazi_pro/view_model.py` | DashboardVM 数据契约 |
| `bazi_pro/ui/consumer_report.py` | 消费级报告（六维叙事 + 术语解释） |
| `bazi_pro/generate_report.py` | 报告生成 CLI（3 种模式） |

## Critical constraints

1. **No LLM logic in `bazi_pro/core/`** — 纯确定性计算。
2. **No fabricated citations** — 每条古籍引用必须可追溯到 `retrieve_classical.py` 输出。
3. **UI data contract** — 所有 UI 组件只接受 `DashboardVM` dataclass，不做正则提取。
4. **Golden case count can never decrease** — 当前 98。
5. **推导 vs 推算** — 确定性映射（干→五行、干→十神）是推导（允许）；脆弱数学链是推算（禁止）。
6. **Linear execution** — SKILL.md 10 步流程顺序执行，不回填。

## Report modes

| 模式 | CLI | 受众 | 说明 |
|------|-----|------|------|
| `report` | `--mode report` | 命理师 | 技术报告，完整表格和评分 |
| `dashboard` | `--mode dashboard` | 命理师 | 交互式仪表盘，SVG 图表 + 证据链 |
| `consumer` | `--mode consumer` | 普通用户 | 消费级报告，结论先行 + 六维叙事 |

## Key gotchas

- **`core_rules.py` 是废弃 shim** — 内部代码应从 `bazi_pro.core` 导入。
- **建禄月劫格** — 层1/2/3 都走 `_build_jianlu_yuejie()`，输出 `建禄格，透X` 而非 `比肩格`。
- **`percent` vs `percent_adjusted`** — `calc_element_forces()` 返回两者。格局筛查用 `percent`（原始），化气格用 `percent_adjusted`（合化修正）。
- **从格用神方向** — 从强/专旺→印星，从财→财星，从官杀→官杀，从儿→食伤。忌神是逆势五行。
- **建禄月劫格用神** — 由格局名中"透X"决定，不是盲取 PATTERN_YONGSHEN 表。
- **Windows 兼容** — 子进程测试使用 `sys.executable`（非 `python3`），文件读写指定 `encoding="utf-8"`。
- **Server 模块可选** — `server/` 依赖 fastapi/pydantic，不装也不影响核心功能，相关测试自动跳过。

## Plugin system

`plugins/{name}/` 含 `plugin.json` + `main.py`，实现 `BaziPlugin` ABC（hooks: `on_retrieve`, `on_evidence`, `on_render`）。插件只能装饰输出，不能修改核心数据。

## Version update checklist

更新版本时同步修改：`bazi_pro/__init__.py`（唯一源）、`pyproject.toml`、`SKILL.md` frontmatter、`README.md` badge、`CODE_WIKI.md`（大版本时）。
