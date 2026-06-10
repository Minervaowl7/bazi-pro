# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project identity

`bazi-pro` v5.3 — 确定性八字命理计算引擎 + 古籍对齐引擎 + 多流派分析路径（典籍对齐版） + LLM 解读框架 + Web 应用。

核心原则：**算析分离** — `bazi_pro/core/` 做所有确定性命理计算（十神、藏干、五行力量、旺衰、格局、喜用神、刑冲合害、破格检测），LLM 只负责解读，不参与计算。

**v5.3 重大更新**：核心格局判定三项古籍对齐修正——会方检测收紧（对齐《滴天髓》"方是方兮局是局"）· 从强格官杀guard（对齐《渊海子平》"官印双全"）· 三刑优先于两刑（对齐《三命通会》）· 阴干墓库加深（对齐《滴天髓》"阴逢库为无用"）· 调候整合喜神（对齐《子平真诠》"论用神配气候得失"）。详见 README.md 版本历史。

## 环境要求

- **Python >= 3.10** — 使用了 `list[dict]`、`dict | None` 等 3.10+ 类型注解语法
- **Node.js >= 18** — Next.js 16 要求
- **pnpm** — 前端包管理器（非 npm/yarn）

## Build and test commands

```bash
pip install -e .                              # 最小安装（核心 + 检索）
pip install -e ".[all]"                       # 完整安装（含 hybrid、report、pdf、tui、server）

# 主测试 — golden-case 边界回归测试
python tests/run_golden.py

# 全量 pytest（排除 server 依赖测试）
python -m pytest tests/ -v

# 单个测试文件
python -m pytest tests/test_core.py -v

# 流派测试
python -m pytest tests/test_schools.py -v

# 环境诊断（15 项检查）
python scripts/doctor.py

# Python lint
ruff check server/ bazi_pro/ tests/

# 编译检查（捕获语法错误）
python -m compileall bazi_pro scripts tests -q

# 启动后端 (端口 8711，与前端默认 API_BASE 匹配)
python -m uvicorn server.app:app --host 127.0.0.1 --port 8711

# 前端（端口 3000）
cd frontend && pnpm install
cd frontend && pnpm dev          # 开发
cd frontend && pnpm build        # 生产构建
cd frontend && pnpm lint         # ESLint（零 warning 策略）
cd frontend && npx tsc --noEmit  # TypeScript 类型检查

# 一键启动（后端 + 前端）
.\start.ps1                      # Windows PowerShell
.\start.bat                      # Windows CMD
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
       │     │  盲派: 宾主/体用/6种做功/贼神捕神/势  │
       │     │  新派: 百神/空亡/反断/格局分类/出空   │
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
       ├──→ Next.js Frontend (frontend/)  ← 亮色/暗色双主题 Web 应用 + 流派对比
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
- FastAPI 应用，通过 uvicorn 启动（推荐端口 8711）
- 双版本 API：v1（WebSocket 推送，遗留）和 v2（SSE 流式 + SQLite 持久化）
- `POST /api/v2/analyze` 支持 `school` 参数（ziping/mangpai/xinpai/all），`POST /api/v2/analyze/compare` 返回三流派对比
- 其他端点：合婚（`/api/v2/hehun`）、每日运势、日柱反查、城市列表
- LLM 配置：`LLM_API_KEY` / `LLM_API_BASE` / `LLM_MODEL` / `LLM_TIMEOUT`（默认 300s）环境变量（见 `.env.example`）
- CORS 默认允许 `localhost:3000`
- 详细模块列表见下方 "Key modules > Web 服务" 表

**前端** (`frontend/`):
- Next.js 16 App Router + TypeScript + Tailwind CSS v4 (PostCSS) + Zustand + ECharts
- `pnpm` 包管理，`NEXT_PUBLIC_API_URL` 配置后端地址（默认 `http://127.0.0.1:8711`）
- 亮色/暗色双主题（默认亮色），所有 UI 文本为中文
- 全局 Navbar（排盘/合婚导航 + 主题切换）
- 路由：`/`（首页表单）、`/analyze/[id]`（分析结果）、`/compare`（合婚）
- **设计令牌**：`globals.css` 为单一来源，组件通过 `var(--xxx)` 引用。JS 层 `constants.ts` 镜像 CSS 变量
- **CSS 工具类**：`.card`（卡片容器）、`.form-input`/`.form-label`（表单）、`.hover-scale`/`.hover-lift`/`.hover-row`/`.hover-card`（hover 交互）、`.focus-ring`（焦点态）、`.gold-divider`/`.cinnabar-bar`（装饰线）
- **prefers-reduced-motion**：JS 动画使用 `usePrefersReducedMotion` hook（`lib/usePrefersReducedMotion.ts`），CSS 动画由 `@media (prefers-reduced-motion: reduce)` 兜底
- **Navbar 滚动态**：`color-mix(in srgb, var(--bg) 92%, transparent)` + `backdrop-filter`，仅在 `scrollY > 10` 时生效
- 核心组件：BaziChartCard（四柱卡片）、SchoolPanel/SchoolComparePanel（流派分析）、DayunTimeline（大运）、ShishenEnergyChart（十神能量）、RelationGraph（关系图谱）、ShenShaPanel/GongweiPanel（神煞宫位）、DailyFortuneCard（每日运势）、LifeKlineChart（人生 K 线）、ChatPanel（LLM 对话）

