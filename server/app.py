#!/usr/bin/env python3
"""
bazi-pro FastAPI 应用 v5.0
API 路由：分析、状态查询、结果获取、仪表盘
"""

import asyncio
import hmac
import json
import logging
import os
import re
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from fastapi import Depends, FastAPI, Query, Request, Security, WebSocket, WebSocketDisconnect  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.middleware.trustedhost import TrustedHostMiddleware  # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse  # noqa: E402
from fastapi.security import APIKeyHeader  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from server.analysis import run_analysis  # noqa: E402
from server.cache import get_cache  # noqa: E402
from server.dayun_score import score_dayun, score_liunian  # noqa: E402
from server.db import (  # noqa: E402
    close_db,
    generate_analysis_id,
    get_analysis,
    get_chat_messages,
    get_db,
    get_report,
    insert_analysis,
    insert_chat_message,
    list_analyses,
    save_report,
    update_analysis_result,
    update_analysis_status,
)
from server.llm import (  # noqa: E402
    build_chat_system_prompt,
    build_report_system_prompt,
    chat_completion,
    get_llm_config,
    is_llm_configured,
    update_llm_config,
)
from server.rag_engine import retrieve_for_chat, retrieve_for_report  # noqa: E402
from server.ratelimiter import MemoryRateLimiter, RateLimiter, RedisRateLimiter, create_rate_limiter  # noqa: E402
from server.schemas import BaziAnalysisRequest  # noqa: E402
from server.taskstore import MemoryTaskStore, RedisTaskStore, create_task_store  # noqa: E402
from server.ws import manager  # noqa: E402

logger = logging.getLogger("bazi-pro")

_ANALYSIS_ID_PATTERN = re.compile(r'^ana_[0-9a-f]{8,24}$')


def _validate_analysis_id(analysis_id: str) -> bool:
    """Validate analysis_id format to prevent injection."""
    return bool(_ANALYSIS_ID_PATTERN.match(analysis_id))


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


@asynccontextmanager
async def _lifespan(app: FastAPI):
    await get_db()
    yield
    await close_db()


app = FastAPI(
    title="bazi-pro API",
    description="专业八字命理解读引擎 Web 服务\n\n⚠️ 免责声明：本服务仅供传统文化学习与参考，分析结果不构成任何决策依据。命理解释包含规则推导、古籍检索和 LLM 辅助解释，请勿将模型输出视为确定性事实。",
    version="5.0.0",
    lifespan=_lifespan,
    docs_url="/docs" if _enable_docs else None,
    redoc_url="/redoc" if _enable_docs else None,
    openapi_url="/openapi.json" if _enable_docs else None,
)

_cors_origins_str = os.environ.get('BAZI_CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
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
    allow_headers=["Content-Type", "X-API-Key"],
)

if not _cors_origins:
    logger.warning("BAZI_CORS_ORIGINS not set — CORS disabled. Set BAZI_CORS_ORIGINS=* or comma-separated origins.")

_allowed_hosts_str = os.environ.get('BAZI_ALLOWED_HOSTS', '')
if _allowed_hosts_str:
    _allowed_hosts = [h.strip() for h in _allowed_hosts_str.split(',') if h.strip()]
else:
    # Default: localhost only for dev. Set BAZI_ALLOWED_HOSTS in production.
    _allowed_hosts = ['localhost', '127.0.0.1', 'testserver']
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


class _APIKeyError(Exception):
    pass


@app.exception_handler(_APIKeyError)
async def _api_key_error_handler(request, exc):
    return error_response(401, "UNAUTHORIZED", "API key 无效或缺失")


async def _verify_api_key(request: Request, api_key: str = Security(_api_key_scheme)):
    if not _API_KEY:
        if os.environ.get('ENV', '').lower() in ('prod', 'production'):
            logger.error("API key not configured in production environment!")
            raise _APIKeyError()
        return True
    if api_key and hmac.compare_digest(api_key, _API_KEY):
        return True
    # SSE/EventSource 无法发送自定义 Header，支持通过查询参数传递 token
    token = request.query_params.get("token", "")
    if token and hmac.compare_digest(token, _API_KEY):
        return True
    raise _APIKeyError()


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
    error_id = uuid.uuid4().hex[:8]
    logger.error("[%s] Unhandled %s: %s", error_id, exc.__class__.__name__, exc, exc_info=True)
    debug = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")
    message = f"{exc} (error_id={error_id})" if debug else f"服务器内部错误 (error_id={error_id})"
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


@app.get("/api/health")
async def api_health():
    """健康检查：返回版本、后端状态、降级信息"""
    cache = get_cache()
    health = {
        "version": app.version,
        "cache_backend": cache.backend,
        "task_store_backend": _backend_name(_task_store),
        "rate_limiter_backend": _ratelimiter_backend_name(_rate_limiter),
    }
    degraded_reasons = []
    if isinstance(_task_store, RedisTaskStore) and _task_store.is_degraded:
        degraded_reasons.append("task_store: redis degraded, using memory fallback")
    if isinstance(_rate_limiter, RedisRateLimiter) and _rate_limiter.is_degraded:
        degraded_reasons.append("rate_limiter: redis degraded, using memory fallback")
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
async def api_analyze(payload: BaziAnalysisRequest, _auth=Depends(_verify_api_key)):
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

    run_id = uuid.uuid4().hex
    payload_dict = payload.model_dump()
    detail_level = payload_dict.pop('detail_level', 'standard')

    _task_store.create(run_id, {
        'status': 'queued',
        'created_at': datetime.now(timezone.utc).isoformat(),
        '_created_ts': time.time(),
    })

    asyncio.create_task(_background_analyze(run_id, payload_dict, detail_level))

    return JSONResponse({
        'run_id': run_id,
        'status': 'queued',
        'message': '分析任务已提交，通过 WebSocket /ws/{run_id} 获取进度',
    })


