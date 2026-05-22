# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project role

`bazi-pro` is an AI Agent skill (v3.3) for interpreting Chinese Bazi / 八字 charts. It does **not** calculate the chart — Bazi MCP or another deterministic calculator produces the chart JSON. This repository handles interpretation, classical-text retrieval, output structure, ethics, and downgrade behavior when MCP data is missing.

## Key files

| File | Role |
|------|------|
| `SKILL.md` | Runtime contract for the Agent — execution flow, step schemas, output spec |
| `CLAUDE.md` | This file — Claude Code working guide + COOL upgrade dev rules |
| `ROADMAP.md` | v4.5→v5.0 升级路线图，含 Phase A/B/C/D 全部任务清单 |
| `CODE_WIKI.md` | 完整架构文档：模块、类函数、数据流、依赖、运行方式 |
| `bazi_pro/retrieve_classical.py` | BM25 + jieba retriever over 2964 classical entries |
| `bazi_pro/generate_report.py` | Report generator: analysis text → HTML/MD/PDF |
| `bazi_pro/dashboard.py` | Interactive dashboard: SVG radar, score ring, dayun timeline |
| `bazi_pro/evidence.py` | Evidence chain: structured claim+confidence+basis JSON |
| `bazi_pro/trace.py` | Analysis trace builder + schema validator |
| `bazi_pro/view_model.py` | Shared data layer: DashboardVM / PillarVM / VerdictVM etc. |
| `bazi_pro/hybrid_search.py` | Hybrid search skeleton: BM25 + vector + authority weights |
| `bazi_pro/ui/report.py` | Consultation report renderer |
| `bazi_pro/ui/replay.py` | Verdict replay renderer (3-column) |
| `bazi_pro/ui/verdict_seal.py` | Verdict seal SVG (朱砂印章) |
| `bazi_pro/ui/text_cleaner.py` | Output text cleaning layer |
| `references/classical_corpus.md` | Classical corpus (6 texts, line-oriented `[ID] @topic @source ## content`) |
| `references/tiaohou.md` | 调候用神 reference table (10 stems × 12 months, based on 穷通宝鉴) |
| `references/ETHICS.md` | Ethical wording rules, prohibited language, special-situation templates |
| `references/migration-checklist.md` | Cross-machine migration checklist (paths, deps, smoke tests) |
| `references/bazi-mcp-direct-call.md` | Direct Bazi MCP call guide (bypass when MCP tool unavailable) |
| `references/case-study-false-positive-yangren.md` | Case study: 羊刃 false-positive pattern trap |

## Non-negotiable design principles

1. **算析分离**: Chart calculation lives in MCP / deterministic code. The skill only interprets.
2. **No fabricated citations**: Every classical quote must come from `retrieve_classical.py` output or an explicit reference file.
3. **Calculation boundaries**: Simple counting (tallying stems/branches, rough percentages for §0.0 gating) is OK for the LLM. Fragile math (multiplication chains, hidden-stem ratios, combination corrections) must come from MCP or scripts. Missing MCP data gets labeled "⚠️ MCP 未提供", never hand-computed.
4. **One canonical execution order**: Step 0 → 1 → 2 → 3(格局) → 4(喜用) → 5(五行力量) → 6(大运) → 7(刑冲合害) → 8(分维度) → 9(历史校准) → [可选] Step 10(生成报告). No "tentative → backfill" loops. If you edit the flow, update `SKILL.md`, `README.md`, and all cross-references.
5. **Ethics first**: Health, finance, marriage, fertility, death, disaster, and legal topics must use cultural-reference phrasing only — never deterministic prediction or professional advice. See `references/ETHICS.md`.

## Architecture: v3.4 linear execution flow

