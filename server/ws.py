#!/usr/bin/env python3
"""
bazi-pro WebSocket 管理 v4.6
实时推送分析进度：每完成一个 Step 推送状态
"""

import json
import asyncio
from typing import Optional
from fastapi import WebSocket


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, run_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[run_id] = ws

    def disconnect(self, run_id: str) -> None:
        self._connections.pop(run_id, None)

    async def send_progress(self, run_id: str, step: str, status: str,
                            summary: str = '', data: dict = None) -> None:
        ws = self._connections.get(run_id)
        if ws is None:
            return
        try:
            await ws.send_json({
                'run_id': run_id,
                'step': step,
                'status': status,
                'summary': summary,
                'data': data or {},
            })
        except Exception:
            self.disconnect(run_id)

    async def broadcast(self, message: dict) -> None:
        dead = []
        for run_id, ws in self._connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(run_id)
        for rid in dead:
            self.disconnect(rid)

    @property
    def active_connections(self) -> int:
        return len(self._connections)


# 单例
manager = ConnectionManager()
