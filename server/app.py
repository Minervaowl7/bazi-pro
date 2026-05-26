#!/usr/bin/env python3
"""
bazi-pro FastAPI 应用 v5.0
API 路由：分析、状态查询、结果获取、仪表盘
"""

import asyncio
import hmac
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, Request, Security, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.analysis import run_analysis
from server.auth.jwt_handler import verify_token
from server.auth.routes import router as auth_router
from server.billing.quota import check_quota, deduct_quota
from server.billing.routes import router as billing_router
from server.cache import get_cache
from server.database import backend as db_backend
from server.database import close_db, get_db, get_user_analyses, init_db, is_degraded, persist_analysis
from server.models import User
from server.ratelimiter import MemoryRateLimiter, RateLimiter, RedisRateLimiter, create_rate_limiter
from server.schemas import BaziAnalysisRequest
from server.taskstore import MemoryTaskStore, RedisTaskStore, create_task_store
from server.ws import manager

logger = logging.getLogger("bazi-pro")


def _get_int_env(name: str, default: int, min_value: int = 1) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
        if value < min_value:
            raise ValueError
        return value
    except (ValueError, TypeError):
        logger.warning("Invalid %s=%r, using default %s", name, raw, default)
        return default


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


_enable_docs = os.environ.get('BAZI_ENABLE_DOCS', '').lower() in ('1', 'true', 'yes')

app = FastAPI(
    title="bazi-pro API",
    description="专业八字命理解读引擎 Web 服务\n\n⚠️ 免责声明：本服务仅供传统文化学习与参考，分析结果不构成任何决策依据。命理解释包含规则推导、古籍检索和 LLM 辅助解释，请勿将模型输出视为确定性事实。",
    version="5.0.0",
    docs_url="/docs" if _enable_docs else None,
    redoc_url="/redoc" if _enable_docs else None,
    openapi_url="/openapi.json" if _enable_docs else None,
)

_cors_origins_str = os.environ.get('BAZI_CORS_ORIGINS', '')
if not _cors_origins_str:
    _cors_origins = []
    _cors_credentials = False
elif _cors_origins_str == '*':
    _cors_origins = ['*']
    _cors_credentials = False
else:
    _cors_origins = [o.strip() for o in _cors_origins_str.split(',')]
    _cors_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_credentials,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)

if not _cors_origins:
    logger.warning("BAZI_CORS_ORIGINS not set — CORS disabled. Set BAZI_CORS_ORIGINS=* or comma-separated origins.")

_allowed_hosts_str = os.environ.get('BAZI_ALLOWED_HOSTS', '')
if _allowed_hosts_str:
    _allowed_hosts = [h.strip() for h in _allowed_hosts_str.split(',') if h.strip()]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)
    logger.info("TrustedHostMiddleware enabled: %s", _allowed_hosts)


class _SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            async def send_with_headers(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"x-content-type-options", b"nosniff"))
                    headers.append((b"x-frame-options", b"DENY"))
                    headers.append((b"referrer-policy", b"strict-origin-when-cross-origin"))
                    headers.append(
                        (b"permissions-policy", b"camera=(), microphone=(), geolocation=()")
                    )
                    headers.append(
                        (b"content-security-policy",
                         b"default-src 'self'; script-src 'self' 'unsafe-inline'; "
                         b"style-src 'self' 'unsafe-inline'; img-src 'self'; "
                         b"connect-src 'self' ws: wss:; frame-ancestors 'none'")
                    )
                    message["headers"] = headers
                await send(message)
            await self.app(scope, receive, send_with_headers)
        else:
            await self.app(scope, receive, send)


app.add_middleware(_SecurityHeadersMiddleware)


_API_KEY = os.environ.get('BAZI_API_KEY', '')
_api_key_scheme = APIKeyHeader(name='X-API-Key', auto_error=False)


class _AuthError(Exception):
    pass


@app.exception_handler(_AuthError)
async def _auth_error_handler(request, exc):
    return error_response(401, "UNAUTHORIZED", "认证信息无效或缺失")


async def _verify_auth(request: Request, api_key: str = Security(_api_key_scheme)):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
        payload = verify_token(token)
        if payload:
            return payload
    if api_key and _API_KEY and hmac.compare_digest(api_key, _API_KEY):
        return None
    if not _API_KEY:
        return None
    raise _AuthError()


async def get_current_user(request: Request, db: Optional[AsyncSession] = Depends(get_db)):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise _AuthError()
    token = auth_header[len("Bearer "):]
    payload = verify_token(token)
    if payload is None:
        raise _AuthError()
    user_id = payload.get("sub")
    if not user_id:
        raise _AuthError()
    if db is None:
        raise _AuthError()
    stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise _AuthError()
    return user


