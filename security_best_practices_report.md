# bazi-pro Security Best Practices Report

**Date:** 2026-05-25  
**Scope:** Server layer (`server/`) + plugin system (`plugins/`) + core modules  
**Framework:** Python 3.10+ / FastAPI 0.110+ / Uvicorn / Pydantic v2  
**Reference Spec:** `python-fastapi-web-server-security.md`

---

## Executive Summary

The bazi-pro server implements several good security practices: Pydantic schema validation, API key authentication, request size limits, rate limiting, and a global exception handler that hides internal errors in non-debug mode. However, the audit identified **10 findings** ranging from Critical to Low severity. The most urgent issues are: unsafe `pickle.load` on disk-cached files, WebSocket authentication occurring after connection acceptance, missing security headers, and OpenAPI docs exposure without production controls. Addressing the Critical and High findings should be prioritized.

---

## Critical Findings

### FINDING-001: Unsafe deserialization via `pickle.load` on cached BM25 index

| Field | Detail |
|---|---|
| **Rule ID** | FASTAPI-INJECT-001 (extended: unsafe deserialization) |
| **Severity** | Critical |
| **Location** | [retrieve_classical.py:205](bazi_pro/retrieve_classical.py#L205) |
| **Evidence** | `data = pickle.load(f)` — loads a pickled object from a file on disk |
| **Impact** | If an attacker can write to the BM25 cache directory (e.g., via path traversal, compromised build process, or shared filesystem), they can achieve arbitrary code execution when the cache is loaded. `pickle.load` executes arbitrary Python during deserialization. |
| **Fix** | Replace `pickle` with a safe serialization format (e.g., `json`, `msgpack`, or `safetensors`). If pickle must be retained for performance, add an integrity check (HMAC-SHA256 signature) and validate the signature before loading. |
| **Mitigation** | Ensure cache directory permissions are restrictive (0700); set `PYTHONHASHSEED` to a fixed value if pickle is kept; consider signing cached data. |
| **False positive notes** | Low risk if the cache directory is not writable by untrusted users and the server runs in a container with read-only filesystem for that path. Verify deployment constraints. |

---

## High Findings

### FINDING-002: WebSocket authentication occurs after `ws.accept()`

| Field | Detail |
|---|---|
| **Rule ID** | FASTAPI-WS-001 |
| **Severity** | High |
| **Location** | [app.py:483-489](server/app.py#L483-L489) |
| **Evidence** | ```python @app.websocket("/ws/{run_id}") async def ws_connect(ws: WebSocket, run_id: str): await ws.accept() if _API_KEY: api_key = ws.headers.get('x-api-key', '') if api_key != _API_KEY: await ws.close(code=4001, reason='Invalid API key') return ``` |
| **Impact** | The WebSocket handshake completes (accept) before authentication is checked. An attacker can open WebSocket connections without valid credentials, consuming server resources (connection slots, memory). This also means the connection is briefly "authenticated" before being closed, which could confuse downstream logic. |
| **Fix** | Perform authentication checks **before** calling `ws.accept()`. If auth fails, close with an appropriate code without accepting. Example: check headers first, then accept only on success. |
| **Mitigation** | Add connection-level rate limiting for WebSocket endpoints. |
| **False positive notes** | The current code does close the connection quickly after detecting invalid auth, but the accept-then-close pattern is still a resource leak vector under load. |

### FINDING-003: API key comparison uses direct string equality (timing attack)

| Field | Detail |
|---|---|
| **Rule ID** | FASTAPI-AUTH-001 (extended: timing-safe comparison) |
| **Severity** | High |
| **Location** | [app.py:98](server/app.py#L98) |
| **Evidence** | `if api_key == _API_KEY:` |
| **Impact** | Direct string comparison (`==`) is vulnerable to timing attacks. An attacker can measure response times to progressively guess the API key character by character. While this requires many requests and precise timing, it is a well-known attack vector for API keys. |
| **Fix** | Use `hmac.compare_digest()` for constant-time comparison: `import hmac; if hmac.compare_digest(api_key, _API_KEY):` |
| **Mitigation** | Rate limiting (already in place) makes timing attacks harder but does not eliminate the vulnerability. |
| **False positive notes** | Practical exploitation is difficult over network due to jitter, but the fix is trivial and should be applied. |

### FINDING-004: No security response headers set

| Field | Detail |
|---|---|
| **Rule ID** | FASTAPI-HEADERS-001 |
| **Severity** | High (the app serves HTML) |
| **Location** | [app.py](server/app.py) — no security header middleware configured |
| **Evidence** | The application serves an HTML page at `/` and has no middleware setting `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, or `Content-Security-Policy`. |
| **Impact** | Without `X-Content-Type-Options: nosniff`, browsers may MIME-sniff responses. Without `X-Frame-Options` / `frame-ancestors`, the page can be framed (clickjacking). Without CSP, any XSS (even in the inline JS) has full capabilities. |
| **Fix** | Add a middleware or use Starlette's `Middleware` to set: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` (or CSP `frame-ancestors: 'none'`), `Referrer-Policy: strict-origin-when-cross-origin`, and a basic CSP. |
| **Mitigation** | These headers can also be set at the reverse proxy/CDN level if one is deployed in front. |
| **False positive notes** | If a reverse proxy already sets these headers, this finding can be dismissed. Verify at the edge. |

### FINDING-005: Plugin loader executes arbitrary Python code from filesystem

| Field | Detail |
|---|---|
| **Rule ID** | FASTAPI-INJECT-002 (extended: arbitrary code execution) |
| **Severity** | High |
| **Location** | [loader.py:35-39](plugins/loader.py#L35-L39) |
| **Evidence** | `spec = importlib.util.spec_from_file_location(...); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)` — dynamically loads and executes any `main.py` found in plugin directories. |
| **Impact** | If an attacker can write a `main.py` + `plugin.json` to the plugins directory (or any directory scanned), they achieve arbitrary code execution in the server process. The `PLUGIN_WHITELIST` in `plugin_api.py` only checks the plugin name after code execution, not before. |
| **Fix** | 1. Validate plugin directory integrity (checksums, signatures) before loading. 2. Move whitelist check before `exec_module`. 3. Consider running plugins in a sandboxed subprocess. 4. Restrict filesystem write access to the plugins directory. |
| **Mitigation** | Ensure the plugins directory is not writable by the server process or untrusted users. Use filesystem permissions and container read-only mounts. |
| **False positive notes** | If the plugins directory is read-only in production (e.g., baked into a Docker image), the risk is significantly reduced. Verify deployment. |

---

## Medium Findings

### FINDING-006: OpenAPI docs enabled without production controls

| Field | Detail |
|---|---|
| **Rule ID** | FASTAPI-OPENAPI-001 |
| **Severity** | Medium |
| **Location** | [app.py:55-56](server/app.py#L55-L56) |
| **Evidence** | `docs_url="/docs", redoc_url="/redoc"` — both are explicitly enabled with no environment-based toggle. |
| **Impact** | In production, `/docs` and `/redoc` expose the full API schema, including all endpoints, request/response models, and authentication schemes. This aids attackers in understanding the attack surface. |
| **Fix** | Make docs URL conditional on environment: `docs_url="/docs" if os.environ.get("BAZI_ENABLE_DOCS") else None`. Apply same for `redoc_url` and `openapi_url`. |
| **Mitigation** | Block `/docs`, `/redoc`, `/openapi.json` at the reverse proxy level in production. |
| **False positive notes** | For internal/development APIs, docs exposure may be acceptable. |

### FINDING-007: CORS with `allow_headers=["*"]`

| Field | Detail |
|---|---|
| **Rule ID** | FASTAPI-CORS-001 |
| **Severity** | Medium |
| **Location** | [app.py:75](server/app.py#L75) |
| **Evidence** | `allow_headers=["*"]` — allows any request header in CORS preflight responses. |
| **Impact** | While `allow_origins` is properly controlled (empty by default, explicit list, or `*` without credentials), the wildcard `allow_headers` is overly permissive. Combined with a permissive origin, this could facilitate cross-origin attacks. |
| **Fix** | Replace `allow_headers=["*"]` with an explicit list of allowed headers, e.g., `allow_headers=["Content-Type", "X-API-Key"]`. |
| **Mitigation** | Current CORS defaults (disabled when `BAZI_CORS_ORIGINS` is unset) mitigate this in the default configuration. |
| **False positive notes** | The `allow_headers=["*"]` only affects CORS preflight; it does not allow browsers to send arbitrary headers — only those explicitly listed in the request's `Access-Control-Request-Headers`. Still, explicit is better. |

### FINDING-008: No Host header validation (TrustedHostMiddleware missing)

| Field | Detail |
|---|---|
| **Rule ID** | FASTAPI-HOST-001 |
| **Severity** | Medium |
| **Location** | [app.py](server/app.py) — no `TrustedHostMiddleware` configured |
| **Evidence** | The application does not use `TrustedHostMiddleware` or any host validation. The app binds to `0.0.0.0` by default. |
| **Impact** | Without host validation, an attacker could craft requests with a malicious `Host` header. If any part of the application generates URLs based on the Host header (e.g., in the HTML page or future password-reset flows), this could lead to cache poisoning or open redirect. |
| **Fix** | Add `TrustedHostMiddleware` with an explicit list of allowed hosts, configurable via environment variable (e.g., `BAZI_ALLOWED_HOSTS`). |
| **Mitigation** | If behind a reverse proxy that validates Host, this is less critical. |
| **False positive notes** | Currently, the app does not appear to use `request.url` or Host-derived values for security-sensitive operations, reducing immediate risk. |

---

## Low Findings

### FINDING-009: Debug mode controlled by environment variable with no default-off guarantee

| Field | Detail |
|---|---|
| **Rule ID** | FASTAPI-DEPLOY-002 |
| **Severity** | Low |
| **Location** | [app.py:196](server/app.py#L196) and [app.py:513](server/app.py#L513) |
| **Evidence** | `debug = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")` — used in two places to decide whether to expose exception details. |
| **Impact** | If `DEBUG=true` is accidentally set in production, internal error messages and exception details will be returned to clients, potentially leaking sensitive implementation details (file paths, variable names, stack traces). |
| **Fix** | This is already reasonably implemented (defaults to off). Consider adding a startup warning log when DEBUG is enabled, and ensure production deployment scripts never set `DEBUG=true`. |
| **Mitigation** | Current default is safe (off). |
| **False positive notes** | The implementation is actually decent — it defaults to hiding errors. This is a low-severity hardening suggestion. |

### FINDING-010: Uvicorn runs without explicit worker configuration in production entrypoint

| Field | Detail |
|---|---|
| **Rule ID** | FASTAPI-DEPLOY-001 |
| **Severity** | Low |
| **Location** | [app.py:523](server/app.py#L523) |
| **Evidence** | `uvicorn.run(app, host=host, port=port, log_level=log_level)` — single-process, no `--workers` configuration, no `reload` flag. |
| **Impact** | Running a single Uvicorn process without worker configuration may not be production-ready for high-traffic deployments. However, there is no `reload=True` (good), and for a single-container deployment this may be acceptable. |
| **Fix** | For production, consider using `uvicorn.run(..., workers=N)` or running behind Gunicorn with Uvicorn workers. Add a `BAZI_WORKERS` environment variable. |
| **Mitigation** | Deploy behind a process manager (systemd, Docker with restart policies) or use Gunicorn as the process manager. |
| **False positive notes** | For low-traffic or development use, single-worker is fine. This is a production hardening suggestion. |

---

## Positive Security Practices Observed

1. **Pydantic schema validation** — All API inputs are validated via `BaziAnalysisRequest` with strict field validators (FASTAPI-VALID-001 ✅)
2. **API key authentication** — Protected endpoints use `Depends(_verify_api_key)` consistently (FASTAPI-AUTH-001 ✅)
3. **Request size limits** — Custom `_RequestSizeLimitMiddleware` enforces a 10KB default limit (FASTAPI-LIMITS-001 ✅)
4. **Rate limiting** — Both memory and Redis backends with configurable limits (FASTAPI-LIMITS-001 ✅)
5. **Global exception handler** — Hides internal error details when DEBUG is off (FASTAPI-DEPLOY-002 ✅)
6. **CORS defaults to disabled** — No origins allowed unless explicitly configured (FASTAPI-CORS-001 ✅)
7. **No SQL injection surface** — No database/SQL usage in the codebase (FASTAPI-INJECT-001 ✅)
8. **No SSRF surface** — No outbound HTTP requests to user-controlled URLs (FASTAPI-SSRF-001 ✅)
9. **No shell injection surface** — No `subprocess`/`os.system` in server code (FASTAPI-INJECT-002 ✅)
10. **UUID-based run IDs** — Uses `uuid.uuid4().hex` for task identifiers, preventing enumeration (General Security Advice ✅)
11. **No secrets in URLs** — API key sent via `X-API-Key` header, not query parameter (FASTAPI-AUTH-002 ✅)
12. **Task data filtering** — Internal fields (prefixed with `_`) are stripped from API responses (FASTAPI-RESP-001 ✅)

---

## Summary Table

| ID | Severity | Rule | Summary | Status |
|---|---|---|---|---|
| FINDING-001 | Critical | INJECT | `pickle.load` on cached BM25 index | Open |
| FINDING-002 | High | WS-001 | WebSocket auth after `ws.accept()` | Open |
| FINDING-003 | High | AUTH-001 | Timing-unsafe API key comparison | Open |
| FINDING-004 | High | HEADERS-001 | No security response headers | Open |
| FINDING-005 | High | INJECT-002 | Plugin loader executes arbitrary code | Open |
| FINDING-006 | Medium | OPENAPI-001 | Docs enabled without prod toggle | Open |
| FINDING-007 | Medium | CORS-001 | `allow_headers=["*"]` | Open |
| FINDING-008 | Medium | HOST-001 | No TrustedHostMiddleware | Open |
| FINDING-009 | Low | DEPLOY-002 | DEBUG env var (default off, but no warning) | Open |
| FINDING-010 | Low | DEPLOY-001 | Single-worker uvicorn in production | Open |