```
Phase 0 (data prep)       Phase 1 (basics)     Phase 2 (core)         Phase 3 (analysis)
┌─────────────────┐       ┌──────────┐        ┌──────────────────┐    ┌─────────────────┐
│ Step 0: 古籍检索 │  →   │ Step 1   │   →    │ Step 3: 格局判定  │ →  │ Step 6: 大运流年 │
│  0.0 五行快速预检 │       │ 数据校验  │        │  层0: 特殊格局    │    │ Step 7: 刑冲合害 │
│  0.1 单通道检索   │       │ Step 2   │        │  层1-5: 月令/暗格 │    │ Step 8: 分维度   │
│  0.2 双通道检索   │       │ 旺衰判定  │        │  层6: 量化评分    │    │ Step 9: 历史校准 │
└─────────────────┘       └──────────┘        │ Step 4: 喜用判定  │    └────────┬────────┘
                                               │  4.1-4.5 四层裁决  │             │ (可选)
                                               │ Step 5: 五行力量  │             ▼
                                               └──────────────────┘    ┌──────────────────────┐
                                                                       │ Step 10: 生成报告     │
                                                                       │  分析文本 → HTML/MD   │
                                                                       │  (含封面、目录、样式)  │
                                                                       └──────────────────────┘
```
**Two-turn protocol** (详细版 only): Turn 1 outputs Step 1 + Step 2 + raw MCP element preview + 3 historical verification questions, then **stops**. Turn 2 continues with Step 3 → 4 → 5 (with corrections) → 6 → 7 → 8 after user feedback.

**Path convention**: All script paths use `${SKILL_DIR:-.}/scripts/retrieve_classical.py`. `SKILL_DIR` is injected by the Hermes runtime. Never hard-code absolute paths like `/home/administrator/...`.

## Setup and commands

Requires Python 3.10+ with `jieba`:

```bash
python3 -m pip install jieba
```

Run corpus stats:

```bash
python3 scripts/retrieve_classical.py --stats
```

Run a retrieval (text output):

```bash
python3 scripts/retrieve_classical.py "从象 从强 假从 壬水 金水 印比成势" -k 5
```

Run a retrieval (JSON, for Agent consumption):

```bash
python3 scripts/retrieve_classical.py "伤官见官 甲木 身弱 财星通关" -k 5 --json
```

Run from any directory by specifying the corpus explicitly:

```bash
python3 /path/to/bazi-pro/scripts/retrieve_classical.py \
  "伤官见官 甲木 身弱 财星通关" \
  -k 5 --json \
  --corpus /path/to/bazi-pro/references/classical_corpus.md
```

Generate a report from analysis output:

```bash
python3 scripts/generate_report.py --input analysis.md --output report.html
python3 scripts/generate_report.py --input analysis.md --output report.html --pdf
cat analysis.md | python3 scripts/generate_report.py > report.html
```

There is no formal test suite. Before committing retrieval changes, run `--stats` and these golden-query smoke tests:

```bash
python3 scripts/retrieve_classical.py "从强 假从 顺势 印比成势" -k 5 --json
python3 scripts/retrieve_classical.py "伤官见官 财星通关" -k 5 --json
python3 scripts/retrieve_classical.py "杀印相生 七杀 印绶" -k 5 --json
python3 scripts/retrieve_classical.py "枭神夺食 食神 偏印" -k 5 --json
python3 scripts/retrieve_classical.py "寒木向阳 调候 丙火" -k 5 --json
python3 scripts/retrieve_classical.py "火炎土燥 调候 壬癸" -k 5 --json
```

## Editing `SKILL.md`

`SKILL.md` is the core runtime contract — keep it concise, unambiguous, executable.

When editing:

1. Keep frontmatter `name` and trigger intent intact unless deliberately changing the skill identity.
2. Update the version string and the version-history section in `README.md` together.
3. Maintain the strict linear flow. The only exception is the two-turn protocol for 详细版, which is explicitly documented.
4. Prefer tables and schemas over long prose rules.
5. Move large lookup tables or theoretical notes into `references/` instead of expanding the main prompt.
6. Any new required output field must have a downgrade behavior for missing MCP data.
7. Any new citation requirement must specify how the citation is retrieved and what to do when retrieval returns weak/no results.
8. Update all cross-references when renumbering steps or subsections.