**叙述器** (`bazi_pro/narrator.py`):
- 从计算结果直接生成 9 维度专业中文文本（旺衰/格局/用神/调候/五行/刑冲/性格/事业）
- 零 LLM 依赖，每句话锚定在确定性数据上
- API 响应中作为 `narration` 字段返回

## CLI 入口

`pyproject.toml` 定义了以下 CLI 命令（`pip install -e .` 后可用）：

| 命令 | 入口 | 说明 |
|------|------|------|
| `bazi-retrieve` | `bazi_pro.retrieve_classical:main` | 古籍检索（BM25 + jieba） |
| `bazi-report` | `bazi_pro.generate_report:main` | 报告生成（HTML/MD/PDF/仪表盘） |
| `bazi-doctor` | `bazi_pro.doctor:main` | 环境诊断（15 项检查） |
| `bazi-evidence` | `bazi_pro.evidence:main` | 证据链 JSON 生成 |
| `bazi-trace` | `bazi_pro.trace:main` | 分析 trace 生成 |
| `bazi-server` | `server.app:main` | FastAPI 后端启动 |
| `bazi-tui` | `bazi_pro.tui.app:main` | 终端 TUI 界面 |
| `bazi-hybrid` | `bazi_pro.hybrid_search:main` | 混合检索（BM25 + 向量） |

## Key modules

### 核心计算 (`bazi_pro/core/`)

| 模块 | 职责 |
|------|------|
| `constants.py` | 天干地支映射、十神推导 |
| `patterns.py` | 六层格局筛查 + 破格检测（专旺/化气/从格/建禄/羊刃/正格 + 建禄羊刃月令优先拦截） |
| `yongshen.py` | 用神/喜神/忌神推导 |
| `strength.py` | 旺衰判定（得令/得地/得势 + 官杀修正极旺判定） |
| `relations.py` | 刑冲合害检测 + 天干合化 |
| `disease.py` | 格局之病检测（5 类） |
| `tiaohou.py` | 调候用神查表（穷通宝鉴 120 条） |
| `elements.py` | 五行力量计算（含月支本气 1.5 倍加成） |
| `branches.py` | 地支藏干、六合/六冲/三合/三刑映射 |
| `ten_gods.py` | 十神关系推导工具 |
| `health.py` | 健康分析（五行-脏腑对应、体质寒热、健康危机指标） |
| `wealth.py` | 财运分析（食伤生财/财官双美/比劫争财/财多身弱/枭神夺食） |
| `marriage.py` | 感情婚姻分析（配偶星/配偶宫/婚姻风险指标） |
| `family.py` | 六亲分析（父母/兄弟/子女宫位与星曜） |

### 流派分析 (`bazi_pro/core/schools/`)

| 模块 | 职责 |
|------|------|
| `base.py` | SchoolAnalyzer 抽象基类 |
| `__init__.py` | SCHOOL_REGISTRY + school_analyze() + register_school() |
| `ziping.py` | 传统子平法（格局用神 + 破格感知用神调整 + 大运吉凶） |
| `mangpai.py` | 盲派（宾主/6种做功/体用/功力/应期/贼神捕神/五党成势/墓用复合） |
| `xinpai.py` | 新派（百神论/空亡论(含出空)/反断论(同宗对)/格局分类(扶抑从强从弱)） |

