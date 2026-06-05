"""
bazi-pro 灵魂钩子系统 — 长期记忆层 (aiosqlite)
命理数据 + 分析历史 + 交互记录 + 命局标签 持久化
"""

import json
import os
import uuid
from datetime import datetime, timezone

import aiosqlite

_DB_PATH = os.environ.get("BAZI_KG_DB_PATH", "bazi_knowledge.db")
_db_initialized = False
_init_lock = None
_db_connection: aiosqlite.Connection | None = None


def _get_init_lock():
    global _init_lock
    if _init_lock is None:
        import asyncio
        _init_lock = asyncio.Lock()
    return _init_lock


async def _create_connection() -> aiosqlite.Connection:
    db = await aiosqlite.connect(_DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def get_kg_db() -> aiosqlite.Connection:
    global _db_initialized, _db_connection
    if not _db_initialized:
        async with _get_init_lock():
            if not _db_initialized:
                db = await _create_connection()
                await _init_tables(db)
                await db.close()
                _db_initialized = True
    if _db_connection is not None:
        try:
            if _db_connection._connection is not None:
                return _db_connection
        except AttributeError:
            pass
    _db_connection = await _create_connection()
    return _db_connection


async def close_kg_db():
    global _db_connection
    if _db_connection is not None:
        try:
            await _db_connection.close()
        except Exception:
            pass
        _db_connection = None


async def _init_tables(db: aiosqlite.Connection):
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS persons (
            person_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            birth_info TEXT,
            bazi_data TEXT,
            ziwei_data TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_persons_name
            ON persons(name);

        CREATE TABLE IF NOT EXISTS analysis_history (
            id TEXT PRIMARY KEY,
            person_id TEXT NOT NULL,
            analysis_type TEXT NOT NULL,
            result TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_analysis_person
            ON analysis_history(person_id, created_at DESC);

        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_interactions_person
            ON interactions(person_id, created_at);

        CREATE TABLE IF NOT EXISTS person_tags (
            person_id TEXT NOT NULL,
            tag TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (person_id, tag),
            FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_tags_tag
            ON person_tags(tag);
    """)


def _generate_person_id() -> str:
    return f"per_{uuid.uuid4().hex[:12]}"


def _generate_analysis_id() -> str:
    return f"kan_{uuid.uuid4().hex[:12]}"


def _row_to_dict(row) -> dict:
    d = {}
    for key in row.keys():
        d[key] = row[key]
    return d


def _parse_json_field(val):
    if not val:
        return None
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return val


class PersonMemory:

    def __init__(self, db: aiosqlite.Connection | None = None):
        self._db = db

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is not None:
            return self._db
        return await get_kg_db()

    async def get_or_create_person(self, name: str, birth_info: dict) -> str:
        db = await self._get_db()
        now = datetime.now(timezone.utc).isoformat()

        cursor = await db.execute(
            "SELECT person_id FROM persons WHERE name=? AND birth_info=?",
            (name, json.dumps(birth_info, ensure_ascii=False)),
        )
        row = await cursor.fetchone()
        if row:
            return row[0]

        person_id = _generate_person_id()
        await db.execute(
            "INSERT INTO persons (person_id, name, birth_info, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (person_id, name, json.dumps(birth_info, ensure_ascii=False), now, now),
        )
        await db.commit()
        return person_id

    async def save_analysis(self, person_id: str, analysis_type: str, result: dict) -> str:
        db = await self._get_db()
        analysis_id = _generate_analysis_id()
        now = datetime.now(timezone.utc).isoformat()

        await db.execute(
            "INSERT INTO analysis_history (id, person_id, analysis_type, result, created_at) VALUES (?, ?, ?, ?, ?)",
            (analysis_id, person_id, analysis_type, json.dumps(result, ensure_ascii=False), now),
        )
        await db.execute(
            "UPDATE persons SET updated_at=? WHERE person_id=?",
            (now, person_id),
        )
        await db.commit()
        return analysis_id

    async def save_interaction(self, person_id: str, role: str, content: str):
        db = await self._get_db()
        now = datetime.now(timezone.utc).isoformat()

        await db.execute(
            "INSERT INTO interactions (person_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (person_id, role, content, now),
        )
        await db.execute(
            "UPDATE persons SET updated_at=? WHERE person_id=?",
            (now, person_id),
        )
        await db.commit()

    async def get_person_context(self, person_id: str) -> dict:
        db = await self._get_db()

        cursor = await db.execute(
            "SELECT * FROM persons WHERE person_id=?", (person_id,)
        )
        person_row = await cursor.fetchone()
        if not person_row:
            return {}

        person = _row_to_dict(person_row)
        person["birth_info"] = _parse_json_field(person["birth_info"])
        person["bazi_data"] = _parse_json_field(person["bazi_data"])
        person["ziwei_data"] = _parse_json_field(person["ziwei_data"])

        cursor = await db.execute(
            "SELECT id, analysis_type, result, created_at FROM analysis_history WHERE person_id=? ORDER BY created_at DESC",
            (person_id,),
        )
        analyses = []
        for row in await cursor.fetchall():
            item = _row_to_dict(row)
            item["result"] = _parse_json_field(item["result"])
            analyses.append(item)

        cursor = await db.execute(
            "SELECT role, content, created_at FROM interactions WHERE person_id=? ORDER BY created_at ASC",
            (person_id,),
        )
        interactions = [_row_to_dict(row) for row in await cursor.fetchall()]

        cursor = await db.execute(
            "SELECT tag FROM person_tags WHERE person_id=?", (person_id,)
        )
        tags = [row[0] for row in await cursor.fetchall()]

        return {
            "person": person,
            "analyses": analyses,
            "interactions": interactions,
            "tags": tags,
        }

    async def search_persons(self, query: str) -> list[dict]:
        db = await self._get_db()

        like_pattern = f"%{query}%"

        cursor = await db.execute(
            """SELECT DISTINCT p.person_id, p.name, p.birth_info, p.bazi_data, p.created_at
               FROM persons p
               LEFT JOIN person_tags t ON p.person_id = t.person_id
               WHERE p.name LIKE ? OR t.tag LIKE ?
               ORDER BY p.updated_at DESC""",
            (like_pattern, like_pattern),
        )
        results = []
        for row in await cursor.fetchall():
            item = _row_to_dict(row)
            item["birth_info"] = _parse_json_field(item["birth_info"])
            item["bazi_data"] = _parse_json_field(item["bazi_data"])

            tag_cursor = await db.execute(
                "SELECT tag FROM person_tags WHERE person_id=?",
                (item["person_id"],),
            )
            item["tags"] = [r[0] for r in await tag_cursor.fetchall()]
            results.append(item)

        return results

    async def add_tag(self, person_id: str, tag: str):
        db = await self._get_db()
        now = datetime.now(timezone.utc).isoformat()

        await db.execute(
            "INSERT OR IGNORE INTO person_tags (person_id, tag, created_at) VALUES (?, ?, ?)",
            (person_id, tag, now),
        )
        await db.commit()

    async def remove_tag(self, person_id: str, tag: str):
        db = await self._get_db()
        await db.execute(
            "DELETE FROM person_tags WHERE person_id=? AND tag=?",
            (person_id, tag),
        )
        await db.commit()

    async def get_similar_persons(self, bazi_features: dict) -> list[dict]:
        db = await self._get_db()

        target_tags = set()
        for key in ("day_master", "pattern", "yongshen", "strength"):
            val = bazi_features.get(key)
            if val:
                target_tags.add(str(val))
        wuxing = bazi_features.get("wuxing_balance")
        if isinstance(wuxing, dict):
            weak_elements = [e for e, v in wuxing.items() if isinstance(v, (int, float)) and v < 0.15]
            for e in weak_elements:
                target_tags.add(f"{e}弱")

        if not target_tags:
            return []

        placeholders = ",".join("?" for _ in target_tags)
        cursor = await db.execute(
            f"""SELECT p.person_id, p.name, p.birth_info, p.bazi_data,
                       COUNT(DISTINCT t.tag) AS match_count
                FROM persons p
                INNER JOIN person_tags t ON p.person_id = t.person_id
                WHERE t.tag IN ({placeholders})
                GROUP BY p.person_id
                ORDER BY match_count DESC
                LIMIT 20""",
            list(target_tags),
        )

        results = []
        for row in await cursor.fetchall():
            item = {
                "person_id": row[0],
                "name": row[1],
                "birth_info": _parse_json_field(row[2]),
                "bazi_data": _parse_json_field(row[3]),
                "match_count": row[4],
            }

            tag_cursor = await db.execute(
                "SELECT tag FROM person_tags WHERE person_id=?",
                (item["person_id"],),
            )
            item["tags"] = [r[0] for r in await tag_cursor.fetchall()]
            results.append(item)

        return results

    async def update_person_bazi(self, person_id: str, bazi_data: dict):
        db = await self._get_db()
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE persons SET bazi_data=?, updated_at=? WHERE person_id=?",
            (json.dumps(bazi_data, ensure_ascii=False), now, person_id),
        )
        await db.commit()

    async def update_person_ziwei(self, person_id: str, ziwei_data: dict):
        db = await self._get_db()
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE persons SET ziwei_data=?, updated_at=? WHERE person_id=?",
            (json.dumps(ziwei_data, ensure_ascii=False), now, person_id),
        )
        await db.commit()

    async def get_person_analyses(self, person_id: str, limit: int = 50) -> list[dict]:
        db = await self._get_db()
        cursor = await db.execute(
            "SELECT id, analysis_type, result, created_at FROM analysis_history WHERE person_id=? ORDER BY created_at DESC LIMIT ?",
            (person_id, limit),
        )
        results = []
        for row in await cursor.fetchall():
            item = _row_to_dict(row)
            item["result"] = _parse_json_field(item["result"])
            results.append(item)
        return results

    async def get_person_interactions(self, person_id: str, limit: int = 100) -> list[dict]:
        db = await self._get_db()
        cursor = await db.execute(
            "SELECT role, content, created_at FROM interactions WHERE person_id=? ORDER BY created_at ASC LIMIT ?",
            (person_id, limit),
        )
        return [_row_to_dict(row) for row in await cursor.fetchall()]

    async def delete_person(self, person_id: str):
        db = await self._get_db()
        await db.execute("DELETE FROM persons WHERE person_id=?", (person_id,))
        await db.commit()
