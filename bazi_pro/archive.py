#!/usr/bin/env python3
"""
bazi-pro 个人命理档案系统 v4.8
SQLite 本地存储历史分析记录
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path


def _db_path() -> str:
    """获取数据库路径"""
    home = Path.home() / '.bazi-pro'
    home.mkdir(parents=True, exist_ok=True)
    return str(home / 'archive.db')


class ArchiveStore:
    """命理档案存储（SQLite 后端）"""

    def __init__(self, db_path: str = ''):
        self.db_path = db_path or _db_path()
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bazi TEXT NOT NULL,
                    day_master TEXT,
                    gender TEXT,
                    trace_json TEXT,
                    report_html TEXT,
                    pattern TEXT,
                    yongshen TEXT,
                    confidence REAL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER,
                    claim TEXT,
                    accurate INTEGER,
                    note TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_bazi ON analyses(bazi)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_created ON analyses(created_at DESC)
            ''')

    def save_analysis(self, bazi: str, trace_json: str = '',
                      report_html: str = '', day_master: str = '',
                      gender: str = '', pattern: str = '',
                      yongshen: str = '', confidence: float = 0.0) -> int:
        """保存一次分析记录"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                '''INSERT INTO analyses (bazi, day_master, gender, trace_json,
                   report_html, pattern, yongshen, confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (bazi, day_master, gender, trace_json,
                 report_html, pattern, yongshen, confidence)
            )
            return cur.lastrowid

    def list_analyses(self, limit: int = 20) -> list[dict]:
        """列出历史分析记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                '''SELECT id, bazi, day_master, pattern, yongshen,
                   confidence, created_at
                   FROM analyses ORDER BY created_at DESC LIMIT ?''',
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_analysis(self, analysis_id: int) -> dict:
        """获取单条分析记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM analyses WHERE id = ?', (analysis_id,)
            ).fetchone()
            return dict(row) if row else {}

    def get_by_bazi(self, bazi: str) -> list[dict]:
        """按八字查找历史分析"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM analyses WHERE bazi = ? ORDER BY created_at DESC',
                (bazi,)
            ).fetchall()
            return [dict(r) for r in rows]

    def export_yearbook(self, year: int = 0) -> str:
        """导出个人命理年鉴（JSON 格式）"""
        year = year or datetime.now().year
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                '''SELECT * FROM analyses
                   WHERE strftime('%Y', created_at) = ?
                   ORDER BY created_at DESC''',
                (str(year),)
            ).fetchall()
            records = [dict(r) for r in rows]
        return json.dumps({
            'year': year,
            'total': len(records),
            'records': records,
        }, ensure_ascii=False, indent=2)

    @property
    def total_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute('SELECT COUNT(*) FROM analyses').fetchone()
            return row[0] if row else 0
