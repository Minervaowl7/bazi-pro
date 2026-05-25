# Agent Guardrails

Rules that any AI agent (or human contributor) must follow when modifying this project.

## Core Rules

1. **Never add core imports from package root.** `bazi_pro/core/` modules must import only from `bazi_pro.core.*`, never from `bazi_pro` directly. This prevents circular dependencies.

2. **Every new rule needs at least one test.** If you add a new function to `bazi_pro/core/`, you must add a corresponding test in `tests/test_core.py` or `tests/test_full_analysis.py`.

3. **Every public API change needs a compatibility test or migration note.** If you change the keys returned by `AnalysisEngine.analyze()` or `full_analysis()`, add a test in `TestAnalysisEngineReturnContract` and update the `EXPECTED_TOP_LEVEL_KEYS` set.

4. **Golden cases cannot decrease.** The count in `tests/golden_cases/` must never go down. You may add or fix cases, but never remove them without replacing with equivalent coverage.

5. **Script wrappers must propagate exit codes.** All `scripts/*.py` wrappers must use `sys.exit(main())`, not bare `main()`.

6. **Doctor must fail on critical issues.** `bazi_pro/doctor.py` must return exit code 1 if any check with status `FAIL` is found. New consistency checks should be added to the `consistency_checks` list.

7. **No LLM placeholders in deterministic output.** Pattern names, wangshuai verdicts, and yongshen values must never be "待LLM分析" or similar placeholders.

8. **Extreme flags must be checked before generic.** In `judge_wangshuai()`, "极旺"/"极弱" must be checked before "身旺"/"身弱" to prevent shadowing.

9. **Retrieval errors must be visible.** `AnalysisEngine.retrieve()` must not silently swallow exceptions. Errors must appear in `result["retrieval"]["warnings"]`.

10. **CI must run the full verification chain.** The CI workflow must include: `pip install -e ".[all]"`, `python -m compileall`, `python -m pytest -q tests`, `python scripts/doctor.py`, `python tests/run_golden.py`, and `python -m bazi_pro.doctor`.

## Verification Commands

After any change, run:

```bash
python -m pytest tests/test_core.py tests/test_full_analysis.py -v
python tests/run_golden.py
python -m bazi_pro.doctor
```

All three must pass with zero exit code.
