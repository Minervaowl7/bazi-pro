#!/usr/bin/env python3
"""
bazi-pro FastAPI 应用 v5.0
路由注册 + 中间件 + 健康检查
"""

import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from fastapi import FastAPI  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.middleware.trustedhost import TrustedHostMiddleware  # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse  # noqa: E402

from server.cache import get_cache  # noqa: E402
from server.db import close_db, get_db  # noqa: E402
from server.deps import (  # noqa: E402
    MAX_PAYLOAD_BYTES,
    APIKeyError,
    backend_name,
    error_response,
    get_int_env,
    rate_limiter,
    ratelimiter_backend_name,
    task_store,
)
from server.metrics import (  # noqa: E402
    create_metrics_middleware,
    format_prometheus_text,
    get_metrics_snapshot,
)
from server.routes import (  # noqa: E402
    v1_legacy,
    v2_analysis,
    v2_chat,
    v2_fortune,
    v2_settings,
    v2_tools,
    v2_ziwei,
)
from server.sse import setup_progress_hook  # noqa: E402
from server.taskstore import RedisTaskStore  # noqa: E402
from server.ws import manager  # noqa: E402

logger = logging.getLogger("bazi-pro")

# OpenAPI 文档默认启用，可通过 BAZI_DISABLE_DOCS=1 禁用（生产环境建议禁用）
_enable_docs = os.environ.get('BAZI_DISABLE_DOCS', '').lower() not in ('1', 'true', 'yes')


def _validate_config():
    """启动时验证关键配置，记录警告"""
    import sys

    api_key = os.environ.get('BAZI_API_KEY', '')
    allow_unauthed = os.environ.get('BAZI_ALLOW_UNAUTHED', '').lower() in ('1', 'true', 'yes')
    env = os.environ.get('ENV', '').lower()

    # 认证检查
    if not api_key and not allow_unauthed:
        if env in ('prod', 'production'):
            logger.error("❌ 生产环境必须设置 BAZI_API_KEY！")
            sys.exit(1)
        else:
            logger.warning("⚠️  BAZI_API_KEY 未设置，所有请求将被拒绝。设置 BAZI_ALLOW_UNAUTHED=1 可禁用认证")

    # LLM 配置检查
    llm_key = os.environ.get('LLM_API_KEY', '')
    if not llm_key:
        logger.info("ℹ️  LLM_API_KEY 未设置 — LLM 辅助解读功能已禁用")

    # LLM_TIMEOUT 安全解析（防止 ValueError 崩溃）
    llm_timeout_raw = os.environ.get('LLM_TIMEOUT', '300')
    try:
        llm_timeout = int(llm_timeout_raw)
        if llm_timeout <= 0:
            raise ValueError
    except (ValueError, TypeError):
        logger.warning("⚠️  LLM_TIMEOUT=%r 无效，使用默认值 300", llm_timeout_raw)

    # 数据库路径检查
    db_path = os.environ.get('BAZI_DB_PATH', 'bazi_pro.db')
    db_dir = os.path.dirname(os.path.abspath(db_path))
    if not os.path.isdir(db_dir):
        logger.warning("⚠️  BAZI_DB_PATH 目录不存在: %s", db_dir)

    # CORS 配置日志
    cors_origins = os.environ.get('BAZI_CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
    logger.info("ℹ️  CORS origins: %s", cors_origins)
    if cors_origins == '*' and env in ('prod', 'production'):
        logger.error("❌ 生产环境不应使用 CORS '*'！")
        sys.exit(1)


# 后台任务注册表（用于优雅关闭）
_background_tasks: set = set()


def register_background_task(task: asyncio.Task):
    """注册后台任务，用于优雅关闭时取消"""
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # 启动配置验证
    _validate_config()
    await get_db()
    # 预热 BM25 古籍索引（避免首次请求阻塞 3-10 秒）
    try:
        import asyncio as _aio
        import logging as _logging
        _logger = _logging.getLogger(__name__)
        def _warm_bm25():
            try:
                from bazi_pro.retrieve_classical import _resolve_corpus, get_bm25, load_corpus
                corpus = _resolve_corpus()
                entries = load_corpus(corpus)
                if entries:
                    get_bm25(corpus, entries)
                    _logger.info("BM25 古籍索引预热完成（%d 条）", len(entries))
            except Exception:
                _logger.warning("BM25 古籍索引预热失败，首次检索将延迟", exc_info=True)
        await _aio.to_thread(_warm_bm25)
    except Exception:
        logger.warning("BM25 古籍索引预热线程异常", exc_info=True)

    yield

    # ── 优雅关闭 ──
    logger.info("正在关闭服务...")

    # 取消所有后台任务
    if _background_tasks:
        logger.info("取消 %d 个后台任务...", len(_background_tasks))
        for task in _background_tasks:
            task.cancel()
        # 等待任务完成（最多 5 秒）
        await asyncio.wait(_background_tasks, timeout=5.0)

    # 关闭数据库连接
    await close_db()
    logger.info("服务已关闭")


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
    _allowed_hosts = ['localhost', '127.0.0.1', 'testserver']
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)
logger.info("TrustedHostMiddleware enabled: %s", _allowed_hosts)