@app.get("/api/status/{run_id}")
async def api_status(run_id: str, _auth=Depends(_verify_api_key)):
    """查询分析进度"""
    task = _task_store.get(run_id)
    if not task:
        return error_response(404, "NOT_FOUND", "run_id 不存在")
    safe_task = {k: v for k, v in task.items() if not k.startswith('_')}
    return JSONResponse(safe_task)


@app.get("/api/result/{run_id}")
async def api_result(run_id: str, _auth=Depends(_verify_api_key)):
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


@app.websocket("/ws/{run_id}")
async def ws_connect(ws: WebSocket, run_id: str):
    if _API_KEY:
        api_key = ws.headers.get('x-api-key', '') or ''
        # WebSocket 不支持自定义 headers，支持通过查询参数传递 token
        token = ws.query_params.get("token", "") if hasattr(ws, "query_params") else ""
        if not (api_key and hmac.compare_digest(api_key, _API_KEY)) and not (token and hmac.compare_digest(token, _API_KEY)):
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


async def _background_analyze(run_id: str, mcp_json: dict, detail_level: str):
    """后台执行分析"""
    _task_store.update(run_id, {'status': 'running'})
    try:
        result = await run_analysis(mcp_json, run_id, detail_level)
        if result is None:
            result = {"status": "failed", "error": "分析引擎返回空结果"}
        # 从 result 中提取真实状态：若分析内部失败，status 为 'failed'
        actual_status = result.get('status', 'completed')
        _task_store.update(run_id, {'status': actual_status})
        cache = get_cache()
        cache.set(f'result:{run_id}', result, ttl=_TASK_TTL_SECONDS)
    except Exception as e:
        _task_store.update(run_id, {
            'status': 'failed',
            'error': str(e) if os.environ.get("DEBUG", "").lower() in ("1", "true", "yes") else "Internal server error",
        })
        logger.error("Analysis failed for run_id=%s: %s", run_id, e)


# ─── P0 Frontend API Routes ─────────────────────────────────────────────────

_sse_subscribers: dict[str, list[asyncio.Queue]] = {}
_sse_buffers: dict[str, list[str]] = {}
_v2_active_ids: set[str] = set()
_sse_lock = asyncio.Lock()
_SSE_BUFFER_MAX = 100


_original_ws_send_progress = manager.send_progress


async def _ws_send_with_sse(run_id, step, status, summary='', data=None):
    await _original_ws_send_progress(run_id, step, status, summary, data)
    if run_id in _v2_active_ids:
        await _sse_broadcast(run_id, "progress", {
            "step": step, "name": summary, "status": status, "message": summary,
        })


manager.send_progress = _ws_send_with_sse


class BirthAnalyzeRequest(BaseModel):
    性别: str = Field(..., description="性别: 男/女")
    八字: str = Field(..., description="四柱八字，空格分隔")
    日主: str = Field(..., description="日主天干")
    阳历: Optional[str] = Field(default="", description="阳历日期时间")
    农历: Optional[str] = Field(default="", description="农历日期")
    生肖: Optional[str] = Field(default="", description="生肖")
    大运: Optional[list] = Field(default=None, description="大运列表")
    detail_level: str = Field(default="standard")
    longitude: Optional[float] = Field(default=None, description="出生地经度")
    latitude: Optional[float] = Field(default=None, description="出生地纬度")
    school: Optional[str] = Field(default="ziping", description="解读流派: ziping/ziwei/qiongtong")


class PaipanRequest(BaseModel):
    性别: str = Field(..., description="性别: 男/女")
    阳历: str = Field(..., description="阳历日期时间，如 2002-05-19 06:14")
    农历: Optional[str] = Field(default="", description="农历日期")


class ChatRequest(BaseModel):
    analysis_id: str = Field(..., description="分析记录 ID")
    message: str = Field(..., description="用户消息")
    school: str = Field(default="ziping", description="派别视角: ziping/mangpai/xinpai")
    retrieval_depth: str = Field(default="enhanced", description="检索深度: basic/enhanced")


class ReportRequest(BaseModel):
    analysis_id: str = Field(..., description="分析记录 ID")
    school: str = Field(default="ziping", description="派别视角: ziping/mangpai/xinpai")
    retrieval_depth: str = Field(default="enhanced", description="检索深度: basic/enhanced")


@app.post("/api/v2/paipan")
async def api_v2_paipan(payload: PaipanRequest):
    """排盘 API — 根据出生时间生成八字四柱"""
    try:
        from bazi_pro.paipan import paipan_from_datetime
        solar = payload.阳历 or ""
        result = paipan_from_datetime(solar, payload.性别, payload.农历 or "")
        return JSONResponse(result)
    except Exception as e:
        return error_response(400, "PAIPAN_ERROR", str(e))


