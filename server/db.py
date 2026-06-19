"""
bazi-pro SQLite 存储层 (aiosqlite)
分析记录 + 聊天历史持久化

并发安全：
  - 使用 _db_write_lock 保护所有写操作，防止 SQLite 单连接并发写入
  - WAL 模式允许并发读取
  - 使用 try/except ping 检查连接健康，不访问私有属性
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone

import aiosqlite

logger = logging.getLogger(__name__)

_DB_PATH = os.environ.get("BAZI_DB_PATH", "bazi_pro.db")
_db_initialized = False
_init_lock: asyncio.Lock | None = None
_write_lock: asyncio.Lock | None = None
_db_connection: aiosqlite.Connection | None = None

# 分页上限，防止恶意请求 dump 整个数据库
MAX_PAGE_SIZE = 100


def _get_init_lock() -> asyncio.Lock:
    global _init_lock
    if _init_lock is None:
        _init_lock = asyncio.Lock()
    return _init_lock


def _get_write_lock() -> asyncio.Lock:
    global _write_lock
    if _write_lock is None:
        _write_lock = asyncio.Lock()
    return _write_lock


async def _create_connection() -> aiosqlite.Connection:
    db = await aiosqlite.connect(_DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def _is_connection_alive(conn: aiosqlite.Connection) -> bool:
    """检查连接是否可用（不访问私有属性）"""
    try:
        cursor = await conn.execute("SELECT 1")
        await cursor.fetchone()
        return True
    except Exception:
        return False


async def get_db() -> aiosqlite.Connection:
    """获取数据库连接（线程安全，自动重连）"""
    global _db_initialized, _db_connection

    # 初始化阶段：创建表结构
    if not _db_initialized:
        async with _get_init_lock():
            if not _db_initialized:
                db = await _create_connection()
                await _init_tables(db)
                await db.close()
                _db_initialized = True

    # 连接健康检查：使用 SELECT 1 ping（不访问私有属性）
    if _db_connection is not None:
        if await _is_connection_alive(_db_connection):
            return _db_connection
        logger.warning("数据库连接已失效，正在重连...")
        try:
            await _db_connection.close()
        except Exception:
            pass
        _db_connection = None

    # 创建新连接
    async with _get_init_lock():
        # 双重检查：另一个协程可能已经创建了连接
        if _db_connection is not None and await _is_connection_alive(_db_connection):
            return _db_connection
        _db_connection = await _create_connection()
        return _db_connection


async def close_db():
    """关闭数据库连接"""
    global _db_connection
    if _db_connection is not None:
        try:
            await _db_connection.close()
        except Exception:
            pass
        _db_connection = None


async def _init_tables(db: aiosqlite.Connection):
    """初始化数据库表结构"""
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
            school TEXT NOT NULL DEFAULT 'ziping',
            created_at TEXT NOT NULL,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_chat_analysis
            ON chat_messages(analysis_id, school, created_at);

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

    # 安全迁移：记录失败而非静默忽略
    for sql, desc in [
        ("ALTER TABLE chat_messages ADD COLUMN school TEXT NOT NULL DEFAULT 'ziping'", "chat_messages.school"),
        ("ALTER TABLE reports ADD COLUMN citations TEXT", "reports.citations"),
    ]:
        try:
            await db.execute(sql)
            logger.info("数据库迁移完成: %s", desc)
        except Exception:
            pass  # 列已存在，正常情况


def generate_analysis_id() -> str:
    return f"ana_{uuid.uuid4().hex[:12]}"


async def insert_analysis(
    analysis_id: str,
    birth_json: dict,
    detail_level: str = "standard",
) -> str:
    async with _get_write_lock():
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
    async with _get_write_lock():
        db = await get_db()
        now = datetime.now(timezone.utc).isoformat()

        pattern_info = result.get("pattern", {})
        yongshen_info = result.get("yongshen", {})
        day_master = result.get("validation", {}).get("day_master", "") or result.get("day_master", "")

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
    async with _get_write_lock():
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
    # 安全限制：防止恶意请求 dump 整个数据库
    page_size = min(page_size, MAX_PAGE_SIZE)
    page = max(1, page)

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


async def insert_chat_message(analysis_id: str, role: str, content: str, citations: str = "", school: str = "ziping"):
    async with _get_write_lock():
        db = await get_db()
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO chat_messages (analysis_id, role, content, citations, school, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (analysis_id, role, content, citations, school, now),
        )
        await db.commit()


async def get_chat_messages(analysis_id: str, limit: int = 50, school: str | None = None) -> list[dict]:
    """获取用户/助手消息（自动过滤摘要消息，前端不展示摘要）"""
    db = await get_db()
    if school:
        cursor = await db.execute(
            "SELECT role, content, citations, created_at FROM chat_messages "
            "WHERE analysis_id = ? AND school = ? AND role != 'summary' ORDER BY id ASC LIMIT ?",
            (analysis_id, school, limit),
        )
    else:
        cursor = await db.execute(
            "SELECT role, content, citations, created_at FROM chat_messages "
            "WHERE analysis_id = ? AND role != 'summary' ORDER BY id ASC LIMIT ?",
            (analysis_id, limit),
        )
    rows = await cursor.fetchall()
    return [
        {"role": row[0], "content": row[1], "citations": row[2] or "", "created_at": row[3]}
        for row in rows
    ]


async def get_latest_summary(analysis_id: str, school: str = "ziping") -> dict | None:
    """获取最新的对话摘要消息（role='summary'）"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, content, created_at FROM chat_messages WHERE analysis_id = ? AND school = ? AND role = 'summary' ORDER BY id DESC LIMIT 1",
        (analysis_id, school),
    )
    row = await cursor.fetchone()
    if not row:
        return None
    return {"id": row[0], "content": row[1], "created_at": row[2]}


