# Codebase Audit Final Report — bazi-pro

**Audit ID**: audit-20260619-174634
**Auditor**: ln-620-codebase-auditor
**Date**: 2026-06-19
**Scope**: Full codebase (Python backend + Next.js frontend)
**Workers Executed**: ln-621 through ln-629 (all 9 domains)

---

## Executive Summary

The bazi-pro codebase has solid foundations in input validation, calculation correctness, and documentation. However, the audit identified **5 CRITICAL**, **12 HIGH**, and **18 MEDIUM** severity issues across security, concurrency, delivery gates, and operational readiness. The most urgent concerns are authentication gaps, concurrency safety in the database layer, and missing operational infrastructure (correlation IDs, graceful shutdown, config validation).

**Overall Risk Rating**: **MEDIUM-HIGH** — The codebase works correctly for single-user/development scenarios but has significant gaps for production deployment.

### Top 5 Critical Issues

| # | Issue | Domain | Impact |
|---|-------|--------|--------|
| 1 | API key auth disabled by default in non-production | Security | Unauthorized access to all endpoints |
| 2 | Single shared SQLite connection with no locking | Concurrency | Data corruption under concurrent writes |
| 3 | Background tasks race on shared result dict | Concurrency | Non-deterministic DB state |
| 4 | No startup config validation | Lifecycle | Silent failures, crash on bad env vars |
| 5 | v2 endpoints lack authentication | Security | Free LLM abuse, rate limit bypass |

---

## Deduplicated Issue Table

### CRITICAL (5 issues)

| # | Domain | Issue | Location | Fix |
|---|--------|-------|----------|-----|
| C1 | Security | API key auth bypassed by default in non-production | `server/deps.py:65-70` | Fail closed: require `BAZI_ALLOW_UNAUTHED=1` to disable |
| C2 | Concurrency | Single shared SQLite connection, no asyncio lock | `server/db.py:16,35-52` | Add `asyncio.Lock` around get-use-commit cycle |
| C3 | Concurrency | Background tasks race on shared `result` dict | `server/analysis.py:320-424` | Await tasks before returning or use separate copies |
| C4 | Config | No startup validation of critical env vars | `server/app.py`, `server/llm.py:75` | Add `validate_config()` in lifespan; fix `LLM_TIMEOUT` parse |
| C5 | Security | v2 analyze/chat/report endpoints unauthenticated | `server/routes/v2_*.py` | Add `_auth=Depends(verify_api_key)` to all endpoints |

### HIGH (12 issues)

| # | Domain | Issue | Location | Fix |
|---|--------|-------|----------|-----|
| H1 | Security | API key accepted via query string `?token=` | `server/deps.py:73-75` | Remove query-string support; header-only |
| H2 | Security | DEBUG mode leaks exception details to clients | `server/app.py:241-243` | Never send raw exceptions; log server-side only |
| H3 | Security | WebSocket auth passes key in query string | `server/app.py:397` | Use short-lived pre-auth tokens |
| H4 | Lifecycle | No graceful shutdown for background tasks | `server/app.py:79` | Track tasks, cancel on shutdown, mark interrupted |
| H5 | Lifecycle | DB connection fragile, no retry, private attr access | `server/db.py:46-47` | Add retry; use `SELECT 1` ping instead of `_connection` |
| H6 | Diagnosability | No correlation/request ID | `server/app.py` | Add middleware with `X-Request-ID` + `contextvars` |
| H7 | Delivery | Mypy configured but never runs in CI | `.github/workflows/ci.yml` | Add mypy step to CI |
| H8 | Delivery | Coverage threshold only 45% | `pyproject.toml:79` | Raise to 65%+ |
| H9 | Delivery | `server` package namespace collision risk | `pyproject.toml:54` | Rename to `bazi_server` or nest under `bazi_pro` |
| H10 | Dead Code | 3 unused `AnalysisEngine` static methods | `bazi_pro/__init__.py:217,235,245` | Remove dead methods |
| H11 | Duplication | Pillar parsing logic in 3 places | `core/__init__.py`, `server/analysis.py` | Factor into `build_pillar_list()` |
| H12 | Duplication | `TIANGAN`/`DIZHI` defined in 3 places | `validation.py`, `gongwei.py`, `ziwei/constants.py` | Import from canonical source |

### MEDIUM (18 issues)

| # | Domain | Issue | Location | Fix |
|---|--------|-------|----------|-----|
| M1 | Security | CORS wildcard (`*`) support | `server/app.py:93-110` | Reject `*` in production |
| M2 | Security | OpenAPI docs enabled by default | `server/app.py:55,88-90` | Auto-disable in production |
| M3 | Security | `/metrics` exposed without auth | `server/app.py:283-293` | Restrict to localhost or add auth |
| M4 | Security | `list_analyses` unbounded `page_size` | `server/db.py:197-230` | Clamp to max 100 |
| M5 | Security | Rate limiter key-space poisoning | `server/ratelimiter.py:33-41` | Hash keys; use LRU eviction |
| M6 | Security | Chat message no `max_length` | `server/routes/v2_chat.py:130` | Add 4096 char limit |
| M7 | Concurrency | `MemoryRateLimiter._buckets` unprotected | `server/ratelimiter.py:24-54` | Add `threading.Lock` |
| M8 | Concurrency | `MemoryTaskStore._tasks` unprotected | `server/taskstore.py:50-89` | Add `threading.Lock` |
| M9 | Concurrency | `get_db()` lazy-init race after `close_db()` | `server/db.py:35-52` | Wrap full body in init lock |
| M10 | Diagnosability | Inconsistent logger names | Multiple `server/` modules | Use `__name__` everywhere |
| M11 | Diagnosability | Silent exception swallowing | `routes/v2_analysis.py`, `analysis.py` | Add `logger.warning()` to all bare excepts |
| M12 | Diagnosability | Health check incomplete (no DB ping, no 503) | `server/app.py:264-280` | Add DB ping; return 503 when degraded |
| M13 | Delivery | Ruff rules too narrow (no B, S, UP) | `pyproject.toml:68` | Enable bugbear, bandit, pyupgrade |
| M14 | Delivery | `ignore_missing_imports` too broad | `pyproject.toml:75` | Per-package overrides |
| M15 | Dead Code | 4 unused metrics helper functions | `server/metrics.py:108-166` | Remove or consolidate |
| M16 | Dead Code | 8 unused Pydantic result models | `server/schemas.py:117-191` | Wire into routes or remove |
| M17 | Duplication | `GAN_WUXING`/`ZHI_WUXING` redefined in scripts | `scripts/dashboard.py:11-26` | Import from `bazi_pro.core.constants` |
| M18 | Lifecycle | SSE buffer memory for stalled clients | `server/sse.py:16-26` | Add periodic TTL cleanup |