Avoid:

- Adding new "必须/强制/不得" rules without removing outdated ones.
- Introducing hand-computation formulas into the prompt.
- Hard-coding absolute paths — use `${SKILL_DIR:-.}`.
- Mystical determinism, fear-based language, or absolute claims about illness, divorce, death, bankruptcy, or childbirth.

## Editing `scripts/retrieve_classical.py`

The retriever is intentionally simple: parse corpus → jieba tokenize → BM25 → top-K. The CLI contract is:

```bash
python3 scripts/retrieve_classical.py "query" -k 5 --json
python3 scripts/retrieve_classical.py --stats
python3 scripts/retrieve_classical.py "query" --corpus references/classical_corpus.md
```

Corpus path resolution order: (1) `--corpus` flag, (2) `SKILL_DIR` env var, (3) relative to script, (4) `~/.hermes/skills/bazi-pro/`.

Prefer additive, testable improvements: `pyproject.toml` for deps, golden-query tests under `tests/`, synonym expansion for term variants, score-threshold warnings, highlighted matched terms in JSON output.

Do **not** silently fall back to poor tokenization. If `jieba` is missing, fail with a clear message and exit code 1.

## Corpus format

`references/classical_corpus.md` is line-oriented. Valid entries:

```text
[ID] @topic @source ## content
```

Example: `[DTM_00082] @十神 @滴天髓 ## 十四、假从 真从之象有几人，假从亦可发其身。`

If the format changes, update `load_corpus()` in the script and README examples together.

## Pull request checklist

Before finalizing changes, verify:

- [ ] `README.md` and `SKILL.md` version strings match.
- [ ] The step order is consistent everywhere (linear flow diagram, two-turn protocol, README table, all cross-references).
- [ ] No reference file is linked but missing.
- [ ] No absolute paths (`/home/...`) are present.
- [ ] At least 3 golden-query smoke tests pass.
- [ ] `scripts/generate_report.py` smoke test passes with sample analysis text.
- [ ] Any new dependency is declared.
- [ ] Ethics language remains non-deterministic and non-coercive (see `references/ETHICS.md`).
- [ ] No classical quotation is fabricated — every citation traces to `retrieve_classical.py` output or a reference file.
- [ ] Every required MCP output field has an explicit downgrade behavior when missing.

## COOL 升级计划（v4.5 → v5.0）

完整路线图见 [ROADMAP.md](./ROADMAP.md)。本节为 Claude Code 提供升级开发的执行规范。

### 当前版本目标

| 目标版本 | 主题 | 核心变更 |
|----------|------|----------|
| **v4.5** | 视觉飞跃 | 动态 SVG 命盘、命运河流时间轴、推理 DAG、印章动画 |
| **v4.6** | 服务化 | FastAPI + WebSocket，从脚本进化为 Web 服务 |
| **v4.7** | 架构统一 | Hybrid Search 落地、ViewModel 单一数据源 |
| **v4.8** | 新功能 | 命盘对比、古籍双栏展示 |
| **v5.0** | 生态闭环 | 流年沙盒、档案系统、插件机制、SDK、TUI |

### 开发规范

#### 视觉组件开发规则

1. **纯 CSS/SVG 动画优先**：Phase A 所有视觉升级不引入新依赖。动画用 `@keyframes` / CSS transitions / SVG SMIL 实现。
2. **书法字体通过 Google Fonts CDN 加载**：不打包字体文件到仓库。fallback 链：`"Zhi Mang Xing", "Ma Shan Zheng", "STKaiti", "KaiTi", serif`。
3. **暗色/亮色主题**：所有新增 UI 组件必须支持 `data-theme="dark|light"` 切换，CSS 变量定义在 `references/design_tokens.css`。
4. **可导出性**：每个可视化组件必须提供独立的 SVG/PNG 导出能力（服务端渲染或客户端 canvas 截图）。
5. **无障碍**：SVG 图形必须有 `<title>` 和 `<desc>` 标签；交互元素必须有 `aria-label`。

