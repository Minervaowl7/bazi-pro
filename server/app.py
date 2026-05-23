#!/usr/bin/env python3
"""
bazi-pro FastAPI 应用 v5.0
API 路由：分析、状态查询、结果获取、仪表盘
"""

import uuid
import asyncio
import os
import time
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Security
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from server.ws import manager
from server.analysis import run_analysis
from server.cache import get_cache
from server.schemas import BaziAnalysisRequest

logger = logging.getLogger("bazi-pro")

app = FastAPI(
    title="bazi-pro API",
    description="专业八字命理解读引擎 Web 服务",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
    allow_headers=["*"],
)

if not _cors_origins:
    logger.warning("BAZI_CORS_ORIGINS not set — CORS disabled. Set BAZI_CORS_ORIGINS=* or comma-separated origins.")


_API_KEY = os.environ.get('BAZI_API_KEY', '')
_api_key_scheme = APIKeyHeader(name='X-API-Key', auto_error=False)


async def _verify_api_key(api_key: str = Security(_api_key_scheme)):
    if not _API_KEY:
        return True
    if api_key == _API_KEY:
        return True
    raise HTTPException(status_code=401, detail='Invalid API key')


class _RequestSizeLimitMiddleware:
    def __init__(self, app, max_body_size=10240):
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            for name, value in scope.get("headers", []):
                if name == b"content-length" and int(value) > self.max_body_size:
                    response = JSONResponse(status_code=413, content={"detail": "Request body too large"})
                    await response(scope, receive, send)
                    return
        await self.app(scope, receive, send)


class _RateLimitMiddleware:
    def __init__(self, app, max_requests=30, window_seconds=60):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            client = scope.get("client")
            ip = client[0] if client else "unknown"
            now = time.time()
            timestamps = self._requests.setdefault(ip, [])
            self._requests[ip] = [t for t in timestamps if now - t < self.window_seconds]
            if len(self._requests[ip]) >= self.max_requests:
                response = JSONResponse(status_code=429, content={"detail": "Too many requests"})
                await response(scope, receive, send)
                return
            self._requests[ip].append(now)
        await self.app(scope, receive, send)


app.add_middleware(_RequestSizeLimitMiddleware, max_body_size=10240)
app.add_middleware(_RateLimitMiddleware, max_requests=30, window_seconds=60)


@app.exception_handler(Exception)
async def _global_exception_handler(request, exc):
    debug = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")
    detail = str(exc) if debug else "Internal server error"
    return JSONResponse(status_code=500, content={"detail": detail})


_analysis_tasks: dict[str, dict] = {}
_TASK_TTL_SECONDS = 7200


def _cleanup_expired_tasks() -> None:
    now = time.time()
    expired = [
        rid for rid, info in _analysis_tasks.items()
        if now - info.get('_created_ts', 0) > _TASK_TTL_SECONDS
    ]
    for rid in expired:
        _analysis_tasks.pop(rid, None)


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
<button class="btn" id="analyzeBtn" onclick="startAnalysis()">开始分析</button>
<div class="status-bar" id="statusBar">等待输入...</div>
<div class="result-box" id="resultBox"></div>
</div>

<div class="api-link">
<a href="/docs">API 文档 (Swagger)</a> |
<a href="/redoc">API 文档 (ReDoc)</a>
</div>
</div>

<script>
let ws = null;
async function startAnalysis() {
    var btn = document.getElementById('analyzeBtn');
    var status = document.getElementById('statusBar');
    var result = document.getElementById('resultBox');
    btn.disabled = true;
    status.textContent = '正在提交...';
    result.style.display = 'none';

    try {
        var mcpData = JSON.parse(document.getElementById('mcpInput').value);
        var headers = {'Content-Type': 'application/json'};
        var resp = await fetch('/api/analyze', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(mcpData)
        });
        var data = await resp.json();
        if (resp.status !== 200 && resp.status !== 202) {
            status.textContent = '错误: ' + (data.detail || JSON.stringify(data));
            btn.disabled = false;
            return;
        }
        var runId = data.run_id;
        status.textContent = '分析已启动 (ID: ' + runId + ')，正在连接 WebSocket...';

        var protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws = new WebSocket(protocol + '//' + location.host + '/ws/' + runId);
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
    var resp = await fetch('/api/result/' + runId);
    var data = await resp.json();
    var result = document.getElementById('resultBox');
    result.textContent = JSON.stringify(data, null, 2);
    result.style.display = 'block';
    document.getElementById('analyzeBtn').disabled = false;
}

async function pollStatus(runId) {
    var interval = setInterval(async function() {
        var resp = await fetch('/api/status/' + runId);
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
    run_id = uuid.uuid4().hex
    payload_dict = payload.model_dump()
    detail_level = payload_dict.pop('detail_level', 'standard')

    _analysis_tasks[run_id] = {
        'status': 'queued',
        'created_at': datetime.now(timezone.utc).isoformat(),
        '_created_ts': time.time(),
    }

    _cleanup_expired_tasks()

    asyncio.create_task(_background_analyze(run_id, payload_dict, detail_level))

    return JSONResponse({
        'run_id': run_id,
        'status': 'queued',
        'message': '分析任务已提交，通过 WebSocket /ws/{run_id} 获取进度',
    })


@app.get("/api/status/{run_id}")
async def api_status(run_id: str, _auth=Depends(_verify_api_key)):
    """查询分析进度"""
    task = _analysis_tasks.get(run_id)
    if not task:
        raise HTTPException(status_code=404, detail='run_id 不存在')
    safe_task = {k: v for k, v in task.items() if not k.startswith('_')}
    return JSONResponse(safe_task)


@app.get("/api/result/{run_id}")
async def api_result(run_id: str, _auth=Depends(_verify_api_key)):
    """获取分析结果"""
    task = _analysis_tasks.get(run_id)
    if not task:
        raise HTTPException(status_code=404, detail='run_id 不存在')

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
    await manager.connect(run_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(run_id, ws)
    except Exception:
        manager.disconnect(run_id, ws)


async def _background_analyze(run_id: str, mcp_json: dict, detail_level: str):
    """后台执行分析"""
    _analysis_tasks[run_id]['status'] = 'running'
    try:
        result = await run_analysis(mcp_json, run_id, detail_level)
        _analysis_tasks[run_id]['status'] = result.get('status', 'completed')
        cache = get_cache()
        cache.set(f'result:{run_id}', result, ttl=7200)
    except Exception as e:
        _analysis_tasks[run_id]['status'] = 'failed'
        debug = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")
        _analysis_tasks[run_id]['error'] = str(e) if debug else "Internal server error"
        logger.error("Analysis failed for run_id=%s: %s", run_id, e)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8800, log_level='info')
