
"""server/chat_service.py 单元测试

覆盖：
1. _estimate_tokens() — 正常/空/中文/英文
2. _extract_analysis_context() — 双源取值（day_master 在顶层 vs validation 下）
3. _load_and_parse_analysis() — JSON 字符串 vs dict
4. _build_messages_list() — 有/无摘要
5. prepare_chat_context() — mock DB + RAG + LLM
6. build_report_context() — 错误路径（NOT_FOUND, ANALYSIS_NOT_COMPLETED）
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

pytest.importorskip("fastapi")

from server.chat_service import (
    ChatContext,
    ReportContext,
    _build_messages_list,
    _estimate_tokens,
    _extract_analysis_context,
    _load_and_parse_analysis,
    build_report_context,
    prepare_chat_context,
)

# ---------------------------------------------------------------------------
# Mock 路径常量
# ---------------------------------------------------------------------------
_PATCH_GET_ANALYSIS = "server.chat_service.get_analysis"
_PATCH_GET_LATEST_SUMMARY = "server.chat_service.get_latest_summary"
_PATCH_GET_MESSAGES_AFTER_ID = "server.chat_service.get_messages_after_id"
_PATCH_INSERT_CHAT_SUMMARY = "server.chat_service.insert_chat_summary"
_PATCH_BUILD_CHAT_SYSTEM_PROMPT = "server.chat_service.build_chat_system_prompt"
_PATCH_BUILD_REPORT_SYSTEM_PROMPT = "server.chat_service.build_report_system_prompt"


# ===================================================================
# 1. _estimate_tokens — 纯函数测试
# ===================================================================


class TestEstimateTokens:
    """_estimate_tokens 纯函数测试。"""

    def test_empty_string(self):
        """空字符串返回 0。"""
        assert _estimate_tokens("") == 0

    def test_none_like(self):
        """None-like 空文本返回 0。"""
        # _estimate_tokens 不接受 None，但空字符串已覆盖

    def test_pure_chinese(self):
        """纯中文文本：约 1.5 字/token。"""
        # 6 个中文字符 → 6 / 1.5 = 4
        result = _estimate_tokens("你好世界测试")
        assert result == 4

    def test_pure_english(self):
        """纯英文文本：约 4 字符/token。"""
        # 8 个英文字符 → 8 / 4 = 2
        result = _estimate_tokens("abcdefgh")
        assert result == 2

    def test_mixed_chinese_english(self):
        """中英混合文本。"""
        # 2 中文 + 4 英文 = 2/1.5 + 4/4 = 1.33 + 1 = 2.33 → 2
        result = _estimate_tokens("测试abcd")
        assert result == 2

    def test_long_text(self):
        """较长文本的 token 估算。"""
        text = "命" * 100  # 100 中文字符 → 100 / 1.5 = 66.67 → 66
        result = _estimate_tokens(text)
        assert result == 66

    def test_only_ascii_digits(self):
        """纯 ASCII 数字。"""
        result = _estimate_tokens("12345678")  # 8 chars / 4 = 2
        assert result == 2

    def test_whitespace(self):
        """空白字符按 other_chars 计算。"""
        result = _estimate_tokens("    ")  # 4 spaces / 4 = 1
        assert result == 1


# ===================================================================
# 2. _extract_analysis_context — 双源取值
# ===================================================================


class TestExtractAnalysisContext:
    """_extract_analysis_context 双源取值测试。"""

    def test_day_master_at_top_level(self):
        """day_master 在 result 顶层时正确提取。"""
        result = {
            "day_master": "丙",
            "pillars": [
                {"gan": "庚", "zhi": "午"},
                {"gan": "辛", "zhi": "巳"},
                {"gan": "丙", "zhi": "寅"},
                {"gan": "壬", "zhi": "辰"},
            ],
            "pattern": {"name": "正官格"},
            "strength": {"wangshuai": {"verdict": "身弱"}},
            "yongshen": {"yongshen": "印"},
        }
        ctx = _extract_analysis_context(result)
        assert ctx["day_master"] == "丙"
        assert "庚午 辛巳 丙寅 壬辰" == ctx["bazi"]

    def test_day_master_under_validation(self):
        """day_master 在 validation 子对象时正确提取（双源回退）。"""
        result = {
            "validation": {"day_master": "甲"},
            "shishen": {
                "pillars": [
                    {"gan": "甲", "zhi": "子"},
                    {"gan": "乙", "zhi": "丑"},
                    {"gan": "丙", "zhi": "寅"},
                    {"gan": "丁", "zhi": "卯"},
                ],
            },
            "pattern": "正印格",  # 字符串形式
            "strength": {},
            "yongshen": "印",  # 字符串形式
        }
        ctx = _extract_analysis_context(result)
        assert ctx["day_master"] == "甲"
        assert "甲子 乙丑 丙寅 丁卯" == ctx["bazi"]

    def test_pattern_as_string(self):
        """pattern 为字符串时包装为 dict。"""
        result = {"pattern": "食神格"}
        ctx = _extract_analysis_context(result)
        assert ctx["pattern"] == {"name": "食神格"}

    def test_pattern_as_empty(self):
        """pattern 为空值时。"""
        result = {"pattern": None}
        ctx = _extract_analysis_context(result)
        assert ctx["pattern"] == {"name": ""}

    def test_wangshuai_in_strength(self):
        """旺衰在 strength.wangshuai 中。"""
        result = {"strength": {"wangshuai": {"verdict": "身旺"}}}
        ctx = _extract_analysis_context(result)
        assert ctx["wangshuai"] == {"verdict": "身旺"}

    def test_wangshuai_at_top_level(self):
        """旺衰在顶层 wangshuai 中（strength 无 wangshuai）。"""
        result = {"strength": {}, "wangshuai": {"verdict": "从弱"}}
        ctx = _extract_analysis_context(result)
        assert ctx["wangshuai"] == {"verdict": "从弱"}

    def test_wangshuai_as_string(self):
        """旺衰为字符串时包装为 dict。"""
        result = {"strength": {}, "wangshuai": "极旺"}
        ctx = _extract_analysis_context(result)
        assert ctx["wangshuai"] == {"verdict": "极旺"}

    def test_yongshen_as_dict(self):
        """用神为 dict 时直接使用。"""
        result = {"yongshen": {"yongshen": "财", "xishen": ["官"]}}
        ctx = _extract_analysis_context(result)
        assert ctx["yongshen"]["yongshen"] == "财"

    def test_yongshen_as_string(self):
        """用神为字符串时包装为 dict。"""
        result = {"yongshen": "印"}
        ctx = _extract_analysis_context(result)
        assert ctx["yongshen"] == {"yongshen": "印"}

    def test_empty_result(self):
        """空 dict 输入不抛异常。"""
        ctx = _extract_analysis_context({})
        assert ctx["day_master"] == ""
        assert ctx["bazi"] == ""
        # all sub-objects: .get(key, {}) returns {} → isinstance dict → assigned as {}
        assert ctx["pattern"] == {}
        assert ctx["wangshuai"] == {}
        assert ctx["yongshen"] == {}

    def test_pillars_with_missing_gan_zhi(self):
        """pillars 中缺少 gan/zhi 的条目被跳过。"""
        result = {
            "pillars": [
                {"gan": "甲", "zhi": "子"},
                {"position": "月柱"},  # 缺 gan/zhi
                {"gan": "丙", "zhi": "寅"},
                {"gan": "丁", "zhi": "卯"},
            ],
        }
        ctx = _extract_analysis_context(result)
        assert ctx["bazi"] == "甲子 丙寅 丁卯"


# ===================================================================
# 3. _load_and_parse_analysis — JSON 字符串 vs dict
# ===================================================================


class TestLoadAndParseAnalysis:
    """_load_and_parse_analysis 测试。"""
    def test_record_not_found(self):
        asyncio.run(self._async_test_record_not_found())

    async def _async_test_record_not_found(self):
        """记录不存在时返回 (None, None)。"""
        with patch(_PATCH_GET_ANALYSIS, new_callable=AsyncMock, return_value=None):
            record, result = await _load_and_parse_analysis("nonexistent_id")
        assert record is None
        assert result is None
    def test_full_result_is_dict(self):
        asyncio.run(self._async_test_full_result_is_dict())

    async def _async_test_full_result_is_dict(self):
        """full_result 已经是 dict 时直接返回。"""
        mock_record = {
            "id": "abc123",
            "full_result": {"status": "completed", "day_master": "丙"},
        }
        with patch(_PATCH_GET_ANALYSIS, new_callable=AsyncMock, return_value=mock_record):
            record, result = await _load_and_parse_analysis("abc123")
        assert record == mock_record
        assert isinstance(result, dict)
        assert result["day_master"] == "丙"
    def test_full_result_is_json_string(self):
        asyncio.run(self._async_test_full_result_is_json_string())

    async def _async_test_full_result_is_json_string(self):
        """full_result 为 JSON 字符串时自动解析。"""
        inner = {"status": "completed", "day_master": "甲"}
        mock_record = {
            "id": "def456",
            "full_result": json.dumps(inner, ensure_ascii=False),
        }
        with patch(_PATCH_GET_ANALYSIS, new_callable=AsyncMock, return_value=mock_record):
            record, result = await _load_and_parse_analysis("def456")
        assert isinstance(result, dict)
        assert result["day_master"] == "甲"
    def test_full_result_is_invalid_json_string(self):
        asyncio.run(self._async_test_full_result_is_invalid_json_string())

    async def _async_test_full_result_is_invalid_json_string(self):
        """full_result 为非法 JSON 字符串时降级为空 dict。"""
        mock_record = {
            "id": "ghi789",
            "full_result": "NOT VALID JSON {{{",
        }
        with patch(_PATCH_GET_ANALYSIS, new_callable=AsyncMock, return_value=mock_record):
            record, result = await _load_and_parse_analysis("ghi789")
        assert isinstance(result, dict)
        assert result == {}


# ===================================================================
# 4. _build_messages_list — 有/无摘要
# ===================================================================


class TestBuildMessagesList:
    """_build_messages_list 测试。"""

    def test_without_summary(self):
        """无摘要时，消息列表为 system + context + user。"""
        messages = _build_messages_list(
            system_prompt="你是命理师",
            summary_content="",
            context_messages=[
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好，有什么问题？"},
            ],
            user_message="我的八字如何？",
        )
        # system + 2 context + user = 4
        assert len(messages) == 4
        assert messages[0] == {"role": "system", "content": "你是命理师"}
        assert messages[1] == {"role": "user", "content": "你好"}
        assert messages[2] == {"role": "assistant", "content": "你好，有什么问题？"}
        assert messages[3] == {"role": "user", "content": "我的八字如何？"}

    def test_with_summary(self):
        """有摘要时，插入摘要系统消息。"""
        messages = _build_messages_list(
            system_prompt="你是命理师",
            summary_content="命主问了身旺身弱的问题",
            context_messages=[
                {"role": "user", "content": "再说说事业"},
            ],
            user_message="详细说说",
        )
        # system + summary + 1 context + user = 4
        assert len(messages) == 4
        assert "对话历史摘要" in messages[1]["content"]
        assert "身旺身弱" in messages[1]["content"]

    def test_empty_context_messages(self):
        """空上下文消息列表。"""
        messages = _build_messages_list(
            system_prompt="prompt",
            summary_content="",
            context_messages=[],
            user_message="第一次问",
        )
        assert len(messages) == 2  # system + user
        assert messages[-1]["role"] == "user"


# ===================================================================
# 5. prepare_chat_context — mock DB + RAG + LLM
# ===================================================================


class TestPrepareChatContext:
    """prepare_chat_context 集成测试（全部 mock）。"""
    def test_analysis_not_found_returns_none(self):
        asyncio.run(self._async_test_analysis_not_found_returns_none())

    async def _async_test_analysis_not_found_returns_none(self):
        """分析记录不存在时返回 None。"""
        with patch(_PATCH_GET_ANALYSIS, new_callable=AsyncMock, return_value=None):
            result = await prepare_chat_context("bad_id", "你好", "ziping", "full")
        assert result is None
    def test_success_path(self):
        asyncio.run(self._async_test_success_path())

    async def _async_test_success_path(self):
        """正常路径：加载分析 + 构建上下文。"""
        mock_record = {
            "id": "test123",
            "full_result": {
                "status": "completed",
                "day_master": "丙",
                "pillars": [
                    {"gan": "庚", "zhi": "午"},
                    {"gan": "辛", "zhi": "巳"},
                    {"gan": "丙", "zhi": "寅"},
                    {"gan": "壬", "zhi": "辰"},
                ],
                "pattern": {"pattern": "正官格"},
                "strength": {"wangshuai": {"verdict": "身弱"}},
                "yongshen": {"yongshen": "印"},
            },
        }
        mock_summary = {"id": 1, "content": "之前的摘要"}
        mock_messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
        ]

        with (
            patch(_PATCH_GET_ANALYSIS, new_callable=AsyncMock, return_value=mock_record),
            patch(_PATCH_GET_LATEST_SUMMARY, new_callable=AsyncMock, return_value=mock_summary),
            patch(_PATCH_GET_MESSAGES_AFTER_ID, new_callable=AsyncMock, return_value=mock_messages),
            patch(_PATCH_BUILD_CHAT_SYSTEM_PROMPT, return_value="系统提示词"),
            patch("server.chat_service._generate_narration", return_value={"overview": "test"}),
            patch("server.chat_service._retrieve_for_chat", new_callable=AsyncMock, return_value=(None, None)),
        ):
            ctx = await prepare_chat_context("test123", "我的格局如何？", "ziping", "full")

        assert ctx is not None
        assert isinstance(ctx, ChatContext)
        assert ctx.result["day_master"] == "丙"
        assert ctx.narration == {"overview": "test"}
        assert ctx.retrieval_results is None
        assert ctx.citations is None
        # messages 应包含 system + summary + context + user
        assert len(ctx.messages) >= 3
        assert ctx.messages[0]["role"] == "system"
        assert ctx.messages[-1]["role"] == "user"
        assert ctx.messages[-1]["content"] == "我的格局如何？"
    def test_with_basic_retrieval_depth_skips_rag(self):
        asyncio.run(self._async_test_with_basic_retrieval_depth_skips_rag())

    async def _async_test_with_basic_retrieval_depth_skips_rag(self):
        """retrieval_depth='basic' 时跳过 RAG 检索。"""
        mock_record = {
            "id": "test456",
            "full_result": {
                "status": "completed",
                "day_master": "甲",
                "pillars": [],
                "pattern": {},
                "strength": {},
                "yongshen": {},
            },
        }

        with (
            patch(_PATCH_GET_ANALYSIS, new_callable=AsyncMock, return_value=mock_record),
            patch(_PATCH_GET_LATEST_SUMMARY, new_callable=AsyncMock, return_value=None),
            patch(_PATCH_GET_MESSAGES_AFTER_ID, new_callable=AsyncMock, return_value=[]),
            patch(_PATCH_BUILD_CHAT_SYSTEM_PROMPT, return_value="prompt"),
            patch("server.chat_service._generate_narration", return_value={}),
        ):
            ctx = await prepare_chat_context("test456", "hello", "ziping", "basic")

        assert ctx is not None
        assert ctx.retrieval_results is None


# ===================================================================
# 6. build_report_context — 错误路径
# ===================================================================


class TestBuildReportContext:
    """build_report_context 错误路径测试。"""
    def test_not_found(self):
        asyncio.run(self._async_test_not_found())

    async def _async_test_not_found(self):
        """记录不存在时返回 (None, 'NOT_FOUND')。"""
        with patch(_PATCH_GET_ANALYSIS, new_callable=AsyncMock, return_value=None):
            ctx, error = await build_report_context("bad_id", "ziping", "full")
        assert ctx is None
        assert error == "NOT_FOUND"
    def test_analysis_not_completed(self):
        asyncio.run(self._async_test_analysis_not_completed())

    async def _async_test_analysis_not_completed(self):
        """分析未完成时返回 (None, 'ANALYSIS_NOT_COMPLETED')。"""
        mock_record = {
            "id": "test789",
            "status": "processing",
            "full_result": {},
        }
        with patch(_PATCH_GET_ANALYSIS, new_callable=AsyncMock, return_value=mock_record):
            ctx, error = await build_report_context("test789", "ziping", "full")
        assert ctx is None
        assert error == "ANALYSIS_NOT_COMPLETED"
    def test_invalid_result(self):
        asyncio.run(self._async_test_invalid_result())

    async def _async_test_invalid_result(self):
        """结果无效时返回 (None, 'INVALID_RESULT')。"""
        mock_record = {
            "id": "test_invalid",
            "status": "completed",
            "full_result": {"status": "error"},  # status != completed
        }
        with patch(_PATCH_GET_ANALYSIS, new_callable=AsyncMock, return_value=mock_record):
            ctx, error = await build_report_context("test_invalid", "ziping", "full")
        assert ctx is None
        assert error == "INVALID_RESULT"
    def test_success_path(self):
        asyncio.run(self._async_test_success_path())

    async def _async_test_success_path(self):
        """正常路径返回 ReportContext。"""
        mock_record = {
            "id": "test_ok",
            "status": "completed",
            "full_result": {
                "status": "completed",
                "day_master": "丙",
                "pillars": [],
                "pattern": {},
                "strength": {"wangshuai": {"verdict": "身弱"}},
                "yongshen": {},
            },
            "birth_json": {},
        }
        with (
            patch(_PATCH_GET_ANALYSIS, new_callable=AsyncMock, return_value=mock_record),
            patch("server.chat_service._generate_narration", return_value={}),
            patch(_PATCH_BUILD_REPORT_SYSTEM_PROMPT, return_value="report prompt"),
        ):
            ctx, error = await build_report_context("test_ok", "ziping", "basic")

        assert error is None
        assert isinstance(ctx, ReportContext)
        assert ctx.system_prompt == "report prompt"
        assert ctx.result["day_master"] == "丙"
    def test_full_result_is_json_string(self):
        asyncio.run(self._async_test_full_result_is_json_string())

    async def _async_test_full_result_is_json_string(self):
        """full_result 为 JSON 字符串时自动解析。"""
        inner = {
            "status": "completed",
            "day_master": "甲",
            "pillars": [],
            "pattern": {},
            "strength": {"wangshuai": {"verdict": "身旺"}},
            "yongshen": {},
        }
        mock_record = {
            "id": "test_json_str",
            "status": "completed",
            "full_result": json.dumps(inner, ensure_ascii=False),
            "birth_json": {},
        }
        with (
            patch(_PATCH_GET_ANALYSIS, new_callable=AsyncMock, return_value=mock_record),
            patch("server.chat_service._generate_narration", return_value={}),
            patch(_PATCH_BUILD_REPORT_SYSTEM_PROMPT, return_value="prompt"),
        ):
            ctx, error = await build_report_context("test_json_str", "ziping", "basic")

        assert error is None
        assert ctx.result["day_master"] == "甲"
    def test_birth_json_is_string(self):
        asyncio.run(self._async_test_birth_json_is_string())

    async def _async_test_birth_json_is_string(self):
        """birth_json 为 JSON 字符串时自动解析。"""
        mock_record = {
            "id": "test_birth_str",
            "status": "completed",
            "full_result": {
                "status": "completed",
                "day_master": "丙",
                "pillars": [],
                "pattern": {},
                "strength": {"wangshuai": {"verdict": "身弱"}},
                "yongshen": {},
            },
            "birth_json": json.dumps({"大运": [{"age": 3}]}, ensure_ascii=False),
        }
        with (
            patch(_PATCH_GET_ANALYSIS, new_callable=AsyncMock, return_value=mock_record),
            patch("server.chat_service._generate_narration", return_value={}),
            patch(_PATCH_BUILD_REPORT_SYSTEM_PROMPT, return_value="prompt"),
        ):
            ctx, error = await build_report_context("test_birth_str", "ziping", "basic")

        assert error is None
        assert ctx.dayun_data is not None
