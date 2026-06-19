from __future__ import annotations

import asyncio
import hmac
import logging
import os
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from server.cache import get_cache
from server.deps import (
    API_KEY,
    TASK_TTL_SECONDS,
    cleanup_expired_tasks,
    error_response,
    task_store,
    verify_api_key,
)
from server.schemas import BaziAnalysisRequest
from server.ws import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/analyze")
async def api_analyze(payload: BaziAnalysisRequest, _auth=Depends(verify_api_key)):
    cleanup_expired_tasks()

    from server.deps import MAX_CONCURRENT_TASKS
    if task_store.count_active() >= MAX_CONCURRENT_TASKS:
        return error_response(503, "SERVER_BUSY", "服务繁忙，请稍后重试")

    run_id = uuid.uuid4().hex
    payload_dict = payload.model_dump()
    detail_level = payload_dict.pop('detail_level', 'standard')

    task_store.create(run_id, {
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


@router.get("/api/status/{run_id}")
async def api_status(run_id: str, _auth=Depends(verify_api_key)):
    task = task_store.get(run_id)
    if not task:
        return error_response(404, "NOT_FOUND", "run_id 不存在")
    safe_task = {k: v for k, v in task.items() if not k.startswith('_')}
    return JSONResponse(safe_task)


@router.get("/api/result/{run_id}")
async def api_result(run_id: str, _auth=Depends(verify_api_key)):
    task = task_store.get(run_id)
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


@router.websocket("/ws/{run_id}")
async def ws_connect(ws: WebSocket, run_id: str):
    if API_KEY:
        api_key = ws.headers.get('x-api-key', '') or ''
        token = ws.query_params.get("token", "") if hasattr(ws, "query_params") else ""
        if not (api_key and hmac.compare_digest(api_key, API_KEY)) and not (token and hmac.compare_digest(token, API_KEY)):
            await ws.close(code=4001, reason='Invalid API key')
            return
    if not task_store.get(run_id):
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
    from server.analysis import run_analysis

    task_store.update(run_id, {'status': 'running'})
    try:
        result = await run_analysis(mcp_json, run_id, detail_level)
        if result is None:
            result = {"status": "failed", "error": "分析引擎返回空结果"}
        actual_status = result.get('status', 'completed')
        task_store.update(run_id, {'status': actual_status})
        cache = get_cache()
        cache.set(f'result:{run_id}', result, ttl=TASK_TTL_SECONDS)
    except Exception as e:
        task_store.update(run_id, {
            'status': 'failed',
            'error': str(e) if os.environ.get("DEBUG", "").lower() in ("1", "true", "yes") else "Internal server error",
        })
        logger.error("Analysis failed for run_id=%s: %s", run_id, e)
