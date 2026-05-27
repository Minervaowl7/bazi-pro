"""
bazi-pro SQLite 存储层 (aiosqlite)
分析记录 + 聊天历史持久化
"""

import json
import os
import uuid
from datetime import datetime, timezone

import aiosqlite

_DB_PATH = os.environ.get("BAZI_DB_PATH", "bazi_pro.db")
_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(_DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
        await _init_tables(_db)
    return _db


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None


async def _init_tables(db: aiosqlite.Connection):
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'processing',
            detail_level TEXT NOT NULL DEFAULT 'standard',
            birth_json TEXT,
            bazi_chart TEXT,
            schools_json TEXT,
            consensus_json TEXT,
            synthesis_md TEXT,
            full_result TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            duration_ms INTEGER,
            day_master TEXT,
            pattern TEXT,
            yongshen TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_analyses_created
            ON analyses(created_at DESC);

        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            citations TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_chat_analysis
            ON chat_messages(analysis_id, created_at);

        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            analysis_id TEXT NOT NULL,
            report_data TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (analysis_id) REFERENCES analyses(id)
        );

        CREATE INDEX IF NOT EXISTS idx_reports_analysis
            ON reports(analysis_id);
    """)


def generate_analysis_id() -> str:
    return f"ana_{uuid.uuid4().hex[:12]}"


async def insert_analysis(
    analysis_id: str,
    birth_json: dict,
    detail_level: str = "standard",
) -> str:
    db = await get_db()
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        """INSERT INTO analyses (id, status, detail_level, birth_json, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (analysis_id, "processing", detail_level, json.dumps(birth_json, ensure_ascii=False), now),
    )
    await db.commit()
    return analysis_id


async def update_analysis_result(analysis_id: str, result: dict):
    db = await get_db()
    now = datetime.now(timezone.utc).isoformat()

    pattern_info = result.get("pattern", {})
    yongshen_info = result.get("yongshen", {})
    day_master = result.get("validation", {}).get("day_master", "")

    pattern_str = pattern_info.get("pattern", "") if isinstance(pattern_info, dict) else ""
    yongshen_str = yongshen_info.get("yongshen", "") if isinstance(yongshen_info, dict) else ""

    status = result.get("status", "completed")

    await db.execute(
        """UPDATE analyses
           SET status=?, full_result=?, completed_at=?,
               day_master=?, pattern=?, yongshen=?
           WHERE id=?""",
        (
            status,
            json.dumps(result, ensure_ascii=False),
            now,
            day_master,
            pattern_str,
            yongshen_str,
            analysis_id,
        ),
    )
    await db.commit()


async def update_analysis_status(analysis_id: str, status: str, error: str | None = None):
    db = await get_db()
    if error:
        await db.execute(
            "UPDATE analyses SET status=?, full_result=? WHERE id=?",
            (status, json.dumps({"error": error}, ensure_ascii=False), analysis_id),
        )
    else:
        await db.execute("UPDATE analyses SET status=? WHERE id=?", (status, analysis_id))
    await db.commit()


async def get_analysis(analysis_id: str) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,))
    row = await cursor.fetchone()
    if not row:
        return None
    return _row_to_dict(row)


async def list_analyses(page: int = 1, page_size: int = 20) -> dict:
    db = await get_db()
    offset = (page - 1) * page_size

    cursor = await db.execute("SELECT COUNT(*) FROM analyses")
    total = (await cursor.fetchone())[0]

    cursor = await db.execute(
        """SELECT id, status, created_at, completed_at, day_master, pattern, yongshen, birth_json
           FROM analyses ORDER BY created_at DESC LIMIT ? OFFSET ?""",
        (page_size, offset),
    )
    rows = await cursor.fetchall()

    analyses = []
    for row in rows:
        item = {
            "id": row[0],
            "status": row[1],
            "created_at": row[2],
            "completed_at": row[3],
            "day_master": row[4] or "",
            "pattern": row[5] or "",
            "yongshen": row[6] or "",
        }
        if row[7]:
            try:
                birth = json.loads(row[7])
                item["bazi"] = birth.get("八字", "")
            except (json.JSONDecodeError, TypeError):
                pass
        analyses.append(item)

    return {"analyses": analyses, "total": total, "page": page, "page_size": page_size}


def _row_to_dict(row) -> dict:
    keys = ["id", "status", "detail_level", "birth_json", "bazi_chart",
            "schools_json", "consensus_json", "synthesis_md", "full_result",
            "created_at", "completed_at", "duration_ms", "day_master", "pattern", "yongshen"]
    d = {}
    for i, key in enumerate(keys):
        val = row[i]
        if key in ("birth_json", "full_result", "bazi_chart", "schools_json", "consensus_json") and val:
            try:
                d[key] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                d[key] = val
        else:
            d[key] = val
    return d


async def insert_chat_message(analysis_id: str, role: str, content: str, citations: str = ""):
    db = await get_db()
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO chat_messages (analysis_id, role, content, citations, created_at) VALUES (?, ?, ?, ?, ?)",
        (analysis_id, role, content, citations, now),
    )
    await db.commit()


async def get_chat_messages(analysis_id: str, limit: int = 50) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT role, content, citations, created_at FROM chat_messages WHERE analysis_id = ? ORDER BY id ASC LIMIT ?",
        (analysis_id, limit),
    )
    rows = await cursor.fetchall()
    return [
        {"role": row[0], "content": row[1], "citations": row[2] or "", "created_at": row[3]}
        for row in rows
    ]


async def save_report(analysis_id: str, report_data: dict) -> str:
    db = await get_db()
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO reports (id, analysis_id, report_data, created_at) VALUES (?, ?, ?, ?)",
        (report_id, analysis_id, json.dumps(report_data, ensure_ascii=False), now),
    )
    await db.commit()
    return report_id


async def get_report(analysis_id: str) -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, analysis_id, report_data, created_at FROM reports WHERE analysis_id = ? ORDER BY created_at DESC LIMIT 1",
        (analysis_id,),
    )
    row = await cursor.fetchone()
    if not row:
        return None
    report_data = row[2]
    if isinstance(report_data, str):
        try:
            report_data = json.loads(report_data)
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": row[0],
        "analysis_id": row[1],
        "report_data": report_data,
        "created_at": row[3],
    }