class _RequestSizeLimitMiddleware:
    def __init__(self, app, max_body_size=10240):
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            content_length = None
            transfer_encoding = None
            for name, value in scope.get("headers", []):
                if name == b"content-length":
                    try:
                        content_length = int(value)
                    except (ValueError, TypeError):
                        response = error_response(400, "BAD_REQUEST", "无效的 Content-Length")
                        await response(scope, receive, send)
                        return
                if name == b"transfer-encoding":
                    transfer_encoding = value.decode("latin-1").lower()

            if content_length is not None and content_length > self.max_body_size:
                response = error_response(413, "PAYLOAD_TOO_LARGE", "请求体过大")
                await response(scope, receive, send)
                return

            if transfer_encoding and "chunked" in transfer_encoding:
                received = 0
                exceeded = False

                async def chunked_receive():
                    nonlocal received, exceeded
                    message = await receive()
                    if message.get("type") == "http.request":
                        body = message.get("body", b"")
                        received += len(body)
                        if received > self.max_body_size:
                            exceeded = True
                            message["body"] = b""
                            message["more_body"] = False
                    return message

                await self.app(scope, chunked_receive, send)

                if exceeded:
                    resp = error_response(413, "PAYLOAD_TOO_LARGE", "请求体过大")
                    await resp(scope, receive, send)
                    return
                return

        await self.app(scope, receive, send)


class _RateLimitMiddleware:
    def __init__(self, app, rate_limiter: RateLimiter):
        self.app = app
        self._limiter = rate_limiter

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            client = scope.get("client")
            ip = client[0] if client else "unknown"
            api_key = ""
            for name, value in scope.get("headers", []):
                if name == b"x-api-key":
                    api_key = value.decode("latin-1")
            key = f"{ip}:{api_key}" if api_key else ip
            if not self._limiter.is_allowed(key):
                response = error_response(429, "RATE_LIMITED", "请求过于频繁，请稍后重试")
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


_MAX_PAYLOAD_BYTES = _get_int_env("BAZI_MAX_PAYLOAD_BYTES", 10240)
_RATE_LIMIT_REQUESTS = _get_int_env("BAZI_RATE_LIMIT_REQUESTS", 30)
_RATE_LIMIT_WINDOW_SECONDS = _get_int_env("BAZI_RATE_LIMIT_WINDOW_SECONDS", 60)
_rate_limiter = create_rate_limiter(
    max_requests=_RATE_LIMIT_REQUESTS,
    window_seconds=_RATE_LIMIT_WINDOW_SECONDS,
)

app.add_middleware(
    _RequestSizeLimitMiddleware,
    max_body_size=_MAX_PAYLOAD_BYTES,
)
app.add_middleware(
    _RateLimitMiddleware,
    rate_limiter=_rate_limiter,
)


@app.exception_handler(Exception)
async def _global_exception_handler(request, exc):
    debug = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")
    message = str(exc) if debug else "服务器内部错误"
    return error_response(500, "INTERNAL_ERROR", message)


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(request, exc):
    errors = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err.get("loc", []))
        errors.append({"field": loc, "message": err.get("msg", ""), "type": err.get("type", "")})
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": "请求校验失败", "details": {"errors": errors}}},
    )


_task_store = create_task_store()
_TASK_TTL_SECONDS = _get_int_env("BAZI_TASK_TTL_SECONDS", 7200)
_MAX_CONCURRENT_TASKS = _get_int_env("BAZI_MAX_CONCURRENT_TASKS", 1000)


def _cleanup_expired_tasks() -> None:
    _task_store.cleanup_expired(_TASK_TTL_SECONDS)


def _backend_name(store) -> str:
    if isinstance(store, RedisTaskStore):
        if store.is_degraded:
            return "redis(degraded)"
        return "redis"
    if isinstance(store, MemoryTaskStore):
        return "memory"
    return type(store).__name__


def _ratelimiter_backend_name(limiter) -> str:
    if isinstance(limiter, RedisRateLimiter):
        if limiter.is_degraded:
            return "redis(degraded)"
        return "redis"
    if isinstance(limiter, MemoryRateLimiter):
        return "memory"
    return type(limiter).__name__


app.include_router(auth_router)
app.include_router(billing_router)


@app.on_event("startup")
async def _on_startup():
    await init_db()
    if is_degraded():
        logger.warning("Database: running in degraded mode — %s", db_backend())
    else:
        logger.info("Database: %s backend active", db_backend())