@app.get("/api/v2/cities")
async def api_v2_cities():
    """返回支持真太阳时校正的城市列表"""
    from server.true_solar_time import CHINA_CITIES
    cities = [{"name": name, "longitude": coords[0], "latitude": coords[1]}
              for name, coords in CHINA_CITIES.items()]
    return JSONResponse(content={"cities": cities})


@app.post("/api/v2/analyze")
async def api_v2_analyze(payload: BirthAnalyzeRequest):
    """P0 前端分析入口 — 存储到 SQLite + SSE 流式"""
    analysis_id = generate_analysis_id()
    payload_dict = payload.model_dump(exclude_none=True)
    detail_level = payload_dict.pop("detail_level", "standard")
    school = payload_dict.pop("school", "ziping")
    longitude = payload_dict.pop("longitude", None)
    payload_dict.pop("latitude", None)

    if longitude is not None and payload_dict.get("阳历"):
        from datetime import datetime as _dt

        from server.true_solar_time import correct_to_true_solar_time
        try:
            solar_str = payload_dict["阳历"] or ""
            if solar_str:
                solar_dt = _dt.fromisoformat(solar_str.replace("/", "-").replace(" ", "T"))
                corrected = correct_to_true_solar_time(solar_dt, longitude)
                payload_dict["阳历"] = corrected.strftime("%Y-%m-%d %H:%M")
                payload_dict["真太阳时校正"] = True
        except (ValueError, TypeError):
            pass

    await insert_analysis(analysis_id, payload_dict, detail_level)

    _sse_subscribers[analysis_id] = []
    _sse_buffers[analysis_id] = []

    asyncio.create_task(_background_analyze_v2(analysis_id, payload_dict, detail_level, school))

    return JSONResponse(
        status_code=202,
        content={
            "analysis_id": analysis_id,
            "status": "processing",
            "stream_url": f"/api/v2/analysis/{analysis_id}/stream",
        },
    )


class CompareRequest(BaseModel):
    八字: str = Field(..., description="四柱八字，空格分隔")
    日主: str = Field(..., description="日主天干")
    性别: str = Field(default="男", description="性别: 男/女")
    出生年: Optional[int] = Field(default=None, description="出生年份")
    出生月: Optional[int] = Field(default=None, description="出生月份")
    出生日: Optional[int] = Field(default=None, description="出生日期")


@app.post("/api/v2/analyze/compare")
async def api_v2_analyze_compare(payload: CompareRequest):
    """三流派对比分析 — 同时返回子平/盲派/新派分析结果"""
    try:
        from bazi_pro.core.schools import school_analyze
    except ImportError:
        return error_response(503, "SCHOOL_NOT_AVAILABLE", "流派分析模块不可用")

    mcp_json = {
        "八字": payload.八字,
        "日主": payload.日主,
        "性别": payload.性别,
    }
    if payload.出生年:
        mcp_json["出生年"] = payload.出生年
    if payload.出生月:
        mcp_json["出生月"] = payload.出生月
    if payload.出生日:
        mcp_json["出生日"] = payload.出生日

    try:
        results = school_analyze(mcp_json, "all")
        return JSONResponse({
            "status": "completed",
            "schools": results,
        })
    except Exception as e:
        logger.error("Compare analysis failed: %s", e)
        return error_response(500, "ANALYSIS_ERROR", f"分析失败: {str(e)}")


class HehunRequest(BaseModel):
    八字A: str = Field(description="甲方八字，空格分隔四柱")
    日主A: str = Field(description="甲方日主天干")
    性别A: str = Field(description="甲方性别")
    八字B: str = Field(description="乙方八字，空格分隔四柱")
    日主B: str = Field(description="乙方日主天干")
    性别B: str = Field(description="乙方性别")


@app.post("/api/v2/hehun")
async def api_v2_hehun(payload: HehunRequest):
    """合婚分析 — 两人八字兼容性评估"""
    try:
        from bazi_pro.compare_engine import CompareEngine
        from bazi_pro.core import full_analysis
    except ImportError:
        return error_response(503, "MODULE_NOT_AVAILABLE", "合婚模块不可用")

    try:
        chart_a = full_analysis({"八字": payload.八字A, "日主": payload.日主A, "性别": payload.性别A})
        chart_b = full_analysis({"八字": payload.八字B, "日主": payload.日主B, "性别": payload.性别B})

        engine = CompareEngine()
        engine.load_chart_a_dict(chart_a)
        engine.load_chart_b_dict(chart_b)
        result = engine.compare()

        from dataclasses import asdict
        return JSONResponse({"status": "completed", "result": asdict(result)})
    except Exception as e:
        logger.error("Hehun analysis failed: %s", e)
        return error_response(500, "ANALYSIS_ERROR", f"合婚分析失败: {str(e)}")


@app.get("/api/v2/fortune/daily/{analysis_id}")
async def api_v2_daily_fortune(analysis_id: str):
    """每日运势 — 基于已有分析结果的日主和用神"""
    from datetime import date as _date

    from server.daily_fortune import calc_daily_fortune

    analysis = await get_analysis(analysis_id)
    if not analysis:
        return error_response(404, "NOT_FOUND", "分析不存在")

    result = analysis.get("full_result", {})
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}
    if not isinstance(result, dict):
        result = {}

    # day_master: full_analysis() 在顶层，run_analysis() 在 validation 下
    day_master = result.get("day_master", "") or result.get("validation", {}).get("day_master", "")
    yongshen_data = result.get("yongshen", {})

    yongshen_wx = yongshen_data.get("yongshen", "")
    jishen_wx = yongshen_data.get("jishen", [])
    # 确保 jishen_wx 是列表（防止旧数据中存储为字符串）
    if isinstance(jishen_wx, str):
        jishen_wx = [jishen_wx] if jishen_wx else []

    if not day_master:
        return error_response(400, "INVALID", "缺少日主数据")

    fortune = calc_daily_fortune(day_master, yongshen_wx, jishen_wx, _date.today())
    return JSONResponse(fortune)