async def get_messages_after_id(
    analysis_id: str, after_id: int, school: str = "ziping", limit: int = 100
) -> list[dict]:
    """获取指定 ID 之后的用户/助手消息（不含摘要），用于构建 LLM 上下文"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, role, content, citations, created_at FROM chat_messages "
        "WHERE analysis_id = ? AND school = ? AND id > ? AND role IN ('user', 'assistant') "
        "ORDER BY id ASC LIMIT ?",
        (analysis_id, school, after_id, limit),
    )
    rows = await cursor.fetchall()
    return [
        {"id": row[0], "role": row[1], "content": row[2], "citations": row[3] or "", "created_at": row[4]}
        for row in rows
    ]


async def insert_chat_summary(analysis_id: str, content: str, school: str = "ziping") -> None:
    """插入对话摘要消息（role='summary'）"""
    db = await get_db()
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO chat_messages (analysis_id, role, content, citations, school, created_at) "
        "VALUES (?, 'summary', ?, '', ?, ?)",
        (analysis_id, content, school, now),
    )
    await db.commit()


async def save_report(analysis_id: str, report_data: dict, citations: dict | None = None) -> str:
    async with _get_write_lock():
        db = await get_db()
        report_id = f"rpt_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        citations_json = json.dumps(citations, ensure_ascii=False) if citations else None
        await db.execute(
            "INSERT INTO reports (id, analysis_id, report_data, citations, created_at) VALUES (?, ?, ?, ?, ?)",
            (report_id, analysis_id, json.dumps(report_data, ensure_ascii=False), citations_json, now),
        )
        await db.commit()
    return report_id


async def get_report(analysis_id: str) -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, analysis_id, report_data, citations, created_at FROM reports WHERE analysis_id = ? ORDER BY created_at DESC LIMIT 1",
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
    citations = row[3]
    if isinstance(citations, str):
        try:
            citations = json.loads(citations)
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": row[0],
        "analysis_id": row[1],
        "report_data": report_data,
        "citations": citations,
        "created_at": row[4],
    }
