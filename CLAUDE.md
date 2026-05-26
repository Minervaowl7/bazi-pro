# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project identity

`bazi-pro` v5.0 — deterministic Chinese Bazi (八字) computation engine + LLM interpretation framework. The core principle is **算析分离**: `bazi_pro/core/` does all deterministic 命理 calculations (十神, 藏干, 五行力量, 旺衰, 格局, 喜用神, 刑冲合害); the LLM only interprets results, never computes them.

### Recent changes (fix/assessment-issues branch)

- **Consumer report mode** (`--mode consumer`): 面向普通用户的消费级报告，结论先行、术语解释、六维叙事扩展
- **Glossary system** (`bazi_pro/ui/glossary.py`): 70 个命理术语的 tooltip 标注 + 分类词典渲染
- **CLI `--mode` parameter**: 新增语义更清晰的 `--mode` 参数（`--theme` 保留向后兼容）
- **Technical appendix collapse**: 技术分析步骤折叠到 `<details>` 中，不丢失信息
- **Test coverage**: 24 项 consumer report 专项测试 + 17 项 dayun 提取测试 + 19 项 VM 提取质量测试
- **VM extraction fixes**: 修复 Markdown→ViewModel 的关键字段提取（pattern/decision/score/dayun/qiyun_age），consumer 报告个性化程度大幅提升
- **Core logic fixes** (prior commits): 地支三刑、天干争合检测、从儿格条件修正、忌神推导修正、关系去重

## Build and test commands

```bash
pip install -e .                              # Minimal install (core + retrieval)
pip install -e ".[all]"                       # Full install (hybrid, report, pdf, server, tui)

# Primary test suite — 98 golden-case boundary regression tests
python tests/run_golden.py

# Full audit pipeline (schema + 4 specialized audits)
python scripts/audit_all.py

# Environment diagnostic (15 checks)
python scripts/doctor.py

# Lint (ruff, configured in pyproject.toml)
ruff check server/ bazi_pro/ tests/

# Trace pipeline validation
python -m bazi_pro.trace demo > trace.json && python -m bazi_pro.trace validate trace.json

# Version consistency check (CI uses this)
python scripts/check_version_consistency.py

# Run individual pytest files (pytest is optional, not in core deps)
python -m pytest tests/test_retrieve.py -v
python -m pytest tests/test_trace.py -v

# Compile check (catches syntax errors across all modules)
python -m compileall bazi_pro server scripts tests -q
```

## Architecture (big picture)

```
Bazi MCP JSON input
       │
       ▼
┌─────────────────────────────────────────┐
│  Deterministic Core (bazi_pro/core/)    │  ← 13 modules, pure data transforms
│  full_analysis() → dict                 │     NO LLM logic here ever
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Retrieval (BM25 + optional FAISS)      │  ← 2964 classical entries, 6 texts
│  retrieve_classical.py / hybrid_search  │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Evidence + Trace Pipeline              │  ← evidence.py → trace.py → view_model.py
│  Structured JSON: claim + confidence    │
└─────────────────────────────────────────┘
       │
       ├──→ UI renderers (bazi_pro/ui/)   ← accept DashboardVM only
       ├──→ FastAPI server (server/)
       └──→ Plugin hooks (plugins/)
```

**Data flow**: `full_analysis(mcp_json)` → `TraceBuilder` → `analysis_trace.json` → `build_vm_from_trace()` → `DashboardVM` → all UI renderers.

**Two import paths to `full_analysis()`**:
- `bazi_pro.core.full_analysis` — canonical, use this
- `bazi_pro.core_rules.full_analysis` — deprecated shim, emits DeprecationWarning

**SDK entry point**: `bazi_pro.AnalysisEngine` wraps core + retrieval + report generation.

## Critical constraints

1. **No fabricated citations** — every classical quote must trace to `retrieve_classical.py` output or a reference file.
2. **推导 vs 推算** — deterministic mappings (stem→element, stem→shishen) are 推导 (allowed, mark with "⚠️ 由已知数据推导"). Fragile math (multiplication chains, combination corrections, hidden-stem ratios) is 推算 (FORBIDDEN, mark "⚠️ MCP 未提供").
3. **Linear execution** — SKILL.md 10-step flow runs 0→1→…→9→[10]. No backfill loops.
4. **Ethics** — health/finance/marriage/death topics use cultural-reference phrasing only. See `references/ETHICS.md`.
5. **UI data contract** — all UI components accept `DashboardVM` dataclass. No regex extraction in UI code.
6. **No new dependencies** without declaring in `pyproject.toml`.
7. **No LLM logic in `bazi_pro/core/`** — it's purely deterministic computation.

## Version update checklist

When bumping version, update ALL of: `bazi_pro/__init__.py` (single source), `pyproject.toml`, `SKILL.md` frontmatter, `README.md` badge, `CODE_WIKI.md` (if major).

## Key gotchas