@app.get("/api/v2/fortune/monthly/{analysis_id}")
async def api_v2_monthly_fortune(analysis_id: str, year: int = Query(default=0), month: int = Query(default=0)):
    """每月运势"""
    from datetime import date as _date

    from server.daily_fortune import calc_monthly_fortune

    if not year:
        year = _date.today().year
    if not month:
        month = _date.today().month

    analysis = await get_analysis(analysis_id)
    if not analysis:
        return error_response(404, "NOT_FOUND", "分析不存在")

    result = analysis.get("full_result", {})
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}
    if not isinstance(result, dict):
        result = {}

    # day_master: full_analysis() 在顶层，run_analysis() 在 validation 下
    day_master = result.get("day_master", "") or result.get("validation", {}).get("day_master", "")
    yongshen_data = result.get("yongshen", {})

    yongshen_wx = yongshen_data.get("yongshen", "")
    jishen_wx = yongshen_data.get("jishen", [])
    if isinstance(jishen_wx, str):
        jishen_wx = [jishen_wx] if jishen_wx else []

    if not day_master:
        return error_response(400, "INVALID", "缺少日主数据")

    fortune = calc_monthly_fortune(day_master, yongshen_wx, jishen_wx, year, month)
    return JSONResponse(fortune)


class ReverseLookupRequest(BaseModel):
    day_pillar: str = Field(description="日柱干支，如 '戊辰'")
    start_year: int = Field(default=2020)
    end_year: int = Field(default=2030)


@app.post("/api/v2/reverse-lookup")
async def api_v2_reverse_lookup(payload: ReverseLookupRequest):
    """四柱反查 — 根据日柱反推可能的出生日期"""
    from server.reverse_lookup import reverse_lookup_day_pillar

    results = reverse_lookup_day_pillar(payload.day_pillar, payload.start_year, payload.end_year)
    return JSONResponse({"dates": results, "day_pillar": payload.day_pillar})


# ── 紫微斗数端点 ──────────────────────────────────────────────

class ZiweiChartRequest(BaseModel):
    """紫微斗数排盘请求"""
    solar_date: str = Field(..., description="阳历出生日期，格式 YYYY-MM-DD")
    hour: int = Field(..., ge=0, le=23, description="出生小时(0-23)")
    gender: int = Field(default=1, description="性别：1=男，0=女")


class ZiweiHoroscopeRequest(BaseModel):
    """紫微斗数运势查询请求"""
    solar_date: str = Field(..., description="阳历出生日期，格式 YYYY-MM-DD")
    hour: int = Field(..., ge=0, le=23, description="出生小时(0-23)")
    gender: int = Field(default=1, description="性别：1=男，0=女")
    query_date: Optional[str] = Field(default=None, description="查询日期，格式 YYYY-MM-DD，默认今天")


class ZiweiPalaceRequest(BaseModel):
    """紫微斗数宫位分析请求"""
    solar_date: str = Field(..., description="阳历出生日期，格式 YYYY-MM-DD")
    hour: int = Field(..., ge=0, le=23, description="出生小时(0-23)")
    gender: int = Field(default=1, description="性别：1=男，0=女")
    palace_name: str = Field(default="命宫", description="宫位名称")


@app.post("/api/v2/ziwei/chart")
async def api_v2_ziwei_chart(payload: ZiweiChartRequest):
    """紫微斗数排盘 — 生成完整十二宫命盘"""
    from server.ziwei import get_ziwei_chart

    result = await asyncio.to_thread(
        get_ziwei_chart,
        solar_date=payload.solar_date,
        hour=payload.hour,
        gender=payload.gender,
    )
    if "error" in result:
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


@app.post("/api/v2/ziwei/horoscope")
async def api_v2_ziwei_horoscope(payload: ZiweiHoroscopeRequest):
    """紫微斗数运势 — 查询大限/流年/流月/流日/流时"""
    from server.ziwei import get_ziwei_horoscope

    result = await asyncio.to_thread(
        get_ziwei_horoscope,
        solar_date=payload.solar_date,
        hour=payload.hour,
        gender=payload.gender,
        query_date=payload.query_date,
    )
    if "error" in result:
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


@app.post("/api/v2/ziwei/palace")
async def api_v2_ziwei_palace(payload: ZiweiPalaceRequest):
    """紫微斗数宫位分析 — 分析特定宫位详细信息"""
    from server.ziwei import analyze_ziwei_palace

    result = await asyncio.to_thread(
        analyze_ziwei_palace,
        solar_date=payload.solar_date,
        hour=payload.hour,
        gender=payload.gender,
        palace_name=payload.palace_name,
    )
    if "error" in result:
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


