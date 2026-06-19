# Agent Guardrails

Rules that any AI agent must follow when modifying this project.

## Core Rules

1. **Never add core imports from package root.** `bazi_pro/core/` modules must import only from `bazi_pro.core.*`, never from `bazi_pro` directly. This prevents circular dependencies.

2. **Every new rule needs at least one test.** If you add a new function to `bazi_pro/core/`, you must add a corresponding test in `tests/test_core.py` or `tests/test_full_analysis.py`.

3. **Every public API change needs a compatibility test or migration note.** If you change the keys returned by `AnalysisEngine.analyze()` or `full_analysis()`, add a test in `TestAnalysisEngineReturnContract` and update the `EXPECTED_TOP_LEVEL_KEYS` set.

4. **Golden cases cannot decrease.** The count in `tests/golden_cases/` must never go down. You may add or fix cases, but never remove them without replacing with equivalent coverage. Current count: 120 golden case JSON files.

5. **Script wrappers must propagate exit codes.** All `scripts/*.py` wrappers must use `sys.exit(main())`, not bare `main()`.

6. **Doctor must fail on critical issues.** `bazi_pro/doctor.py` must return exit code 1 if any check with status `FAIL` is found. New consistency checks should be added to the `consistency_checks` list.

7. **No LLM placeholders in deterministic output.** Pattern names, wangshuai verdicts, and yongshen values must never be "待LLM分析" or similar placeholders.

8. **Extreme flags must be checked before generic.** In `judge_wangshuai()`, "极旺"/"极弱" must be checked before "身旺"/"身弱" to prevent shadowing.

9. **Retrieval errors must be visible.** `AnalysisEngine.retrieve()` must not silently swallow exceptions. Errors must appear in `result["retrieval"]["warnings"]`.

10. **建禄/羊刃月令优先于专旺格/从强格.** When the month branch is 建禄 or 羊刃 of the day master, `_screen_layer0` must skip 专旺格 and 从强格 detection (`not is_jianlu_yangren_month`), letting the 建禄/羊刃格 path take precedence. This aligns with 《子平真诠》"用神专寻月令".

11. **旺衰极旺判定须考虑官杀力量.** In `judge_wangshuai()`, when 印比≥75%, if 官杀力量≥15%, do not force "极旺" verdict (官印双全 pattern). This aligns with 《渊海子平》.

12. **神煞查表统一使用年支.** 驿马/桃花/华盖/将星/劫煞/绞煞/亡神/红鸾/天喜 must all use `year_zhi` (年支), aligned with 《三命通会》.

13. **双源兼容取值.** When reading `day_master`/`pillars` from analysis results, always use dual-source fallback: `result.get("day_master", "") or result.get("validation", {}).get("day_master", "")`. `full_analysis()` puts these at top level; `run_analysis()` puts them under `validation`/`shishen`.

14. **`bazi_pro/core/` is pure deterministic.** No LLM calls, no I/O, no randomness. All computation must be reproducible.

15. **`core_rules.py` is a deprecated shim.** Internal code must import from `bazi_pro.core` directly. The shim emits `DeprecationWarning`.

16. **`server/analysis.py` is append-only.** You may add new fields and imports, but never change existing function signatures or return structures.

17. **紫微斗数核心模块 (`bazi_pro/core/ziwei/`) is pure deterministic.** No LLM calls, no I/O, no randomness. All computation must be reproducible.

18. **Function Calling 工具集 (`server/agents/tools.py`) must not modify core.** Tools are wrappers around `bazi_pro.core` functions, never modify them.

19. **流式 Chat 端点 (`/api/v2/chat/stream`) must save assistant reply on error.** When LLM call fails in SSE generator, save error message as assistant reply to avoid orphaned user messages.

20. **`_parse_report_json` must include all chapter keys.** When adding new report chapters, update `new_keys`, `old_keys` fallback, and default dict in `_parse_report_json()`.

21. **`ChatStreamEvent` type must include all event types.** When backend sends new SSE event types (e.g., `tool_call`, `tool_result`), update `ChatStreamEvent` type union in `frontend/src/lib/api.ts`.

## Verification Commands

After any change, run the full chain (mirrors CI):

```bash
# Lint
ruff check server/ bazi_pro/ tests/

# Compile check (catches syntax errors)
python -m compileall bazi_pro server scripts tests -q

# Core + golden tests
python -m pytest tests/test_core.py tests/test_full_analysis.py -v
python tests/run_golden.py

# Doctor (two paths, both must pass)
python scripts/doctor.py
python -m bazi_pro.doctor
```

All commands must exit with code 0.

## Environment & Toolchain

- **Python >= 3.10** — uses `list[dict]`, `dict | None` syntax.
- **Frontend: pnpm** — not npm or yarn. Lock file is `frontend/pnpm-lock.yaml`.
- **Frontend: Node >= 18** — Next.js 16 requirement.
- **Linting: ruff** — config in `pyproject.toml` (`[tool.ruff]`), targets `py310`, line-length 120.
- **Type hints: mypy** — config in `pyproject.toml`, `ignore_missing_imports = true`.
- **Test runner: pytest** — config in `pyproject.toml` (`[tool.pytest.ini_options]`), `testpaths = ["tests"]`, `addopts = "-v --tb=short"`.

## Quick Reference

```bash
# Install (minimal)
pip install -e .

# Install (all extras: hybrid, report, pdf, server, ziwei, tui)
pip install -e ".[all]"

# Full test suite
python -m pytest -q

# Golden case regression
python tests/run_golden.py

# Single test file
python -m pytest tests/test_core.py -v

# Frontend dev
cd frontend && pnpm install && pnpm dev

# Backend dev (port 8711)
python -m uvicorn server.app:app --host 127.0.0.1 --port 8711

# One-click start (both backend + frontend)
.\start.ps1
```

## Key Gotchas

- **`percent` vs `percent_adjusted`** — `calc_element_forces()` returns both. Pattern screening uses `percent` (raw); 化气格 uses `percent_adjusted` (合化修正).
- **从格检测 gans must exclude day master** — `_screen_layer_ccong*` must pass `gans_no_dm = [g for g in gans if g != day_master]` to `_count_shishen_categories()`, otherwise 从格 detection always fails.
- **天干合/地支冲 mappings** — use explicit dict (not frozenset). See `_GAN_HE_PARTNER` and `_ZHI_CHONG_MAP`.
- **Schools use lazy loading** — `schools/__init__.py` uses `_ensure_schools_loaded()` with `import bazi_pro.core.schools.xxx` style (not `from ... import`).
- **Windows compat** — subprocess tests use `sys.executable` (not `python3`); file I/O must specify `encoding="utf-8"`.
- **Frontend TS quirk** — echarts-for-react types conflict with React 19 strict types; files using ECharts need `// @ts-nocheck`.
- **`chat_completion_stream_typed` vs `chat_completion_stream_with_tools`** — the former is true SSE streaming, the latter is non-streaming with fake chunking (20-char slices). Use the typed version for real streaming.
- **紫微斗数 iztro-py dependency** — `server/ziwei.py` imports `iztro-py` as optional dependency. All functions return `{"error": "..."}` when iztro-py is not installed.
- **Function Calling 工具集** — `server/agents/tools.py` defines 5 tools (paipan/query_geju/query_yongshen/query_shensha/query_classical). Tools are wrappers, never modify core.
- **RAG 检索模式** — `retrieve_for_chat()` and `retrieve_for_report()` support `retrieval_mode` parameter: "bm25" (default), "hybrid" (requires sentence-transformers), "auto" (hybrid with BM25 fallback).
