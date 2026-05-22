#!/usr/bin/env python3
"""
bazi-pro WebSocket 管理 v5.0
实时推送分析进度：每完成一个 Step 推送状态
支持同一 run_id 多连接
"""

import json
import asyncio
from typing import Optional
from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, run_id: str, ws: WebSocket) -> None:
        await ws.accept()
        if run_id not in self._connections:
            self._connections[run_id] = []
        self._connections[run_id].append(ws)

    def disconnect(self, run_id: str, ws: WebSocket = None) -> None:
        if run_id not in self._connections:
            return
        if ws is None:
            self._connections.pop(run_id, None)
            return
        conns = self._connections[run_id]
        try:
            conns.remove(ws)
        except ValueError:
            pass
        if not conns:
            self._connections.pop(run_id, None)

    async def send_progress(self, run_id: str, step: str, status: str,
                            summary: str = '', data: dict = None) -> None:
        conns = self._connections.get(run_id)
        if not conns:
            return
        msg = {
            'run_id': run_id,
            'step': step,
            'status': status,
            'summary': summary,
            'data': data or {},
        }
        dead = []
        for ws in conns:
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(run_id, ws)

    async def broadcast(self, message: dict) -> None:
        dead = []
        for run_id, conns in self._connections.items():
            for ws in conns:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append((run_id, ws))
        for run_id, ws in dead:
            self.disconnect(run_id, ws)

    @property
    def active_connections(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


manager = ConnectionManager()