### 叙述与报告

| 模块 | 职责 |
|------|------|
| `bazi_pro/narrator.py` | 确定性叙述器（9 维度中文文本生成） |
| `bazi_pro/view_model.py` | DashboardVM 数据契约 |
| `bazi_pro/ui/consumer_report.py` | 消费级报告（六维叙事 + 术语解释） |
| `bazi_pro/generate_report.py` | 报告生成 CLI（3 种模式） |

### Web 服务 (`server/`)

| 模块 | 职责 |
|------|------|
| `app.py` | FastAPI 应用（REST + SSE + WebSocket + 流派选择 + 对比端点） |
| `db.py` | SQLite 存储层（aiosqlite） |
| `analysis.py` | 异步分析编排（调用 core + schools + nayin + gongwei + shensha） |
| `nayin.py` | 60甲子纳音常量表 |
| `gongwei.py` | 宫位计算（胎元/命宫/身宫） |
| `shensha.py` | 神煞查表（天乙贵人/文昌/驿马/桃花/华盖等 25+ 种） |
| `llm.py` | LLM 服务封装（OpenAI 兼容 API） |
| `true_solar_time.py` | 真太阳时修正（Jean Meeus 时差方程 + 38 城市经纬度） |
| `daily_fortune.py` | 每日/每月运势（6 维度评分） |
| `kline_ohlc.py` | 百年人生 K 线 OHLC 模型（4 维度） |
| `personality.py` | 性格分析（10 题 + 分叉路径） |
| `reverse_lookup.py` | 日柱反查 |
| `cross_validate.py` | 三流派交叉验证 |
| `interpretation_modes.py` | 解读模式（通俗/专业/技术） |
| `dayun_score.py` | 大运流年评分 |
| `chart_quality.py` | 命局层次评分（格局清纯度/用神状态/冲突/五行流通/大运配合，100 分制） |

## Critical constraints

1. **No LLM logic in `bazi_pro/core/`** — 纯确定性计算。
2. **No fabricated citations** — 每条古籍引用必须可追溯到 `retrieve_classical.py` 输出。
3. **UI data contract** — 所有 UI 组件只接受 `DashboardVM` dataclass，不做正则提取。
4. **Golden case count can never decrease** — 当前 120 个 golden case JSON 文件（`tests/golden_cases/`）。
5. **推导 vs 推算** — 确定性映射（干→五行、干→十神）是推导（允许）；脆弱数学链是推算（禁止）。
6. **Linear execution** — SKILL.md 10 步流程顺序执行，不回填。
7. **`server/analysis.py` 只追加，不重写** — 可添加新字段和 import，不改变现有函数签名和返回结构。
8. **Narrator 零幻觉** — `narrator.py` 每句话必须可追溯到计算数据，不允许模糊表述。
9. **SchoolAnalyzer 注册** — 新流派必须继承 `SchoolAnalyzer` 基类，调用 `register_school()` 注册，并在 `schools/__init__.py` 的 `_ensure_schools_loaded()` 中添加 lazy import。
10. **破格检测必须有古籍依据** — 每个破格类型必须引用子平真诠/渊海子平/滴天髓/神峰通考原文。
11. **盲派/新派方法论必须有典籍依据** — 盲派核心概念（宾主/体用/做功/贼神捕神/势）须对照段建业《盲派初级命理学》《命理珍宝瑰宝50期》；新派核心概念（百神/空亡/反断/格局分类）须对照李涵辰《八字预测真踪》。
12. **每个新规则必须有测试** — 向 `bazi_pro/core/` 添加新函数时，必须在 `tests/test_core.py` 或 `tests/test_full_analysis.py` 中添加对应测试。
13. **公开 API 变更需兼容测试** — 修改 `AnalysisEngine.analyze()` 或 `full_analysis()` 返回的 key 时，需在 `TestAnalysisEngineReturnContract` 中添加测试并更新 `EXPECTED_TOP_LEVEL_KEYS`。
14. **脚本包装器必须传播退出码** — 所有 `scripts/*.py` 包装器必须使用 `sys.exit(main())`，不能裸调 `main()`。
15. **Doctor 必须在关键问题时失败** — `bazi_pro/doctor.py` 发现 `FAIL` 状态时必须返回退出码 1。
16. **极端标记必须先于通用标记检查** — `judge_wangshuai()` 中"极旺"/"极弱"必须在"身旺"/"身弱"之前检查，防止被遮蔽。
17. **检索错误必须可见** — `AnalysisEngine.retrieve()` 不得静默吞异常，错误必须出现在 `result["retrieval"]["warnings"]` 中。