### LOW (12 issues)

| # | Domain | Issue | Location |
|---|--------|-------|----------|
| L1 | Security | Health endpoint discloses infrastructure | `server/app.py:264-280` |
| L2 | Security | No HTTPS/HSTS enforcement | `server/app.py:453` |
| L3 | Security | Chunked body logic bug | `server/app.py:166-209` |
| L4 | Security | `load_dotenv` loads server/.env | `server/app.py:14` |
| L5 | Concurrency | `ws.py` ConnectionManager no lock | `server/ws.py` |
| L6 | Concurrency | `sse.py` v2_active_ids without lock | `server/sse.py` |
| L7 | Diagnosability | BM25 warmup failure unverified | `server/app.py:62-78` |
| L8 | Lifecycle | Cache singleton never closed | `server/cache.py:140-148` |
| L9 | Config | `get_int_env` min_value=1 may surprise | `server/deps.py:24` |
| L10 | Delivery | No plugin system tests | `plugins/` |
| L11 | Dead Code | `core_rules.py` deprecated shim | `bazi_pro/core_rules.py` |
| L12 | Dead Code | Thin wrapper scripts | `scripts/doctor.py` etc. |

---

## Prioritized Remediation Plan

### CRITICAL — Fix Immediately (Week 1)

| # | Issue | Effort | Acceptance Check |
|---|-------|--------|------------------|
| C1 | Fail-closed auth | 2h | `BAZI_API_KEY` required unless `BAZI_ALLOW_UNAUTHED=1` |
| C2 | SQLite connection lock | 4h | Concurrent requests don't corrupt DB; load test passes |
| C3 | Background task race | 3h | Result dict consistent; no partial writes |
| C4 | Startup config validation | 3h | Bad `LLM_TIMEOUT=abc` logs warning, doesn't crash |
| C5 | Auth on all v2 endpoints | 2h | Unauthenticated requests return 401 |

**Total estimated effort**: ~14 hours

### HIGH — Fix Within 2 Weeks (Weeks 2-3)

| # | Issue | Effort | Acceptance Check |
|---|-------|--------|------------------|
| H1 | Remove query-string token | 1h | `?token=` returns 401 |
| H2 | Sanitize debug exceptions | 1h | Client never sees raw exception |
| H4 | Graceful shutdown | 4h | Background tasks marked interrupted on SIGTERM |
| H5 | DB connection retry | 3h | Transient failures auto-recover |
| H6 | Correlation ID middleware | 3h | All log lines include request ID |
| H7 | Mypy in CI | 1h | CI fails on type errors |
| H8 | Coverage threshold 65% | 1h | CI enforces new threshold |
| H10 | Remove dead methods | 1h | Tests pass without dead code |
| H11 | Factor pillar parsing | 3h | Single `build_pillar_list()` function |

**Total estimated effort**: ~18 hours

### MEDIUM — Fix Within 1 Month (Weeks 4-6)

| # | Issue | Effort |
|---|-------|--------|
| M1-M6 | Security hardening | 6h |
| M7-M9 | Concurrency locks | 4h |
| M10-M12 | Diagnosability | 4h |
| M13-M14 | Lint/type config | 2h |
| M15-M18 | Dead code cleanup | 4h |

**Total estimated effort**: ~20 hours

---

## Research Sources

| Source Type | Source | Used For |
|-------------|--------|----------|
| Official docs | FastAPI security docs | Auth patterns, CORS, middleware |
| Official docs | SQLite WAL mode docs | Concurrency model |
| Official docs | aiosqlite docs | Async connection safety |
| Best practice | OWASP API Security Top 10 | Authentication, input validation |
| Best practice | Python async best practices | Lock patterns, task management |

---

## Cleanup Note

This report consolidates findings from all 9 audit workers (ln-621 through ln-629). No temporary worker markdown reports were created — all analysis was performed inline during the audit session.

---

## Self-Check

- [x] Research completed (web search, official docs)
- [x] All applicable worker summaries recorded (9/9)
- [x] Worker conflicts resolved with `codebase_audit_worker_boundaries.md`
- [x] Aggregation completed (deduplicated from ~60 raw findings to 47 unique)
- [x] Final remediation report written
- [x] Cleanup verified (no temp files to remove)
- [x] Coordinator summary recorded

---

**Report generated**: 2026-06-19T17:46:34Z
**Auditor**: ln-620-codebase-auditor v5.0.0