#### Web 服务层规则（Phase B-1）

1. **FastAPI 项目结构**：
   ```
   server/
   ├── app.py          # FastAPI 实例 + 路由注册
   ├── ws.py           # WebSocket 连接管理
   ├── cache.py        # Redis 缓存封装
   ├── analysis.py     # 异步分析编排（调用现有 bazi_pro 模块）
   └── templates/
       ├── base.html   # Jinja2 基础模板
       └── dashboard.html
   ```
2. **WebSocket 推送格式**：每完成一个 Step 推送 `{ "step": "3", "status": "done", "summary": "..." }`。
3. **Redis 为可选依赖**：未配置 Redis 时降级为内存缓存（LRU dict）。
4. **不改动核心引擎**：`server/analysis.py` 只是异步包装现有的同步 SKILL.md 执行流。

#### ViewModel 统一化规则（Phase B-3）

1. **SKILL.md 输出扩展**：在 Step 10 之后增加隐式输出——结构化 JSON 写入 `.artifacts/result.json`，包含完整的 pillars/wuxing/pattern/dayun/evidence 数据。
2. **废弃路径标记**：`build_vm_from_analysis_text()` 标记 `@deprecated`，保留但不推荐使用。
3. **UI 组件禁止正则提取数据**：所有 UI 只接受 `DashboardVM` dataclass 作为输入。

#### 插件机制规则（Phase D-1）

1. **插件目录**：`plugins/` 下每个子目录是一个插件，含 `plugin.json`（元数据）和 `main.py`（实现）。
2. **钩子签名**：
   ```python
   class BaziPlugin(ABC):
       @abstractmethod
       def on_retrieve(self, query: str, results: list[dict]) -> list[dict]: ...
       @abstractmethod
       def on_evidence(self, evidence: dict) -> dict: ...
       @abstractmethod
       def on_render(self, html: str, vm: DashboardVM) -> str: ...
   ```
3. **插件不得修改核心数据**：只能读取、过滤、增强、装饰输出。
4. **内置插件放在 `plugins/examples/`**，不影响默认行为。

#### 新增文件命名约定

| 类型 | 命名模式 | 示例 |
|------|----------|------|
| UI 组件 | `ui/{feature}.py` | `ui/pillar_chart.py`, `ui/reasoning_graph.py` |
| 服务端 | `server/{module}.py` | `server/app.py`, `server/ws.py` |
| 功能模块 | `{feature}.py` | `liunian_sandbox.py`, `compare_engine.py` |
| 插件 | `plugins/{name}/main.py` | `plugins/english/main.py` |

#### 升级开发的 PR Checklist

标准 checklist 之外，升级相关 PR 还需验证：

- [ ] 新增 UI 组件同时支持暗色/亮色主题
- [ ] SVG 图形包含 `<title>` / `<desc>` 无障碍标签
- [ ] 新增的可视化组件可通过 `--output` 导出为独立文件
- [ ] Web 端点有对应的 OpenAPI schema 文档
- [ ] 新增功能有对应的 smoke test（`tests/test_{feature}.py`）
- [ ] 不破坏现有 CLI 的向后兼容性
- [ ] `ROADMAP.md` 中对应任务已勾选更新

## Future refactor direction

A cleaner architecture would separate the project into three layers:

1. **Calculation layer** — parse MCP JSON, normalize field names, compute root strength, five-element forces, pattern candidates, relation graph.
2. **Evidence layer** — classical retrieval, tiaohou lookup, ethics/safety constraints.
3. **Narrative layer** — SKILL.md interprets the normalized JSON and evidence, with no fragile arithmetic.

Target intermediate schema:

```json
{
  "meta": {}, "pillars": {}, "ten_gods": {}, "hidden_stems": {},
  "root_strength": {}, "element_forces": {}, "pattern_candidates": [],
  "useful_god_candidates": [], "dayun": [], "relations": [],
  "evidence": [], "warnings": []
}
```