class _CorrelationIdMiddleware:
    """为每个请求生成唯一 correlation ID，用于日志关联"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request_id = uuid.uuid4().hex[:12]
            scope["request_id"] = request_id
            # 添加到响应头
            async def send_with_id(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"x-request-id", request_id.encode()))
                    message["headers"] = headers
                await send(message)
            await self.app(scope, receive, send_with_id)
        else:
            await self.app(scope, receive, send)


app.add_middleware(_CorrelationIdMiddleware)


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


@app.exception_handler(APIKeyError)
async def _api_key_error_handler(request, exc):
    return error_response(401, "UNAUTHORIZED", "API key 无效或缺失")


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
    def __init__(self, app, rate_limiter):
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


app.add_middleware(_RequestSizeLimitMiddleware, max_body_size=MAX_PAYLOAD_BYTES)
app.add_middleware(_RateLimitMiddleware, rate_limiter=rate_limiter)
app.add_middleware(create_metrics_middleware())


@app.exception_handler(Exception)
async def _global_exception_handler(request, exc):
    error_id = uuid.uuid4().hex[:8]
    # 始终记录完整异常到日志（服务端）
    logger.error("[%s] Unhandled %s: %s", error_id, exc.__class__.__name__, exc, exc_info=True)
    # 安全：永远不向客户端发送原始异常信息（防止信息泄露）
    # DEBUG 模式下日志已包含完整堆栈，客户端只需 error_id 即可关联
    message = f"服务器内部错误 (error_id={error_id})"
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


setup_progress_hook(manager)

from server.ratelimiter import RedisRateLimiter  # noqa: E402


@app.get("/api/health")
async def api_health():
    cache = get_cache()
    health = {
        "version": app.version,
        "cache_backend": cache.backend,
        "task_store_backend": backend_name(task_store),
        "rate_limiter_backend": ratelimiter_backend_name(rate_limiter),
    }
    degraded_reasons = []
    if isinstance(task_store, RedisTaskStore) and task_store.is_degraded:
        degraded_reasons.append("task_store: redis degraded, using memory fallback")
    if isinstance(rate_limiter, RedisRateLimiter) and rate_limiter.is_degraded:
        degraded_reasons.append("rate_limiter: redis degraded, using memory fallback")
    if degraded_reasons:
        health["degraded"] = degraded_reasons
    return JSONResponse(health)


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus 指标端点（无需鉴权，供 Prometheus 抓取）"""
    return JSONResponse(get_metrics_snapshot())


@app.get("/metrics/text")
async def metrics_text_endpoint():
    """Prometheus text exposition 格式"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(format_prometheus_text(), media_type="text/plain")


@app.get("/", response_class=HTMLResponse)
async def index():
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


app.include_router(v1_legacy.router)
app.include_router(v2_analysis.router)
app.include_router(v2_fortune.router)
app.include_router(v2_ziwei.router)
app.include_router(v2_chat.router)
app.include_router(v2_settings.router)
app.include_router(v2_tools.router)


def main():
    import uvicorn
    host = os.environ.get("BAZI_HOST", "0.0.0.0")
    port = get_int_env("BAZI_PORT", 8711)
    log_level = os.environ.get("BAZI_LOG_LEVEL", "info")
    workers = get_int_env("BAZI_WORKERS", 1)
    if workers > 1:
        logger.warning("SQLite does not support multi-worker mode; forcing workers=1")
        workers = 1
    if os.environ.get("DEBUG", "").lower() in ("1", "true", "yes"):
        logger.warning("⚠️  DEBUG mode is enabled — do not use in production!")
    uvicorn.run(app, host=host, port=port, log_level=log_level, workers=workers)


if __name__ == '__main__':
    main()