async def _background_analyze_v2(analysis_id: str, mcp_json: dict, detail_level: str, school: str = 'ziping'):
    """P0 后台分析 — 发送 SSE 事件 + 存储结果"""
    for key in list(mcp_json.keys()):
        if mcp_json[key] is None:
            mcp_json[key] = ''

    _v2_active_ids.add(analysis_id)
    try:
        await _sse_broadcast(analysis_id, "progress", {
            "step": "0", "name": "启动分析", "status": "running", "message": "正在初始化..."
        })

        result = await run_analysis(mcp_json, analysis_id, detail_level, school)

        if result is None:
            result = {"status": "failed", "error": "分析引擎返回空结果"}

        await update_analysis_result(analysis_id, result)

        # 根据分析结果的实际状态决定发送哪种 SSE 事件
        actual_status = result.get('status', 'completed')
        if actual_status == 'failed':
            error_msg = result.get('error', '分析失败')
            await _sse_broadcast(analysis_id, "analysis-error", {"message": error_msg})
        elif actual_status == 'invalid_input':
            errors = result.get('errors', [])
            error_msg = '; '.join(errors) if isinstance(errors, list) and errors else result.get('error', '输入数据无效')
            await _sse_broadcast(analysis_id, "analysis-error", {"message": error_msg})
        else:
            await _sse_broadcast(analysis_id, "done", {"analysis_id": analysis_id})

    except Exception as e:
        import traceback as _tb
        logger.error("V2 analysis failed for %s: %s\n%s", analysis_id, e, _tb.format_exc())
        client_msg = str(e) or type(e).__name__
        await update_analysis_status(analysis_id, "failed", client_msg)
        await _sse_broadcast(analysis_id, "analysis-error", {"message": client_msg})
    finally:
        _v2_active_ids.discard(analysis_id)
        # 等待订阅者自行退出后再清理，最多等 5 秒
        for _ in range(10):
            async with _sse_lock:
                subs = _sse_subscribers.get(analysis_id, [])
                if not subs:
                    _sse_subscribers.pop(analysis_id, None)
                    _sse_buffers.pop(analysis_id, None)
                    break
            await asyncio.sleep(0.5)
        else:
            # 超时仍有订阅者，强制清理
            async with _sse_lock:
                _sse_subscribers.pop(analysis_id, None)
                _sse_buffers.pop(analysis_id, None)


async def _sse_broadcast(analysis_id: str, event: str, data: dict):
    """向所有订阅该 analysis_id 的 SSE 客户端广播事件，同时缓存"""
    msg = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
    async with _sse_lock:
        buf = _sse_buffers.get(analysis_id)
        if buf is not None:
            buf.append(msg)
            if len(buf) > _SSE_BUFFER_MAX:
                del buf[:len(buf) - _SSE_BUFFER_MAX]
        queues = list(_sse_subscribers.get(analysis_id, []))
    for q in queues:
        await q.put(msg)


@app.get("/api/v2/analysis/{analysis_id}/stream")
async def api_v2_stream(analysis_id: str, _auth=Depends(_verify_api_key)):
    """SSE 流式端点 — 实时推送分析进度（含缓冲回放）"""
    queue: asyncio.Queue = asyncio.Queue()

    async with _sse_lock:
        buffered = _sse_buffers.get(analysis_id, [])
        for msg in buffered:
            await queue.put(msg)

        if analysis_id not in _sse_subscribers:
            _sse_subscribers[analysis_id] = []
        _sse_subscribers[analysis_id].append(queue)

    already_done = any(m.startswith("event: done") or m.startswith("event: analysis-error") for m in buffered)

    async def event_generator():
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield msg
                    if msg.startswith("event: done") or msg.startswith("event: analysis-error"):
                        break
                except asyncio.TimeoutError:
                    if already_done:
                        break
                    yield ": keepalive\n\n"
        finally:
            async with _sse_lock:
                subs = _sse_subscribers.get(analysis_id, [])
                if queue in subs:
                    subs.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/v2/analysis/{analysis_id}")
async def api_v2_get_analysis(analysis_id: str):
    """获取分析完整结果"""
    if not _validate_analysis_id(analysis_id):
        return error_response(400, "INVALID_FORMAT", "analysis_id 格式不合法")
    record = await get_analysis(analysis_id)
    if not record:
        return error_response(404, "NOT_FOUND", "分析记录不存在")

    result = record.get("full_result")
    if not result:
        return JSONResponse({
            "analysis_id": analysis_id,
            "status": record["status"],
            "message": "分析尚未完成" if record["status"] == "processing" else "无结果数据",
        })

    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            pass

    if isinstance(result, dict) and result.get("status") == "completed" and "tiaohou" not in result:
        try:
            from bazi_pro.core.tiaohou import lookup_tiaohou
            # day_master: full_analysis() 在顶层，run_analysis() 在 validation 下
            day_master = result.get("day_master", "") or result.get("validation", {}).get("day_master", "")
            # pillars: full_analysis() 在顶层，run_analysis() 在 shishen 下
            pillars = result.get("pillars", []) or result.get("shishen", {}).get("pillars", [])
            bazi_parts = [p.get("gan", "") + p.get("zhi", "") for p in pillars]
            month_zhi = bazi_parts[1][1] if len(bazi_parts) >= 2 and len(bazi_parts[1]) >= 2 else ""
            if day_master and month_zhi:
                result["tiaohou"] = lookup_tiaohou(day_master, month_zhi)
        except Exception:
            pass

    narration = {}
    if isinstance(result, dict) and result.get("status") == "completed":
        try:
            from bazi_pro.narrator import narrate_analysis
            narration = narrate_analysis(result)
        except Exception:
            pass

    effective_status = record["status"]
    effective_error = None
    if isinstance(result, dict):
        if "status" in result:
            effective_status = result["status"]
        if "error" in result:
            effective_error = result["error"]

    response = {
        "analysis_id": analysis_id,
        "status": effective_status,
        "created_at": record.get("created_at"),
        "completed_at": record.get("completed_at"),
        "day_master": record.get("day_master", ""),
        "pattern": record.get("pattern", ""),
        "yongshen": record.get("yongshen", ""),
        "result": result,
        "narration": narration,
    }
    if effective_error:
        response["error"] = effective_error
    return JSONResponse(response)


