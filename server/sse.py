from __future__ import annotations

import asyncio
import json
import logging

logger = logging.getLogger("bazi-pro")

subscribers: dict[str, list[asyncio.Queue]] = {}
buffers: dict[str, list[str]] = {}
v2_active_ids: set[str] = set()
lock = asyncio.Lock()
_BUFFER_MAX = 100


async def broadcast(analysis_id: str, event: str, data: dict):
    msg = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
    async with lock:
        buf = buffers.get(analysis_id)
        if buf is not None:
            buf.append(msg)
            if len(buf) > _BUFFER_MAX:
                del buf[:len(buf) - _BUFFER_MAX]
        queues = list(subscribers.get(analysis_id, []))
    for q in queues:
        await q.put(msg)


def setup_progress_hook(manager):
    original = manager.send_progress

    async def _ws_send_with_sse(run_id, step, status, summary='', data=None):
        await original(run_id, step, status, summary, data)
        if run_id in v2_active_ids:
            await broadcast(run_id, "progress", {
                "step": step, "name": summary, "status": status, "message": summary,
            })

    manager.send_progress = _ws_send_with_sse
