# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project role

`bazi-pro` v5.0 is an AI Agent skill and Python SDK for interpreting Chinese Bazi / 八字 charts. It does **not** calculate the chart — Bazi MCP or another deterministic calculator produces the chart JSON. This repository handles interpretation, classical-text retrieval (BM25 + Hybrid Search), interactive visualization (SVG charts, timelines, DAG graphs), report generation (HTML/MD/PDF), a FastAPI web server, plugin system, and TUI.

## Key files

| File | Role |
|------|------|
| `SKILL.md` | Runtime contract for the LLM Agent — 10-step execution flow, output spec, ethics |
| `ROADMAP.md` | v4.5→v5.0 upgrade roadmap (all phases completed) |
| `CODE_WIKI.md` | Full architecture doc: modules, classes, data flow, dependencies |
| `bazi_pro/__init__.py` | `__version__` (single source) + `AnalysisEngine` SDK class |
| `bazi_pro/retrieve_classical.py` | BM25 + jieba retriever over 2964 classical entries; pickle cache |
| `bazi_pro/hybrid_search.py` | BM25 + vector (FAISS) + authority weights fusion search; CLI entry |
| `bazi_pro/generate_report.py` | Report generator: Markdown/HTML/PDF with Chinese aesthetics |
| `bazi_pro/dashboard.py` | Legacy dashboard v3.0 (SVG radar, score ring, timeline) |
| `bazi_pro/evidence.py` | Evidence chain: structured claim + confidence + basis JSON |
| `bazi_pro/trace.py` | `TraceBuilder` + schema validator for analysis trace |
| `bazi_pro/view_model.py` | Shared data layer: `DashboardVM` / `PillarVM` / `VerdictVM` etc. |
| `bazi_pro/doctor.py` | Environment diagnostic: 9 checks (Python, jieba, corpus, cache, hybrid...) |
| `bazi_pro/archive.py` | SQLite archive store for historical analyses |
| `bazi_pro/calibration.py` | User feedback tracker + evidence weight adjustment |
| `bazi_pro/compare_engine.py` | Dual-chart comparison engine (pillars, wuxing, compatibility) |
| `bazi_pro/liunian_sandbox.py` | Year-by-year luck sandbox (2020-2040 slider) |
| `bazi_pro/plugin_api.py` | `BaziPlugin` ABC (on_retrieve / on_evidence / on_render hooks) |
| `bazi_pro/ui/__init__.py` | Unified UI entry: `render_dashboard()` / `render_report()` / `render_replay()` |
| `bazi_pro/ui/pillar_chart.py` | Dynamic SVG bazi chart — calligraphy fonts, particle animations, pulse ring |
| `bazi_pro/ui/timeline_river.py` | Destiny river timeline — SVG curve, peaks/valleys, keyboard nav |
| `bazi_pro/ui/reasoning_graph.py` | Reasoning DAG — node-edge graph, confidence heatmap, zoom/pan |
| `bazi_pro/ui/verdict_seal.py` | Verdict seal SVG — stamp animation, ink spread, rotating border, PNG export |
| `bazi_pro/ui/classics_viewer.py` | Dual-column classics viewer — vertical original + modern interpretation |
| `bazi_pro/ui/compare_view.py` | Side-by-side chart comparison HTML |
| `bazi_pro/ui/sandbox_ui.py` | Year slider UI for liunian sandbox |
| `bazi_pro/ui/report.py` | Consultation report renderer (cover → executive summary → verdict → risk) |
| `bazi_pro/ui/replay.py` | Verdict replay renderer (3-column: stages, detail, claims/counter) |
| `bazi_pro/ui/report_composer.py` | Markdown → structured `ReportDocument` (content vs appendix) |
| `bazi_pro/ui/text_cleaner.py` | Output text cleaning (markdown residue, bracket closure, pattern mapping) |
| `bazi_pro/tui/app.py` | Interactive TUI (rich): colored tables, progress bars, Tab-completion REPL |
| `server/app.py` | FastAPI app: REST API + WebSocket + Jinja2 templates |
| `server/ws.py` | WebSocket connection manager — per-step progress push |
| `server/cache.py` | Redis (optional) or LRU dict cache |
| `server/analysis.py` | Async analysis orchestration wrapping sync `bazi_pro` modules |
| `plugins/loader.py` | Plugin discovery: directory scan + entry_points |
| `references/classical_corpus.md` | 2964 classical entries, 6 texts, `[ID] @topic @source ## content` format |
| `references/ETHICS.md` | Ethical wording rules, prohibited language, special-situation templates |
| `references/tiaohou.md` | 调候用神 reference (10 stems × 12 months) |