@app.get("/api/v2/dayun-liunian/{analysis_id}")
async def api_v2_dayun_liunian(analysis_id: str):
    record = await get_analysis(analysis_id)
    if not record:
        return error_response(404, "NOT_FOUND", "分析记录不存在")

    result = record.get("full_result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}

    if not isinstance(result, dict) or result.get("status") != "completed":
        return error_response(400, "ANALYSIS_NOT_COMPLETED", "分析尚未完成，无法获取大运流年评分")

    dayun_list = result.get("dayun", [])
    qiyun_age = result.get("qiyun_age", 5)

    yongshen_info = result.get("yongshen", {})
    if isinstance(yongshen_info, dict):
        yongshen_wx = yongshen_info.get("yongshen", "")
        jishen_wx = yongshen_info.get("jishen", [])
        xishen_wx = yongshen_info.get("xishen", [])
        if isinstance(jishen_wx, str):
            jishen_wx = [jishen_wx] if jishen_wx else []
        if isinstance(xishen_wx, str):
            xishen_wx = [xishen_wx] if xishen_wx else []
    else:
        if isinstance(yongshen_info, list) and yongshen_info:
            yongshen_wx = str(yongshen_info[0]) if yongshen_info[0] else ""
        elif isinstance(yongshen_info, str):
            yongshen_wx = yongshen_info
        else:
            yongshen_wx = str(yongshen_info) if yongshen_info else ""
        jishen_wx = []
        xishen_wx = []

    # day_master: full_analysis() 在顶层，run_analysis() 在 validation 下
    day_master = result.get("day_master", "") or result.get("validation", {}).get("day_master", "")
    if not day_master:
        day_master = record.get("day_master", "")

    birth_json = record.get("birth_json", {})
    if isinstance(birth_json, str):
        try:
            birth_json = json.loads(birth_json)
        except (json.JSONDecodeError, TypeError):
            birth_json = {}

    birth_year = None
    solar = birth_json.get("阳历", "")
    if solar:
        try:
            birth_year = int(solar.split("-")[0])
        except (ValueError, IndexError):
            birth_year = None

    if not dayun_list or not yongshen_wx or not birth_year:
        return JSONResponse({
            "analysis_id": analysis_id,
            "dayun_scores": [],
            "liunian_scores": [],
            "warning": "缺少大运、用神或出生年份数据，无法评分",
        })

    dayun_scores = score_dayun(dayun_list, yongshen_wx, jishen_wx, day_master)
    liunian_scores = score_liunian(
        dayun_list, yongshen_wx, jishen_wx, xishen_wx, day_master,
        birth_year, qiyun_age,
    )

    return JSONResponse({
        "analysis_id": analysis_id,
        "dayun_scores": dayun_scores,
        "liunian_scores": liunian_scores,
    })


@app.get("/api/v2/history")
async def api_v2_history(page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100)):
    """历史分析记录列表"""
    data = await list_analyses(page=page, page_size=page_size)
    return JSONResponse(data)


