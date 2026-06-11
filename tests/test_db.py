"""
server/db.py 单元测试 — 覆盖所有 CRUD 操作
使用临时 SQLite 文件，测试后自动清理。
"""

import asyncio
import json
import os
import tempfile

import pytest

# ──────────────────────────── 辅助 ────────────────────────────

def _run(coro):
    """同步运行异步函数"""
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _tmp_db(monkeypatch):
    """每个测试使用独立的临时 SQLite 数据库，重置全局单例状态。"""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    import server.db as db_mod

    monkeypatch.setattr(db_mod, "_DB_PATH", db_path)
    monkeypatch.setattr(db_mod, "_db_initialized", False)
    monkeypatch.setattr(db_mod, "_db_connection", None)
    monkeypatch.setattr(db_mod, "_init_lock", None)

    yield db_path

    _run(db_mod.close_db())
    try:
        os.unlink(db_path)
    except OSError:
        pass


# ──────────────────────────── get_db 初始化 ────────────────────────────


def test_get_db_initializes_tables():
    """get_db 应自动创建所有表（analyses / chat_messages / reports）"""
    import server.db as db_mod

    async def _test():
        db = await db_mod.get_db()
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        names = [row[0] for row in await cursor.fetchall()]
        assert "analyses" in names
        assert "chat_messages" in names
        assert "reports" in names

    _run(_test())


def test_get_db_returns_singleton():
    """连续调用 get_db 应返回同一连接对象"""
    import server.db as db_mod

    async def _test():
        db1 = await db_mod.get_db()
        db2 = await db_mod.get_db()
        assert db1 is db2

    _run(_test())


def test_get_db_reconnects_after_close():
    """close_db 后再调 get_db 应重新创建连接"""
    import server.db as db_mod

    async def _test():
        db1 = await db_mod.get_db()
        await db_mod.close_db()
        db2 = await db_mod.get_db()
        assert db2 is not None
        assert db2 is not db1

    _run(_test())


# ──────────────────────────── analysis CRUD ────────────────────────────


def test_insert_and_get_analysis():
    """insert_analysis → get_analysis 完整链路"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        birth = {"year": 1990, "month": 1, "day": 1, "hour": 12}
        await db_mod.insert_analysis(aid, birth, detail_level="full")

        result = await db_mod.get_analysis(aid)
        assert result is not None
        assert result["id"] == aid
        assert result["status"] == "processing"
        assert result["detail_level"] == "full"
        assert result["birth_json"] == birth

    _run(_test())


def test_get_analysis_not_found():
    """查询不存在的分析记录应返回 None"""
    import server.db as db_mod

    async def _test():
        result = await db_mod.get_analysis("nonexistent_id")
        assert result is None

    _run(_test())


def test_update_analysis_result():
    """update_analysis_result 应写入 full_result 并更新状态"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        result_data = {
            "status": "completed",
            "day_master": "甲",
            "pattern": {"pattern": "正官格"},
            "yongshen": {"yongshen": "水"},
            "validation": {"day_master": "甲"},
        }
        await db_mod.update_analysis_result(aid, result_data)

        row = await db_mod.get_analysis(aid)
        assert row["status"] == "completed"
        assert row["day_master"] == "甲"
        assert row["pattern"] == "正官格"
        assert row["yongshen"] == "水"
        assert row["completed_at"] is not None

    _run(_test())


def test_update_analysis_status():
    """update_analysis_status 可设置为 error 并附带错误信息"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        await db_mod.update_analysis_status(aid, "error", error="超时")

        row = await db_mod.get_analysis(aid)
        assert row["status"] == "error"
        assert "超时" in json.dumps(row["full_result"], ensure_ascii=False)

    _run(_test())


def test_list_analyses_pagination():
    """list_analyses 应支持分页，按 created_at DESC 排序"""
    import server.db as db_mod

    async def _test():
        for i in range(5):
            aid = db_mod.generate_analysis_id()
            await db_mod.insert_analysis(aid, {"year": 1990 + i, "month": 1, "day": 1, "hour": 12})

        page1 = await db_mod.list_analyses(page=1, page_size=2)
        assert page1["total"] == 5
        assert len(page1["analyses"]) == 2
        assert page1["page"] == 1
        assert page1["page_size"] == 2

        page3 = await db_mod.list_analyses(page=3, page_size=2)
        assert len(page3["analyses"]) == 1

    _run(_test())


# ──────────────────────────── chat_messages CRUD ────────────────────────────


def test_insert_and_get_chat_messages():
    """insert_chat_message → get_chat_messages 完整链路"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        await db_mod.insert_chat_message(aid, "user", "我的八字如何？")
        await db_mod.insert_chat_message(aid, "assistant", "您是甲木日主…", citations="《子平真诠》")

        msgs = await db_mod.get_chat_messages(aid)
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "我的八字如何？"
        assert msgs[1]["role"] == "assistant"
        assert msgs[1]["citations"] == "《子平真诠》"

    _run(_test())


