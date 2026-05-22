#!/usr/bin/env python3
"""
bazi-pro 个人命理档案系统 v5.0
SQLite 本地存储历史分析记录（线程安全）
"""

import os
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path


def _db_path() -> str:
    home = Path.home() / '.bazi-pro'
    home.mkdir(parents=True, exist_ok=True)
    return str(home / 'archive.db')


class ArchiveStore:

    def __init__(self, db_path: str = ''):
        self.db_path = db_path or _db_path()
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute('PRAGMA journal_mode=WAL')
        return self._local.conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
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
            conn.execute('CREATE INDEX IF NOT EXISTS idx_bazi ON analyses(bazi)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created ON analyses(created_at DESC)')

    def save_analysis(self, bazi: str, trace_json: str = '',
                      report_html: str = '', day_master: str = '',
                      gender: str = '', pattern: str = '',
                      yongshen: str = '', confidence: float = 0.0) -> int:
        conn = self._get_conn()
        with conn:
            cur = conn.execute(
                '''INSERT INTO analyses (bazi, day_master, gender, trace_json,
                   report_html, pattern, yongshen, confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (bazi, day_master, gender, trace_json,
                 report_html, pattern, yongshen, confidence)
            )
            return cur.lastrowid

    def list_analyses(self, limit: int = 20) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            '''SELECT id, bazi, day_master, pattern, yongshen,
               confidence, created_at
               FROM analyses ORDER BY created_at DESC LIMIT ?''',
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_analysis(self, analysis_id: int) -> dict:
        conn = self._get_conn()
        row = conn.execute(
            'SELECT * FROM analyses WHERE id = ?', (analysis_id,)
        ).fetchone()
        return dict(row) if row else {}

    def get_by_bazi(self, bazi: str) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            'SELECT * FROM analyses WHERE bazi = ? ORDER BY created_at DESC',
            (bazi,)
        ).fetchall()
        return [dict(r) for r in rows]

    def export_yearbook(self, year: int = 0) -> str:
        year = year or datetime.now().year
        conn = self._get_conn()
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
        conn = self._get_conn()
        row = conn.execute('SELECT COUNT(*) FROM analyses').fetchone()
        return row[0] if row else 0