@app.post("/api/v2/chat")
async def api_v2_chat(payload: ChatRequest):
    """对话接口 — 基于命盘数据与 LLM 对话"""
    if not is_llm_configured():
        return error_response(503, "LLM_NOT_CONFIGURED", "LLM 服务未配置。请设置 LLM_API_KEY 环境变量。")

    record = await get_analysis(payload.analysis_id)
    if not record:
        return error_response(404, "NOT_FOUND", "分析记录不存在")

    result = record.get("full_result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}

    narration = {}
    if isinstance(result, dict) and result.get("status") == "completed":
        try:
            from bazi_pro.narrator import narrate_analysis
            narration = narrate_analysis(result)
        except Exception:
            pass

    retrieval_results = None
    citations = None
    if payload.retrieval_depth != "basic" and isinstance(result, dict):
        try:
            analysis_context = _extract_analysis_context(result)
            retrieval_results = await asyncio.to_thread(retrieve_for_chat, payload.message, analysis_context, k=5)
            # 只返回格式化后的引用文本给前端，不返回完整检索结构
            from server.rag_engine import _format_retrieval_for_prompt
            citations = _format_retrieval_for_prompt(retrieval_results)
        except Exception as exc:
            logger.warning("RAG retrieval failed for chat %s: %s", payload.analysis_id, exc)

    system_prompt = build_chat_system_prompt(result or {}, narration, school=payload.school, retrieval_results=retrieval_results)

    history = await get_chat_messages(payload.analysis_id, limit=20, school=payload.school)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": payload.message})

    await insert_chat_message(payload.analysis_id, "user", payload.message, school=payload.school)

    try:
        reply = await chat_completion(messages)
        await insert_chat_message(payload.analysis_id, "assistant", reply, citations=citations or "", school=payload.school)
        response_payload = {"reply": reply}
        if citations is not None:
            response_payload["citations"] = citations
        return JSONResponse(response_payload)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error("Chat failed for analysis %s: %s\n%s", payload.analysis_id, e, tb)
        err_msg = str(e) or type(e).__name__
        return error_response(500, "LLM_ERROR", f"LLM 调用失败: {err_msg}")


@app.get("/api/v2/chat/{analysis_id}")
async def api_v2_get_chat(analysis_id: str, school: str = Query(default=None)):
    """获取对话历史"""
    messages = await get_chat_messages(analysis_id, limit=100, school=school)
    return JSONResponse({"messages": messages})


@app.post("/api/v2/report")
async def api_v2_create_report(payload: ReportRequest):
    """生成七维度综合分析报告"""
    if not is_llm_configured():
        return error_response(503, "LLM_NOT_CONFIGURED", "LLM 服务未配置。请设置 LLM_API_KEY 环境变量。")

    record = await get_analysis(payload.analysis_id)
    if not record:
        return error_response(404, "NOT_FOUND", "分析记录不存在")

    if record.get("status") != "completed":
        return error_response(400, "ANALYSIS_NOT_COMPLETED", "分析尚未完成，无法生成报告")

    result = record.get("full_result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}

    if not isinstance(result, dict) or result.get("status") != "completed":
        return error_response(400, "INVALID_RESULT", "分析结果数据异常，无法生成报告")

    narration = {}
    try:
        from bazi_pro.narrator import narrate_analysis
        narration = narrate_analysis(result)
    except Exception:
        pass

    birth_json = record.get("birth_json", {})
    if isinstance(birth_json, str):
        try:
            birth_json = json.loads(birth_json)
        except (json.JSONDecodeError, TypeError):
            birth_json = {}

    dayun_data = result.get("dayun") or birth_json.get("大运", None)

    retrieval_results = None
    citations = None
    if payload.retrieval_depth != "basic":
        try:
            analysis_context = _extract_analysis_context(result)
            chapter_keys = [
                "overview", "past_validation", "future_luck", "career_wealth",
                "marriage_love", "family", "health", "guidance",
            ]
            retrieval_results = {}
            citations = {}
            from server.rag_engine import _format_retrieval_for_prompt
            for chapter_key in chapter_keys:
                chapter_result = await asyncio.to_thread(retrieve_for_report, chapter_key, analysis_context, k=5)
                retrieval_results[chapter_key] = chapter_result
                citations[chapter_key] = _format_retrieval_for_prompt(chapter_result)
        except Exception as exc:
            logger.warning("RAG retrieval failed for report %s: %s", payload.analysis_id, exc)

    system_prompt = build_report_system_prompt(result, narration, dayun_data, school=payload.school, retrieval_results=retrieval_results)
    messages = [{"role": "system", "content": system_prompt}]

    try:
        raw_reply = await chat_completion(messages, temperature=0.7, max_tokens=8192)
    except Exception as e:
        logger.error("Report LLM call failed for analysis %s: %s", payload.analysis_id, e)
        err_msg = str(e) or type(e).__name__
        return error_response(500, "LLM_ERROR", f"LLM 调用失败: {err_msg}")

    report_data = _parse_report_json(raw_reply)

    report_id = await save_report(payload.analysis_id, report_data, citations=citations)

    response_payload = {
        "status": "completed",
        "analysis_id": payload.analysis_id,
        "report_id": report_id,
        "sections": report_data,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if citations is not None:
        response_payload["citations"] = citations
    return JSONResponse(response_payload)


@app.get("/api/v2/report/{analysis_id}")
async def api_v2_get_report(analysis_id: str):
    """获取已生成的七维度综合分析报告"""
    record = await get_report(analysis_id)
    if not record:
        return error_response(404, "NOT_FOUND", "报告不存在，请先通过 POST /api/v2/report 生成")

    return JSONResponse({
        "status": "completed",
        "analysis_id": record["analysis_id"],
        "report_id": record["id"],
        "sections": record["report_data"],
        "citations": record.get("citations"),
        "created_at": record["created_at"],
    })


def _extract_analysis_context(result: dict) -> dict:
    """从分析结果中提取 RAG 检索所需的上下文信息。"""
    context: dict = {}
    if isinstance(result, dict):
        # day_master: full_analysis() 在顶层，run_analysis() 在 validation 下
        context["day_master"] = result.get("day_master", "") or result.get("validation", {}).get("day_master", "")
        # pillars: full_analysis() 在顶层，run_analysis() 在 shishen 下
        pillars = result.get("pillars", []) or result.get("shishen", {}).get("pillars", [])
        context["bazi"] = " ".join(p.get("gan", "") + p.get("zhi", "") for p in pillars if p.get("gan") and p.get("zhi"))

    pattern = result.get("pattern", {}) if isinstance(result, dict) else {}
    if isinstance(pattern, dict):
        context["pattern"] = pattern
    else:
        context["pattern"] = {"name": str(pattern) if pattern else ""}

    # 旺衰数据在 result['strength']['wangshuai'] 下
    strength_info = result.get("strength", {}) if isinstance(result, dict) else {}
    if isinstance(strength_info, dict) and "wangshuai" in strength_info:
        context["wangshuai"] = strength_info["wangshuai"]
    else:
        # 兼容：可能直接在 result['wangshuai']
        wangshuai = result.get("wangshuai", {}) if isinstance(result, dict) else {}
        if isinstance(wangshuai, dict):
            context["wangshuai"] = wangshuai
        else:
            context["wangshuai"] = {"verdict": str(wangshuai) if wangshuai else ""}

    yongshen = result.get("yongshen", {}) if isinstance(result, dict) else {}
    if isinstance(yongshen, dict):
        context["yongshen"] = yongshen
    else:
        context["yongshen"] = {"yongshen": str(yongshen) if yongshen else ""}

    return context


def _parse_report_json(raw_reply: str) -> dict:
    """解析LLM返回的JSON报告，支持新旧两种格式"""
    try:
        cleaned = raw_reply.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):]
        if cleaned.startswith("```"):
            cleaned = cleaned[len("```"):]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-len("```")]
        cleaned = cleaned.strip()
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            # 新格式8个章节
            new_keys = {"overview", "past_validation", "future_luck", "career_wealth", "marriage_love", "family", "health", "guidance"}
            # 旧格式7个章节（兼容）
            old_keys = {"overview", "personality", "career", "marriage", "health", "dayun_analysis", "lucky"}

            if new_keys.issubset(parsed.keys()):
                return parsed
            if old_keys.issubset(parsed.keys()):
                # 旧格式转换为新格式
                return {
                    "overview": parsed.get("overview", ""),
                    "past_validation": "",
                    "future_luck": parsed.get("dayun_analysis", ""),
                    "career_wealth": parsed.get("career", ""),
                    "marriage_love": parsed.get("marriage", ""),
                    "family": "",
                    "health": parsed.get("health", ""),
                    "guidance": parsed.get("lucky", ""),
                }
            # 部分匹配，填充缺失字段
            return {
                "overview": parsed.get("overview", ""),
                "past_validation": parsed.get("past_validation", ""),
                "future_luck": parsed.get("future_luck", parsed.get("dayun_analysis", "")),
                "career_wealth": parsed.get("career_wealth", parsed.get("career", "")),
                "marriage_love": parsed.get("marriage_love", parsed.get("marriage", "")),
                "family": parsed.get("family", ""),
                "health": parsed.get("health", ""),
                "guidance": parsed.get("guidance", parsed.get("lucky", "")),
            }
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse report JSON: %s", e)

    # 解析失败，返回默认结构
    return {
        "overview": raw_reply,
        "past_validation": "",
        "future_luck": "",
        "career_wealth": "",
        "marriage_love": "",
        "family": "",
        "health": "",
        "guidance": "",
    }


