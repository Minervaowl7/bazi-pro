# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project identity

`bazi-pro` v5.1 — 确定性八字命理计算引擎 + 古籍对齐引擎 + 多流派分析路径 + LLM 解读框架 + Web 应用。

核心原则：**算析分离** — `bazi_pro/core/` 做所有确定性命理计算（十神、藏干、五行力量、旺衰、格局、喜用神、刑冲合害、破格检测），LLM 只负责解读，不参与计算。

## Build and test commands

```bash
pip install -e .                              # 最小安装（核心 + 检索）
pip install -e ".[all]"                       # 完整安装（含 hybrid、report、pdf、tui、server）

# 主测试 — 103 golden-case 边界回归测试
python tests/run_golden.py

# 全量 pytest（排除 server 依赖测试）
python -m pytest tests/ -v

# 单个测试文件
python -m pytest tests/test_core.py -v

# 流派测试
python -m pytest tests/test_schools.py -v

# 环境诊断（15 项检查）
python scripts/doctor.py

# Lint
ruff check server/ bazi_pro/ tests/

# Golden case 审计
python scripts/audit_golden_cases.py

# 编译检查（捕获语法错误）
python -m compileall bazi_pro scripts tests -q

# 启动后端 (端口 8710)
python -m uvicorn server.app:app --host 127.0.0.1 --port 8710

# 启动前端 (端口 3000，需先 cd frontend && pnpm install)
cd frontend && pnpm dev
```

## Architecture

```
用户输入 (Web 表单 / MCP JSON)
       │
       ▼
┌─────────────────────────────────────────┐
│  Deterministic Core (bazi_pro/core/)    │  ← 13 模块，纯数据变换
│  full_analysis() → dict                 │     绝不含 LLM 逻辑
│  含：破格检测 + 方局/月令检查            │
└─────────────────────────────────────────┘
       │
       ├──→ ┌──────────────────────────────────────┐
       │     │  Multi-School Analysis (schools/)    │
       │     │  ZipingAnalyzer · MangpaiAnalyzer    │
       │     │  XinpaiAnalyzer · school_analyze()   │
       │     └──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Classical Retrieval (BM25 + FAISS)     │  ← 2964 条古籍，6 部经典
│  retrieve_classical.py / hybrid_search  │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Narrator (bazi_pro/narrator.py)        │  ← 确定性文本生成，零 LLM
│  narrate_analysis() → 9 维度中文文本     │     每句可追溯到计算数据
└─────────────────────────────────────────┘
       │
       ├──→ FastAPI Server (server/)      ← REST + SSE + SQLite + 流派选择
       ├──→ Next.js Frontend (frontend/)  ← 暗色主题 Web 应用 + 流派对比
       ├──→ UI renderers (bazi_pro/ui/)   ← 接受 DashboardVM
       └──→ Plugin hooks (plugins/)
```

**数据流**: `full_analysis(mcp_json)` → `TraceBuilder` → `analysis_trace.json` → `build_vm_from_trace()` → `DashboardVM` → UI 渲染器。

**流派数据流**: `school_analyze(mcp_json, school='ziping')` → `ZipingAnalyzer.analyze()` → 流派特定结果。

**Web 数据流**: `POST /api/v2/analyze?school=ziping` → `run_analysis()` → SQLite 存储 → `GET /api/v2/analysis/{id}` 返回 result + narration。

**两个导入路径**:
- `bazi_pro.core.full_analysis` — 正式路径
- `bazi_pro.core_rules.full_analysis` — 已废弃 shim，会发 DeprecationWarning

**SDK 入口**: `bazi_pro.AnalysisEngine` 封装 core + retrieval + report 生成。

## Web application (P0)

**后端** (`server/`):
- FastAPI 应用，默认端口 8710
- 原有路由 (`/api/analyze`, `/api/status/{id}`, `/api/result/{id}`) 使用 WebSocket 推送
- 新路由 (`/api/v2/*`) 使用 SSE 流式 + SQLite 持久化
- `POST /api/v2/analyze` 支持 `school` 参数（ziping/mangpai/xinpai/all）
- `POST /api/v2/analyze/compare` 返回三流派对比分析
- `server/db.py`: aiosqlite 存储层，`BAZI_DB_PATH` 环境变量配置路径
- CORS 默认允许 `localhost:3000`

**前端** (`frontend/`):
- Next.js 14 App Router + TypeScript + Tailwind CSS + Zustand + ECharts
- `pnpm` 包管理，`NEXT_PUBLIC_API_URL` 配置后端地址（默认 `http://127.0.0.1:8710`）
- 暗色主题（DeepOracle 风格），所有 UI 文本为中文
- 流派选择下拉框 + SchoolComparePanel 三列对比
- BaziChartCard 显示 formation（方局信息）+ break_conditions（破格条件）

**叙述器** (`bazi_pro/narrator.py`):
- 从计算结果直接生成 9 维度专业中文文本（旺衰/格局/用神/调候/五行/刑冲/性格/事业）
- 零 LLM 依赖，每句话锚定在确定性数据上
- API 响应中作为 `narration` 字段返回

## Key modules