## 变更后验证命令

每次修改后执行完整验证链（与 CI 一致）：

```bash
# Lint
ruff check server/ bazi_pro/ tests/

# 编译检查（捕获语法错误）
python -m compileall bazi_pro server scripts tests -q

# 核心 + golden 测试
python -m pytest tests/test_core.py tests/test_full_analysis.py -v
python tests/run_golden.py

# 环境诊断（两条路径均须通过）
python scripts/doctor.py
python -m bazi_pro.doctor
```

所有命令必须以退出码 0 完成。

## 审计脚本

```bash
python scripts/audit_all.py          # 一键运行全部 4 项审计
python scripts/audit_data_tables.py  # 数据表一致性审计
python scripts/audit_logic_chain.py  # 逻辑链审计
python scripts/audit_golden_cases.py # Golden case 审计
python scripts/audit_skill_consistency.py  # SKILL.md 一致性审计
```

## 古籍对齐规则 (v5.1)

### 专旺格
- 必须有地支方局/三合局（`_check_formation()`），无则降级为从强格
- 必须月令当令（`_check_month_season()`）
- **建禄/羊刃月令不入专旺格** — 月令为建禄/羊刃时，专旺格检测被跳过，走建禄/羊刃格路径（`not is_jianlu_yangren_month`）
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
- **建禄/羊刃月令不从强** — 月令为建禄/羊刃时，从强格检测被跳过（`not is_jianlu_yangren_month`）

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

### 导入与废弃

- **`core_rules.py` 是废弃 shim** — 内部代码应从 `bazi_pro.core` 导入。
- **双源兼容取值** — `full_analysis()` 返回 `result['day_master']`/`result['pillars']`（顶层），`run_analysis()` 返回 `result['validation']['day_master']`/`result['shishen']['pillars']`。取值时需双源回退：`result.get("day_master", "") or result.get("validation", {}).get("day_master", "")`。

### 格局与用神

- **建禄月劫格** — 层1/2/3 都走 `_build_jianlu_yuejie()`，输出 `建禄格，透X` 而非 `比肩格`。
- **建禄月劫格用神** — 由格局名中"透X"决定，不是盲取 PATTERN_YONGSHEN 表。
- **建禄/羊刃月令优先于专旺格/从强格** — 月令为建禄/羊刃时，建禄格/羊刃格优先于专旺格和从强格。`_screen_layer0` 中排除 `is_jianlu_yangren_month`，对齐《子平真诠》"用神专寻月令"原则。
- **从格用神方向** — 从强/专旺→印星，从财→财星，从官杀→官杀，从儿→食伤。忌神是逆势五行。
- **金水伤官除外** — 伤官格破格检测中，庚/辛日主（金日主）的伤官见官不标记破格。
- **破格检测函数签名** — `_screen_layer1/2/3` 和 `_build_jianlu_yuejie` 需要传入 `bazi_parts` 参数。
- **SHISHEN_WUXING_REL 无 '印比'** — 印星和比劫需单独映射，从强格/专旺格用神拆分为 `['印星', '比劫']`。
- **从格检测 gans 必须排除日主** — `_screen_layer_ccong*` 中调用 `_count_shishen_categories()` 时，传入的天干列表必须排除日主自身（`gans_no_dm = [g for g in gans if g != day_master]`），否则 `derive_shishen(day_master, day_master)` 返回"比肩"，导致 `bijie_free` 恒为 False，从财/从官杀/从儿/从势格永远无法命中。

### 旺衰与五行