@app.on_event("shutdown")
async def _on_shutdown():
    await close_db()


@app.get("/api/health")
async def api_health():
    """健康检查：返回版本、后端状态、降级信息"""
    cache = get_cache()
    health = {
        "version": app.version,
        "cache_backend": cache.backend,
        "task_store_backend": _backend_name(_task_store),
        "rate_limiter_backend": _ratelimiter_backend_name(_rate_limiter),
        "database_backend": db_backend(),
    }
    degraded_reasons = []
    if isinstance(_task_store, RedisTaskStore) and _task_store.is_degraded:
        degraded_reasons.append("task_store: redis degraded, using memory fallback")
    if isinstance(_rate_limiter, RedisRateLimiter) and _rate_limiter.is_degraded:
        degraded_reasons.append("rate_limiter: redis degraded, using memory fallback")
    if is_degraded():
        degraded_reasons.append("database: postgresql unavailable, using memory mode")
    if degraded_reasons:
        health["degraded"] = degraded_reasons
    return JSONResponse(health)


@app.get("/", response_class=HTMLResponse)
async def index():
    """Web 界面首页"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>bazi-pro — 八字命理解读引擎</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#111122;--surface:#1a1a2e;--surface2:#22223a;--ink:#e0dcc8;
  --muted:#666;--accent:#c4a86c;--border:#333;--radius:12px}
body{font-family:system-ui,sans-serif;background:var(--bg);color:var(--ink);
  line-height:1.6;min-height:100vh;display:flex;flex-direction:column;align-items:center}
.container{max-width:720px;width:100%;padding:40px 20px}
.hero{text-align:center;margin-bottom:40px}
.hero h1{font-size:48px;color:var(--accent);margin-bottom:8px;letter-spacing:4px}
.hero p{color:var(--muted);font-size:16px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  padding:24px;margin-bottom:16px}
.card h2{font-size:18px;margin-bottom:12px;color:var(--accent)}
textarea{width:100%;min-height:200px;background:var(--surface2);color:var(--ink);
  border:1px solid var(--border);border-radius:8px;padding:12px;font-family:monospace;font-size:13px;resize:vertical}
.btn{display:inline-block;padding:10px 24px;background:var(--accent);color:#111;
  border:none;border-radius:20px;font-size:14px;font-weight:600;cursor:pointer;margin-top:12px;transition:all .2s}
.btn:hover{opacity:0.85}
.btn:disabled{opacity:0.4;cursor:not-allowed}
.status-bar{margin-top:12px;padding:8px 16px;background:var(--surface2);border-radius:8px;font-size:13px;color:var(--muted)}
.result-box{margin-top:16px;padding:16px;background:var(--surface2);border-radius:8px;
  font-size:13px;white-space:pre-wrap;max-height:400px;overflow-y:auto;display:none}
.api-link{text-align:center;margin-top:20px}
.api-link a{color:var(--accent);font-size:13px;text-decoration:none}
.api-link a:hover{text-decoration:underline}
</style>
</head>
<body>
<div class="container">
<div class="hero">
<h1>bazi-pro</h1>
<p>专业八字命理解读引擎 · AI Agent Skill v5.0</p>
</div>

<div class="card">
<h2>上传八字 JSON 数据</h2>
<p style="font-size:13px;color:var(--muted);margin-bottom:12px">粘贴 Bazi MCP 返回的 JSON 数据（含八字、日主、性别等字段）</p>
<textarea id="mcpInput" placeholder='{"性别":"女","阳历":"2002-05-19 06:14","农历":"壬午年四月初八","八字":"壬午 乙巳 丁亥 癸卯","日主":"丁","生肖":"马"}'></textarea>
<div style="margin-top:8px">
<label style="font-size:13px;color:var(--muted)">API Key（如服务端已设置鉴权，请填写）</label>
<input id="apiKeyInput" type="password" placeholder="留空则不发送" style="width:100%;padding:8px;background:var(--surface2);color:var(--ink);border:1px solid var(--border);border-radius:8px;margin-top:4px;font-size:13px" />
</div>
<button class="btn" id="analyzeBtn" onclick="startAnalysis()">开始分析</button>
<div class="status-bar" id="statusBar">等待输入...</div>
<div class="result-box" id="resultBox"></div>
</div>

<div class="api-link">
<a href="/docs">API 文档 (Swagger)</a> |
<a href="/redoc">API 文档 (ReDoc)</a>
</div>
<p style="text-align:center;margin-top:16px;font-size:11px;color:var(--muted)">⚠️ 免责声明：本服务仅供传统文化学习与参考，分析结果不构成任何决策依据。输出包含规则推导、古籍检索和 LLM 辅助解释，请勿视为确定性事实。</p>
</div>

<script>
let ws = null;
function getApiKey() {
    return document.getElementById('apiKeyInput').value.trim();
}
function authHeaders() {
    var h = {'Content-Type': 'application/json'};
    var key = getApiKey();
    if (key) h['X-API-Key'] = key;
    return h;
}
async function startAnalysis() {
    var btn = document.getElementById('analyzeBtn');
    var status = document.getElementById('statusBar');
    var result = document.getElementById('resultBox');
    btn.disabled = true;
    status.textContent = '正在提交...';
    result.style.display = 'none';

    try {
        var mcpData = JSON.parse(document.getElementById('mcpInput').value);
        var resp = await fetch('/api/analyze', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(mcpData)
        });
        var data = await resp.json();
        if (resp.status !== 200 && resp.status !== 202) {
            var errMsg = data.error ? data.error.message : (data.detail || JSON.stringify(data));
            status.textContent = '错误: ' + errMsg;
            btn.disabled = false;
            return;
        }
        var runId = data.run_id;
        status.textContent = '分析已启动 (ID: ' + runId + ')，正在连接 WebSocket...';

        var protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        var wsUrl = protocol + '//' + location.host + '/ws/' + runId;
        ws = new WebSocket(wsUrl, [], {headers: {'x-api-key': getApiKey()}});
        ws.onmessage = function(e) {
            var msg = JSON.parse(e.data);
            status.textContent = 'Step ' + msg.step + ': ' + msg.summary;
            if (msg.status === 'done' && msg.step === '9') {
                status.textContent = '分析完成！获取结果中...';
                fetchResult(runId);
            }
        };
        ws.onerror = function() {
            status.textContent = 'WebSocket 连接失败，正在轮询...';
            pollStatus(runId);
        };
    } catch(e) {
        status.textContent = '错误: ' + e.message;
        btn.disabled = false;
    }
}

async function fetchResult(runId) {
    var resp = await fetch('/api/result/' + runId, {headers: authHeaders()});
    var data = await resp.json();
    var result = document.getElementById('resultBox');
    result.textContent = JSON.stringify(data, null, 2);
    result.style.display = 'block';
    document.getElementById('analyzeBtn').disabled = false;
}

async function pollStatus(runId) {
    var interval = setInterval(async function() {
        var resp = await fetch('/api/status/' + runId, {headers: authHeaders()});
        var data = await resp.json();
        document.getElementById('statusBar').textContent = '状态: ' + data.status;
        if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(interval);
            fetchResult(runId);
        }
    }, 2000);
}
</script>
</div>
</body>
</html>"""