## Non-negotiable design principles

1. **算析分离**: Chart calculation is external (MCP / deterministic code). This repo only interprets.
2. **No fabricated citations**: Every classical quote must come from `retrieve_classical.py` output or a reference file.
3. **Calculation boundaries**: Simple counting (tallying stems/branches) is OK for the LLM. Fragile math (multiplication chains, hidden-stem ratios) must come from MCP or scripts. Missing MCP data gets labeled "⚠️ MCP 未提供".
4. **Linear execution flow**: Step 0→1→2→3→4→5→6→7→8→9→[optional]10. No tentative→backfill loops.
5. **Ethics first**: Health, finance, marriage, fertility, death topics use cultural-reference phrasing only — never deterministic prediction. See `references/ETHICS.md`.
6. **UI data contract**: All UI components accept `DashboardVM` dataclass only. No regex extraction inside UI code (legacy `build_vm_from_analysis_text()` is deprecated).

## Architecture

```
                          Bazi MCP JSON
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  Evidence Retrieval Layer                                    │
│  retrieve_classical.py (BM25 + jieba + pickle cache)         │
│  hybrid_search.py    (BM25 + vector/FAISS + authority)       │
│  → classical_corpus.md (2964 entries, 6 classics)            │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  Analysis Engine (SKILL.md 10-step flow)                     │
│  Step 0: Classical retrieval (single/dual-channel)           │
│  Step 1-2: Validation + Day-master strength                  │
│  Step 3-5: Pattern (6-layer) + Useful God (4-layer) + Wuxing │
│  Step 6-9: Dayun + Relations + Dimensions + Calibration      │
│  Step 10 (optional): Generate report                         │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  Evidence + Trace Pipeline                                   │
│  evidence.py → structured evidence JSON (claim + confidence) │
│  trace.py    → TraceBuilder → analysis_trace.json            │
│  view_model.py → DashboardVM (shared data layer)             │
└──────────────────────────────────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
     Dashboard HTML       Report HTML          Replay HTML
     (pillar_chart,       (cover, verdict,     (3-column:
      timeline_river,      risk, appendix)      stages, detail,
      reasoning_graph)                          claims)
```

**Two-turn protocol** (详细版 only): Turn 1 outputs Step 1+2 + raw element preview + 3 verification questions, then stops. Turn 2 continues after user feedback.

**ViewModel data flow**: `analysis_trace.json` → `build_vm_from_trace()` → `DashboardVM` → all UI renderers. The legacy path `build_vm_from_analysis_text()` (regex from Markdown) is deprecated since v4.7.

## Setup and commands

Requires Python 3.10+ with `jieba`:

```bash
pip install -e .                        # Install as package with all console scripts
pip install -e ".[hybrid,report,tui]"   # With optional dependency groups
```

### Retrieval

```bash
# BM25 search (JSON output for Agent consumption)
python scripts/retrieve_classical.py "伤官见官 甲木 身弱 财星通关" -k 5 --json

# Corpus statistics
python scripts/retrieve_classical.py --stats

# Hybrid search (requires sentence-transformers + faiss-cpu + numpy)
python -m bazi_pro.hybrid_search "从强 假从 顺势 印比成势" -k 5 --json
python -m bazi_pro.hybrid_search --build-index    # Pre-build FAISS index
python -m bazi_pro.hybrid_search --status         # Check hybrid availability
```

### Report generation

```bash
# Markdown report (default, zero-loss)
python scripts/generate_report.py --input analysis.md --output report.md

# HTML report with Chinese aesthetics
python scripts/generate_report.py --input analysis.md --format html --output report.html

# Interactive dashboard (SVG charts + timeline + DAG)
python scripts/generate_report.py --input analysis.md --theme dashboard --output dashboard.html

# PDF (needs weasyprint or pdfkit)
python scripts/generate_report.py --input analysis.md --output report.md --pdf
```

### Environment & diagnostics

```bash
python scripts/doctor.py                  # 9-check diagnostic
python -m bazi_pro.trace demo > trace.json
python -m bazi_pro.trace validate trace.json
```

### Smoke tests (golden queries)

```bash
python scripts/retrieve_classical.py "从强 假从 顺势 印比成势" -k 5 --json
python scripts/retrieve_classical.py "伤官见官 财星通关" -k 5 --json
python scripts/retrieve_classical.py "杀印相生 七杀 印绶" -k 5 --json
python scripts/retrieve_classical.py "枭神夺食 食神 偏印" -k 5 --json
python scripts/retrieve_classical.py "寒木向阳 调候 丙火" -k 5 --json
python scripts/retrieve_classical.py "火炎土燥 调候 壬癸" -k 5 --json
```