class LLMSettingsRequest(BaseModel):
    api_key: str = Field(default="", description="LLM API Key")
    api_base: str = Field(default="https://api.openai.com/v1", description="API Base URL")
    model: str = Field(default="gpt-4o-mini", description="模型名称")


@app.get("/api/v2/settings/llm")
async def api_v2_get_llm_settings(_auth=Depends(_verify_api_key)):
    cfg = get_llm_config()
    return JSONResponse({
        "api_base": cfg["api_base"],
        "api_key_set": cfg["api_key_set"],
        "model": cfg["model"],
    })


@app.post("/api/v2/settings/llm")
async def api_v2_update_llm_settings(req: LLMSettingsRequest, _auth=Depends(_verify_api_key)):
    try:
        update_llm_config(
            api_key=req.api_key or None,
            api_base=req.api_base or None,
            model=req.model or None,
        )
    except ValueError as e:
        return error_response(400, "INVALID_INPUT", str(e))
    cfg = get_llm_config()
    return JSONResponse({
        "ok": True,
        "api_base": cfg["api_base"],
        "api_key_set": cfg["api_key_set"],
        "model": cfg["model"],
    })


@app.post("/api/v2/settings/llm/test")
async def api_v2_test_llm_settings(_auth=Depends(_verify_api_key)):
    from server.llm import chat_completion, is_llm_configured
    if not is_llm_configured():
        return error_response(400, "NOT_CONFIGURED", "API Key 未配置")
    try:
        reply = await chat_completion(
            [{"role": "user", "content": "请回复\"连接成功\"两个字"}],
            max_tokens=100,
        )
        return JSONResponse({"ok": True, "reply": reply[:100]})
    except Exception as e:
        return error_response(502, "CONNECTION_FAILED", f"连接测试失败: {str(e) or type(e).__name__}")


def main():
    import uvicorn
    host = os.environ.get("BAZI_HOST", "0.0.0.0")
    port = _get_int_env("BAZI_PORT", 8711)
    log_level = os.environ.get("BAZI_LOG_LEVEL", "info")
    workers = _get_int_env("BAZI_WORKERS", 1)
    if workers > 1:
        logger.warning("SQLite does not support multi-worker mode; forcing workers=1")
        workers = 1
    if os.environ.get("DEBUG", "").lower() in ("1", "true", "yes"):
        logger.warning("⚠️  DEBUG mode is enabled — do not use in production!")
    uvicorn.run(app, host=host, port=port, log_level=log_level, workers=workers)


if __name__ == '__main__':
    main()