@app.post("/api/analyze")
async def api_analyze(
    payload: BaziAnalysisRequest,
    request: Request,
    _auth=Depends(_verify_auth),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """接收 MCP JSON，启动后台分析

    请求体示例:
    {
        "性别": "女",
        "阳历": "2002-05-19 06:14",
        "八字": "壬午 乙巳 丁亥 癸卯",
        "日主": "丁",
        "detail_level": "standard"
    }
    """
    _cleanup_expired_tasks()

    if _task_store.count_active() >= _MAX_CONCURRENT_TASKS:
        return error_response(503, "SERVER_BUSY", "服务繁忙，请稍后重试")

    auth_header = request.headers.get("Authorization", "")
    is_jwt = auth_header.startswith("Bearer ")

    if is_jwt and _auth is not None:
        user_id = _auth.get("sub") if isinstance(_auth, dict) else None
        if user_id:
            quota = await check_quota(user_id, db)
            if not quota.allowed:
                return error_response(402, "QUOTA_EXCEEDED", f"配额不足，当前计划: {quota.plan}，剩余次数: {quota.remaining}")

    run_id = uuid.uuid4().hex
    payload_dict = payload.model_dump()
    detail_level = payload_dict.pop('detail_level', 'standard')

    _task_store.create(run_id, {
        'status': 'queued',
        'created_at': datetime.now(timezone.utc).isoformat(),
        '_created_ts': time.time(),
    })

    user_id_for_quota = None
    if is_jwt and _auth is not None and isinstance(_auth, dict):
        user_id_for_quota = _auth.get("sub")

    asyncio.create_task(_background_analyze(run_id, payload_dict, detail_level, user_id_for_quota, db))

    return JSONResponse({
        'run_id': run_id,
        'status': 'queued',
        'message': '分析任务已提交，通过 WebSocket /ws/{run_id} 获取进度',
    })


@app.get("/api/status/{run_id}")
async def api_status(run_id: str, _auth=Depends(_verify_auth)):
    """查询分析进度"""
    task = _task_store.get(run_id)
    if not task:
        return error_response(404, "NOT_FOUND", "run_id 不存在")
    safe_task = {k: v for k, v in task.items() if not k.startswith('_')}
    return JSONResponse(safe_task)


@app.get("/api/result/{run_id}")
async def api_result(run_id: str, _auth=Depends(_verify_auth)):
    """获取分析结果"""
    task = _task_store.get(run_id)
    if not task:
        return error_response(404, "NOT_FOUND", "run_id 不存在")

    if task['status'] == 'failed':
        return JSONResponse({
            'status': 'failed',
            'error': task.get('error', '未知错误'),
            'run_id': run_id,
        })

    cache = get_cache()
    result = cache.get(f'result:{run_id}')
    if result:
        return JSONResponse(result)

    return JSONResponse({
        'status': task['status'],
        'run_id': run_id,
        'message': '分析尚未完成',
    })


@app.get("/api/history")
async def api_history(current_user: User = Depends(get_current_user), limit: int = 50, offset: int = 0):
    user_id = str(current_user.id)

    records = await get_user_analyses(user_id, limit=limit, offset=offset)
    return JSONResponse({"history": records, "source": db_backend(), "total": len(records)})


@app.websocket("/ws/{run_id}")
async def ws_connect(ws: WebSocket, run_id: str):
    if _API_KEY:
        api_key = ws.headers.get('x-api-key', '') or ''
        if not hmac.compare_digest(api_key, _API_KEY):
            await ws.close(code=4001, reason='Invalid API key')
            return
    if not _task_store.get(run_id):
        await ws.close(code=4004, reason='run_id not found')
        return
    await ws.accept()
    manager.add_accepted(run_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(run_id, ws)
    except Exception:
        manager.disconnect(run_id, ws)


async def _background_analyze(run_id: str, mcp_json: dict, detail_level: str, user_id: Optional[str] = None, db: Optional[AsyncSession] = None):
    """后台执行分析"""
    _task_store.update(run_id, {'status': 'running'})
    try:
        result = await run_analysis(mcp_json, run_id, detail_level)
        _task_store.update(run_id, {'status': result.get('status', 'completed')})
        cache = get_cache()
        cache.set(f'result:{run_id}', result, ttl=_TASK_TTL_SECONDS)

        if user_id and db is not None:
            await deduct_quota(user_id, db)

        await persist_analysis(
            run_id=run_id,
            user_id=user_id or os.environ.get("BAZI_DEFAULT_USER_ID") or None,
            bazi=mcp_json.get('八字', ''),
            day_master=mcp_json.get('日主', ''),
            gender=mcp_json.get('性别', ''),
            solar_date=mcp_json.get('阳历', ''),
            detail_level=detail_level,
            status=result.get('status', 'completed'),
            result=result,
        )
    except Exception as e:
        _task_store.update(run_id, {'status': 'failed'})
        debug = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")
        _task_store.update(run_id, {'error': str(e) if debug else "Internal server error"})
        logger.error("Analysis failed for run_id=%s: %s", run_id, e)

        await persist_analysis(
            run_id=run_id,
            user_id=user_id or os.environ.get("BAZI_DEFAULT_USER_ID") or None,
            bazi=mcp_json.get('八字', ''),
            day_master=mcp_json.get('日主', ''),
            gender=mcp_json.get('性别', ''),
            solar_date=mcp_json.get('阳历', ''),
            detail_level=detail_level,
            status='failed',
            result=None,
        )


def main():
    import uvicorn
    host = os.environ.get("BAZI_HOST", "0.0.0.0")
    port = _get_int_env("BAZI_PORT", 8800)
    log_level = os.environ.get("BAZI_LOG_LEVEL", "info")
    workers = _get_int_env("BAZI_WORKERS", 1)
    if os.environ.get("DEBUG", "").lower() in ("1", "true", "yes"):
        logger.warning("⚠️  DEBUG mode is enabled — do not use in production!")

    _static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if os.path.isdir(_static_dir) and os.path.exists(os.path.join(_static_dir, 'index.html')):
        app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
        logger.info("Serving frontend static files from %s", _static_dir)

    uvicorn.run(app, host=host, port=port, log_level=log_level, workers=workers)


if __name__ == '__main__':
    main()