### Test suite

```bash
python tests/run_golden.py                # 4 golden-case boundary regression tests
python -m pytest tests/test_html_quality.py -v  # UI rendering quality checks
python -m pytest tests/test_retrieve.py -v      # Core command smoke tests
python -m pytest tests/test_trace.py -v         # Trace schema validation
```

### Web server

```bash
pip install -e ".[server]"
python server/app.py                      # Start on http://localhost:8800
# OpenAPI docs at /docs, ReDoc at /redoc
# WebSocket progress at /ws/{run_id}
```

### Interactive TUI

```bash
pip install -e ".[tui]"
bazi-tui                                 # Rich-powered interactive terminal
# Or: python -m bazi_pro.tui.app
```

### SDK usage

```python
from bazi_pro import AnalysisEngine

engine = AnalysisEngine()
results = engine.retrieve("伤官见官 财星通关", k=5)
analysis = engine.analyze({"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "性别": "女"})
report = engine.generate_report(analysis, format='html')
```

## Editing `SKILL.md`

`SKILL.md` is the core runtime contract — keep it concise, unambiguous, executable.

- Keep frontmatter `name` and trigger intent intact
- Update version string in SKILL.md + README.md + `__init__.py` together
- Maintain strict linear flow (the only exception is two-turn protocol for 详细版)
- Prefer tables and schemas over long prose
- Move large lookup tables into `references/`
- Every new required output field must have a downgrade behavior for missing MCP data
- Update all cross-references when renumbering steps
- Avoid: adding new mandatory rules without removing outdated ones, hand-computation formulas, hard-coded absolute paths, deterministic/fear-based language

## Editing `retrieve_classical.py`

The retriever is intentionally simple: parse corpus → jieba tokenize → BM25 → top-K.

- Corpus path resolution: (1) `--corpus` flag, (2) `SKILL_DIR` env var, (3) relative to script, (4) `~/.hermes/skills/bazi-pro/`
- Prefer additive improvements: `pyproject.toml` deps, golden-query tests, synonym expansion
- If `jieba` is missing, fail with clear message and exit code 1 — never silently degrade tokenization

## Corpus format

`references/classical_corpus.md` is line-oriented: `[ID] @topic @source ## content`

## Plugin development

Plugins live in `plugins/{name}/` with `plugin.json` + `main.py`. They implement `BaziPlugin` from `bazi_pro.plugin_api`:

```python
class BaziPlugin(ABC):
    @abstractmethod
    def on_retrieve(self, query: str, results: list[dict]) -> list[dict]: ...
    @abstractmethod
    def on_evidence(self, evidence: dict) -> dict: ...
    @abstractmethod
    def on_render(self, html: str, vm: DashboardVM) -> str: ...
```

Plugins can only read, filter, enhance, and decorate output — never modify core data. Example plugins are in `plugins/examples/` (english, tarot, fengshui).

## UI component development

- Pure CSS/SVG animation only (no new dependencies for visual components)
- Calligraphy fonts via Google Fonts CDN: `"Zhi Mang Xing", "Ma Shan Zheng", STKaiti, KaiTi, serif`
- Every component must support `data-theme="dark|light"` and provide SVG/PNG export
- Accessibility: SVG `<title>` + `<desc>`; interactive elements must have `aria-label`

## Version update checklist

When bumping the version, update ALL of these:

- [ ] `bazi_pro/__init__.py` — `__version__` (single source of truth)
- [ ] `pyproject.toml` — `version` field
- [ ] `SKILL.md` — frontmatter `description` and version history section
- [ ] `README.md` — title badge and version history table
- [ ] `CODE_WIKI.md` — version table (if major)
- [ ] `ROADMAP.md` — mark completed tasks (if applicable)
- [ ] CI (`ci.yml`) — version consistency check

## Pull request checklist

- [ ] Version strings match across `__init__.py`, `pyproject.toml`, `README.md`, `SKILL.md`
- [ ] Step order consistent everywhere (flow diagram, two-turn protocol, README, cross-references)
- [ ] No absolute paths (`/home/...`) present
- [ ] At least 3 golden-query smoke tests pass
- [ ] `scripts/generate_report.py` smoke test passes
- [ ] New dependencies declared in `pyproject.toml`
- [ ] Ethics language remains non-deterministic and non-coercive
- [ ] No classical quotation is fabricated — every citation traces to `retrieve_classical.py` output
- [ ] Every required MCP output field has an explicit downgrade behavior
- [ ] New UI components support both dark/light themes
- [ ] SVG graphics include `<title>` / `<desc>` accessibility tags
- [ ] Backward compatibility: existing CLI interfaces still work