| 模块 | 职责 |
|------|------|
| `bazi_pro/core/constants.py` | 天干地支映射、十神推导 |
| `bazi_pro/core/patterns.py` | 六层格局筛查 + 破格检测（专旺/化气/从格/建禄/羊刃/正格） |
| `bazi_pro/core/yongshen.py` | 用神/喜神/忌神推导 |
| `bazi_pro/core/strength.py` | 旺衰判定（得令/得地/得势） |
| `bazi_pro/core/relations.py` | 刑冲合害检测 + 天干合化 |
| `bazi_pro/core/disease.py` | 格局之病检测（5 类） |
| `bazi_pro/core/tiaohou.py` | 调候用神查表（穷通宝鉴 120 条） |
| `bazi_pro/core/schools/base.py` | SchoolAnalyzer 抽象基类 |
| `bazi_pro/core/schools/__init__.py` | SCHOOL_REGISTRY + school_analyze() + register_school() |
| `bazi_pro/core/schools/ziping.py` | 传统子平法（格局用神 + 破格感知用神调整 + 大运吉凶） |
| `bazi_pro/core/schools/mangpai.py` | 盲派（宾主/做功/体用/功力/应期） |
| `bazi_pro/core/schools/xinpai.py` | 新派（百神论/空亡论/反断论） |
| `bazi_pro/narrator.py` | 确定性叙述器（9 维度中文文本生成） |
| `bazi_pro/view_model.py` | DashboardVM 数据契约 |
| `bazi_pro/ui/consumer_report.py` | 消费级报告（六维叙事 + 术语解释） |
| `bazi_pro/generate_report.py` | 报告生成 CLI（3 种模式） |
| `server/app.py` | FastAPI 应用（REST + SSE + WebSocket + 流派选择 + 对比端点） |
| `server/db.py` | SQLite 存储层（aiosqlite） |
| `server/analysis.py` | 异步分析编排（调用 core + schools 模块） |

## Critical constraints

1. **No LLM logic in `bazi_pro/core/`** — 纯确定性计算。
2. **No fabricated citations** — 每条古籍引用必须可追溯到 `retrieve_classical.py` 输出。
3. **UI data contract** — 所有 UI 组件只接受 `DashboardVM` dataclass，不做正则提取。
4. **Golden case count can never decrease** — 当前 103。
5. **推导 vs 推算** — 确定性映射（干→五行、干→十神）是推导（允许）；脆弱数学链是推算（禁止）。
6. **Linear execution** — SKILL.md 10 步流程顺序执行，不回填。
7. **DO NOT modify existing `server/analysis.py`** — 只扩展，不重写。
8. **Narrator 零幻觉** — `narrator.py` 每句话必须可追溯到计算数据，不允许模糊表述。
9. **SchoolAnalyzer 注册** — 新流派必须继承 `SchoolAnalyzer` 基类，调用 `register_school()` 注册，并在 `schools/__init__.py` 的 `_ensure_schools_loaded()` 中添加 lazy import。
10. **破格检测必须有古籍依据** — 每个破格类型必须引用子平真诠/渊海子平/滴天髓/神峰通考原文。

## 古籍对齐规则 (v5.1)

### 专旺格
- 必须有地支方局/三合局（`_check_formation()`），无则降级为从强格
- 必须月令当令（`_check_month_season()`）
- 破格：官杀逆势（high）、引至死绝（medium）

### 化气格
- 月令当令=真化（confidence=0.85），不当令=假化（confidence=0.60）
- 地支根局提升 confidence +0.05
- 破格：争合（high）、妒合（high）、克化神（medium）

### 从格
- 从财须会财、从杀须会杀（`_check_formation()`）
- 有局=真从（0.85），无局=假从（0.65）
- 破格：命逢根气（high）
- 从儿格须财星≥1（滴天髓"只要吾儿又得儿"）

### 建禄/羊刃/正格
- 建禄格破格：孤官无辅（medium）、会杀为凶（high）
- 羊刃格破格：透刃合煞（high）
- 正官格破格：伤官见官（high）
- 财格破格：比劫争财（high）
- 印格破格：财星破印（high）
- 食神格破格：枭神夺食（high）
- 伤官格破格：伤官见官（high，金水伤官除外）

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
- **前端包管理** — 使用 `pnpm`（非 npm/yarn），lock 文件为 `pnpm-lock.yaml`。
- **SSE 事件缓冲** — `/api/v2/analysis/{id}/stream` 缓冲已发送事件，迟连接客户端可回放。
- **Schools lazy loading** — `schools/__init__.py` 使用 `_ensure_schools_loaded()` 延迟导入，避免循环依赖。import 语句用 `import bazi_pro.core.schools.xxx` 风格（非 `from ... import`），加 `# noqa: F401`。
- **register_school 位置** — 在各流派模块底部调用 `register_school()`，import 在顶部（ziping.py 需 `# noqa: E402`）。
- **破格检测函数签名** — `_screen_layer1/2/3` 和 `_build_jianlu_yuejie` 需要传入 `bazi_parts` 参数。
- **金水伤官除外** — 伤官格破格检测中，庚/辛日主（金日主）的伤官见官不标记破格。

## Plugin system

`plugins/{name}/` 含 `plugin.json` + `main.py`，实现 `BaziPlugin` ABC（hooks: `on_retrieve`, `on_evidence`, `on_render`）。插件只能装饰输出，不能修改核心数据。

## Version update checklist

更新版本时同步修改：`bazi_pro/__init__.py`（唯一源）、`pyproject.toml`、`SKILL.md` frontmatter、`README.md` badge、`CODE_WIKI.md`（大版本时）。
