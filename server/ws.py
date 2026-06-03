#!/usr/bin/env python3
"""
bazi-pro WebSocket 管理 v5.0
实时推送分析进度：每完成一个 Step 推送状态
支持同一 run_id 多连接
"""

import logging

from fastapi import WebSocket

logger = logging.getLogger("bazi-pro.ws")


class ConnectionManager:

    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, run_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self.add_accepted(run_id, ws)

    def add_accepted(self, run_id: str, ws: WebSocket) -> None:
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
        for ws in list(conns):
            try:
                await ws.send_json(msg)
            except Exception as e:
                dead.append(ws)
                logger.debug("WebSocket send failed for run_id=%s: %s", run_id, e)
        for ws in dead:
            try:
                self.disconnect(run_id, ws)
            except Exception as e:
                logger.warning("WebSocket disconnect error for run_id=%s: %s", run_id, e)
                # Force remove the dead connection if still present
                conns_list = self._connections.get(run_id)
                if conns_list is not None:
                    try:
                        conns_list.remove(ws)
                    except ValueError:
                        pass
                    if not conns_list:
                        self._connections.pop(run_id, None)

    async def broadcast(self, message: dict) -> None:
        dead = []
        for run_id, conns in list(self._connections.items()):
            for ws in list(conns):
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