- **Python 3.12+ importlib** — `importlib.util` and `importlib.metadata` must be explicitly imported (not auto-available as `importlib.util`). The plugin loader requires both.
- **Corpus exists in two places** — `bazi_pro/data/classical_corpus.md` (package data, CRLF on Windows) and `references/classical_corpus.md` (LF). They're content-identical. The package data copy is authoritative for installed usage.
- **`core_rules.py` is a deprecated shim** — it re-exports everything from `bazi_pro.core` with a DeprecationWarning. Internal code should import from `bazi_pro.core` directly.
- **Golden tests check terminology patterns**, not computation correctness — they verify that prohibited terms don't appear in wrong contexts and that core engine outputs match expected values for 98 boundary cases.
- **`json` module** — if you need it in a function, import at module top level. Scoped imports inside conditional branches cause `UnboundLocalError` when another branch references the same name.
- **建禄格 vs 月劫格 vs 羊刃格** — `_classify_bijie_pattern` must check `JIANLU_MAP`/`YANGREN_MAP` against month_zhi, not just benqi_ss. 阴干无羊刃（only 甲卯丙午戊午庚酉壬子）.
- **从格用神方向** — 从强/专旺格用印星(生我), 从财格用财星(我克), 从官杀格用官杀(克我), 从儿格用食伤(我生). 忌神是逆势五行, 不是扶抑格逻辑.
- **`percent` vs `percent_adjusted`** — `calc_element_forces()` returns both. Pattern screening uses `percent` (raw); 化气格 uses `percent_adjusted` (hehua-corrected). This is by design.
- **建禄月劫格用神** — 由格局名中的"透X"决定, 不是盲取 PATTERN_YONGSHEN 表第一候选. "透食神"→食伤为用, "透正官"→官杀为用.

## Agent guardrails

See `AGENTS.md` for the full list. Key rules:
- `bazi_pro/core/` modules import only from `bazi_pro.core.*` (no circular deps)
- Every new core function needs a test
- Golden case count can never decrease (currently 98)
- Script wrappers use `sys.exit(main())`
- `full_analysis()` return keys changes need `TestAnalysisEngineReturnContract` update

## Plugin system

Plugins in `plugins/{name}/` with `plugin.json` + `main.py` implementing `BaziPlugin` ABC (hooks: `on_retrieve`, `on_evidence`, `on_render`). `plugins/examples/` is excluded from auto-scan. Plugins can only decorate output, never modify core data.

## Corpus format

`[ID] @topic @source ## content` — one entry per line, 2964 total across 6 classical texts.

## Report modes

Three report rendering modes, all consuming the same `DashboardVM` data:

| Mode | CLI | Audience | Description |
|------|-----|----------|-------------|
| `report` (default) | `--mode report` | 开发者/命理师 | 传统技术报告，按分析步骤排列，含完整表格和评分 |
| `dashboard` | `--mode dashboard` | 开发者/命理师 | 交互式仪表盘，SVG 图表 + 证据链 + 推理图谱 |
| `consumer` | `--mode consumer` | 普通用户 | 消费级报告，结论先行 + 术语解释 + 六维叙事 + 技术附录折叠 |

```bash
# 生成消费级报告（面向普通用户）
python bazi_pro/generate_report.py --input analysis.md --mode consumer --format html -o report.html

# 生成传统技术报告（默认行为不变）
python bazi_pro/generate_report.py --input analysis.md --format html -o report.html

# --theme 是 --mode 的旧别名，向后兼容；--mode 优先级更高
python bazi_pro/generate_report.py --input analysis.md --theme consumer --format html -o report.html
```

Consumer 模式特性：术语 tooltip（hover 显示通俗解释）、70 词术语小词典、六维度叙事扩展（性格/事业/财运/感情/健康/近运各 300+ 字）、技术附录折叠、移动端适配、暗色模式、阅读进度条。

VM 提取能力（`build_vm_from_analysis_text()`）：
- **格局 pattern**：三策略级联提取（树形层级行 → 定性语句 → 格局行 fallback），支持 21 种已知格局名
- **旺衰 decision**：从综合判定表格提取（身旺/身弱/极旺/极弱）
- **格局评分 pattern_score**：支持 中等/中上等/中下等/上等/下等 全部标签
- **大运 dayun**：按行分割单元格解析，兼容 5/6 列表格、Markdown 粗体、emoji 标记
- **起运年龄 qiyun_age**：兼容 `**起运**：9岁` 格式

重新生成示例：`python bazi_pro/generate_report.py --input examples/sample_analysis.md --mode consumer --format html -o examples/sample_consumer_report.html`

### 已知未做事项（下一轮）

- Relations 提取（刑冲合害表格解析）→ 为感情/健康章节提供个性化素材
- 十神组合特征判断（官杀混杂、食伤生财等）→ 增强叙事条件分支
- Pattern score 展示 → 在核心发现卡中显示格局评分
- 感情/财运叙事增强 → 利用 relations + 十神组合数据

## Editing SKILL.md

SKILL.md is the LLM runtime contract. Keep it concise and executable. Don't add computation formulas. Every new required field needs a downgrade behavior for missing MCP data. Update cross-references when renumbering steps.