def test_get_chat_messages_school_filter():
    """get_chat_messages 按 school 过滤"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        await db_mod.insert_chat_message(aid, "user", "子平问题", school="ziping")
        await db_mod.insert_chat_message(aid, "user", "盲派问题", school="mangpai")
        await db_mod.insert_chat_message(aid, "user", "新派问题", school="xinpai")

        ziping_msgs = await db_mod.get_chat_messages(aid, school="ziping")
        assert len(ziping_msgs) == 1
        assert ziping_msgs[0]["content"] == "子平问题"

        mangpai_msgs = await db_mod.get_chat_messages(aid, school="mangpai")
        assert len(mangpai_msgs) == 1
        assert mangpai_msgs[0]["content"] == "盲派问题"

        all_msgs = await db_mod.get_chat_messages(aid)
        assert len(all_msgs) == 3

    _run(_test())


def test_get_chat_messages_excludes_summary():
    """get_chat_messages 自动过滤 role='summary' 的消息"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        await db_mod.insert_chat_message(aid, "user", "普通消息")
        await db_mod.insert_chat_summary(aid, "这是一段摘要")

        msgs = await db_mod.get_chat_messages(aid)
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"

    _run(_test())


def test_get_chat_messages_limit():
    """get_chat_messages 的 limit 参数应限制返回条数"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        for i in range(10):
            await db_mod.insert_chat_message(aid, "user", f"消息{i}")

        msgs = await db_mod.get_chat_messages(aid, limit=3)
        assert len(msgs) == 3

    _run(_test())


# ──────────────────────────── chat_summary CRUD ────────────────────────────


def test_insert_and_get_latest_summary():
    """insert_chat_summary → get_latest_summary 完整链路"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        await db_mod.insert_chat_summary(aid, "第一段摘要", school="ziping")
        await db_mod.insert_chat_summary(aid, "第二段摘要", school="ziping")

        summary = await db_mod.get_latest_summary(aid, school="ziping")
        assert summary is not None
        assert summary["content"] == "第二段摘要"
        assert "id" in summary
        assert "created_at" in summary

    _run(_test())


def test_get_latest_summary_not_found():
    """无摘要时 get_latest_summary 应返回 None"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        summary = await db_mod.get_latest_summary(aid)
        assert summary is None

    _run(_test())


def test_get_latest_summary_school_filter():
    """get_latest_summary 按 school 隔离"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        await db_mod.insert_chat_summary(aid, "子平摘要", school="ziping")
        await db_mod.insert_chat_summary(aid, "盲派摘要", school="mangpai")

        ziping = await db_mod.get_latest_summary(aid, school="ziping")
        assert ziping["content"] == "子平摘要"

        mangpai = await db_mod.get_latest_summary(aid, school="mangpai")
        assert mangpai["content"] == "盲派摘要"

    _run(_test())


# ──────────────────────────── get_messages_after_id ────────────────────────────


def test_get_messages_after_id():
    """get_messages_after_id 应返回指定 ID 之后的 user/assistant 消息"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        await db_mod.insert_chat_message(aid, "user", "消息1")
        await db_mod.insert_chat_message(aid, "assistant", "回复1")
        await db_mod.insert_chat_message(aid, "user", "消息2")
        await db_mod.insert_chat_summary(aid, "摘要不应返回")

        after = await db_mod.get_messages_after_id(aid, after_id=1, school="ziping")
        assert len(after) == 2
        assert after[0]["content"] == "回复1"
        assert after[1]["content"] == "消息2"
        assert "id" in after[0]

    _run(_test())


def test_get_messages_after_id_limit():
    """get_messages_after_id 的 limit 参数应生效"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        for i in range(5):
            await db_mod.insert_chat_message(aid, "user", f"msg{i}")

        after = await db_mod.get_messages_after_id(aid, after_id=0, school="ziping", limit=2)
        assert len(after) == 2

    _run(_test())


# ──────────────────────────── report CRUD ────────────────────────────


def test_save_and_get_report():
    """save_report → get_report 完整链路"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        report_data = {"chapter1": "总论", "chapter2": "详析"}
        citations = {"ref1": "《子平真诠》卷一"}
        report_id = await db_mod.save_report(aid, report_data, citations=citations)

        assert report_id.startswith("rpt_")

        report = await db_mod.get_report(aid)
        assert report is not None
        assert report["id"] == report_id
        assert report["analysis_id"] == aid
        assert report["report_data"] == report_data
        assert report["citations"] == citations

    _run(_test())


def test_get_report_not_found():
    """无报告时 get_report 应返回 None"""
    import server.db as db_mod

    async def _test():
        result = await db_mod.get_report("nonexistent")
        assert result is None

    _run(_test())


def test_save_report_without_citations():
    """save_report 不传 citations 时 citations 应为 None"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        await db_mod.save_report(aid, {"chapter1": "内容"})

        report = await db_mod.get_report(aid)
        assert report is not None
        assert report["citations"] is None

    _run(_test())


def test_get_report_returns_latest():
    """多次 save_report 时 get_report 应返回最新的一条"""
    import server.db as db_mod

    async def _test():
        aid = db_mod.generate_analysis_id()
        await db_mod.insert_analysis(aid, {"year": 1990, "month": 1, "day": 1, "hour": 12})

        await db_mod.save_report(aid, {"version": 1})
        await db_mod.save_report(aid, {"version": 2})

        report = await db_mod.get_report(aid)
        assert report["report_data"]["version"] == 2

    _run(_test())


# ──────────────────────────── generate_analysis_id ────────────────────────────


def test_generate_analysis_id_format():
    """generate_analysis_id 应以 'ana_' 开头且长度为 16"""
    import server.db as db_mod

    aid = db_mod.generate_analysis_id()
    assert aid.startswith("ana_")
    assert len(aid) == 16


def test_generate_analysis_id_unique():
    """连续生成的 ID 应唯一"""
    import server.db as db_mod

    ids = {db_mod.generate_analysis_id() for _ in range(100)}
    assert len(ids) == 100