- **`percent` vs `percent_adjusted`** — `calc_element_forces()` 返回两者。格局筛查用 `percent`（原始），化气格用 `percent_adjusted`（合化修正）。
- **旺衰极旺判定官杀修正** — `judge_wangshuai()` 中印比≥75%时，若官杀力量≥15%则不强制判极旺（"官印双全"格），对齐《渊海子平》。
- **elements.py 月支加成** — 月支本气1.5倍加成使用 `zhi == month_zhi` 参数判断，非硬编码索引 `i==1`。

### 查表映射

- **_GAN_HE_PARTNER 映射** — 天干合查表使用显式映射表（非 frozenset），避免查找失败。
- **_ZHI_CHONG_MAP 映射** — 地支冲查表使用显式映射表（非 frozenset set），ziping.py 大运吉凶用此表。
- **神煞查表统一用年支** — 驿马/桃花/华盖/将星/劫煞/绞煞/亡神/红鸾/天喜均使用 `year_zhi`（年支），对齐《三命通会》。

### 流派特定

- **天干合用神检测** — `ziping.py` 大运吉凶中，天干合用神不限制大运天干本身必须是喜用五行，忌神天干合去用神天干同样应标记。
- **盲派化用五行方向** — `mangpai.py` 化用检测中 `(cg_wx, gan_wx) in SHENG_PAIRS` 表示藏干生天干（体泄秀为用），非 `(gan_wx, cg_wx)`。
- **Schools lazy loading** — `schools/__init__.py` 使用 `_ensure_schools_loaded()` 延迟导入，避免循环依赖。import 语句用 `import bazi_pro.core.schools.xxx` 风格（非 `from ... import`），加 `# noqa: F401`。
- **register_school 位置** — 在各流派模块底部调用 `register_school()`，import 在顶部（ziping.py 需 `# noqa: E402`）。

### Server 与前端

- **Server 模块可选** — `server/` 依赖 fastapi/pydantic，不装也不影响核心功能，相关测试自动跳过。
- **SSE 事件缓冲** — `/api/v2/analysis/{id}/stream` 缓冲已发送事件，迟连接客户端可回放。
- **紫微斗数时辰** — `analysis.py` 从阳历字段提取出生小时（`solar.split()[1].split(':')[0]`），默认午时(12)。不使用 `mcp_json.get('时辰')`，因为 `BirthAnalyzeRequest` 无此字段。
- **前端包管理** — 使用 `pnpm`（非 npm/yarn），lock 文件为 `pnpm-lock.yaml`。
- **前端共享常量** — `frontend/src/lib/constants.ts` 导出 `WUXING_COLORS`/`WUXING_BG`/`WUXING_GRADIENT_BG`/`WUXING_BAR_GRADIENT`/`GAN_WUXING`/`ZHI_WUXING`/`RELATION_COLORS`/`SCHOOL_OPTIONS`/`SCHOOL_OPTIONS_WITH_ALL`。组件不应本地重复定义这些映射。
- **CSS 变量与 JS** — `WUXING_COLORS` 值是 `var(--wx-wood)` 形式，不能在 JS 模板字符串中拼接 hex alpha（如 `${color}40`）。需要 rgba 值时用 `WUXING_GLOW`（已移除，改用 CSS 变量）。
- **Tailwind CSS v4** — 使用 `@tailwindcss/postcss` 插件，非 v3 的 `tailwind.config.js` 模式。
- **React 19 + echarts-for-react 类型不兼容** — echarts-for-react 的类型定义与 React 19 严格类型冲突，使用 ECharts 的文件（RelationGraph、LifeKlineChart、ShishenEnergyChart）需要 `// @ts-nocheck`。
- **全局 Navbar 布局** — `layout.tsx` 包含固定顶部 Navbar（h-14），内容区已有 `pt-14` 偏移，新页面无需额外处理。

### 平台兼容

- **Windows 兼容** — 子进程测试使用 `sys.executable`（非 `python3`），文件读写指定 `encoding="utf-8"`。

## Plugin system

`plugins/{name}/` 含 `plugin.json` + `main.py`，实现 `BaziPlugin` ABC（hooks: `on_retrieve`, `on_evidence`, `on_render`）。插件只能装饰输出，不能修改核心数据。

## Version update checklist

更新版本时同步修改：`bazi_pro/__init__.py`（唯一源）、`pyproject.toml`、`SKILL.md` frontmatter、`README.md` badge、`CODE_WIKI.md`（大版本时）。
