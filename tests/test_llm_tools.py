
"""server/llm_client.py Function Calling 路径测试

覆盖：
1. chat_completion_with_tools() — 工具调用循环、max rounds、reasoning 降级
2. chat_completion_stream_with_tools() — 流式工具调用、heartbeat 事件
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

pytest.importorskip("fastapi")

from server.llm_client import chat_completion_stream_with_tools, chat_completion_with_tools

# ---------------------------------------------------------------------------
# Mock 路径常量
# ---------------------------------------------------------------------------
_PATCH_POST_WITH_RETRY = "server.llm_client._post_with_retry"
_PATCH_EXECUTE_TOOLS = "server.agents.tools.execute_tools"
_PATCH_LLM_API_KEY = "server.llm_client._LLM_API_KEY"

# ---------------------------------------------------------------------------
# 辅助工厂
# ---------------------------------------------------------------------------


def _make_llm_response(
    content: str = "",
    tool_calls: list[dict] | None = None,
    reasoning_content: str = "",
) -> dict:
    """构造 LLM API 返回的 JSON 数据。"""
    message: dict = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    if reasoning_content:
        message["reasoning_content"] = reasoning_content
    return {"choices": [{"message": message}]}


def _make_tool_call(name: str, args: dict, call_id: str = "call_001") -> dict:
    """构造 OpenAI 格式的 tool_call。"""
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(args, ensure_ascii=False),
        },
    }


def _make_tool_result(call_id: str, content: str = '{"result": "ok"}') -> dict:
    """构造工具执行结果 message。"""
    return {
        "role": "tool",
        "tool_call_id": call_id,
        "content": content,
    }


# ===================================================================
# 1. chat_completion_with_tools 测试
# ===================================================================


class TestChatCompletionWithTools:
    """chat_completion_with_tools 测试。"""

    @pytest.fixture(autouse=True)
    def _set_api_key(self):
        """每个测试前设置 API key。"""
        import server.llm_client as mod
        orig = mod._LLM_API_KEY
        mod._LLM_API_KEY = "sk-test-key"
        yield
        mod._LLM_API_KEY = orig

    @pytest.mark.asyncio
    def test_no_tool_calls_returns_content(self):
        asyncio.run(self._async_test_no_tool_calls_returns_content())

    async def _async_test_no_tool_calls_returns_content(self):
        """LLM 直接返回文本（无工具调用）时，直接返回 content。"""
        llm_data = _make_llm_response(content="你好，我是命理师")
        with patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, return_value=llm_data):
            result = await chat_completion_with_tools(
                messages=[{"role": "user", "content": "你好"}],
                tools=[],
            )

        assert result["content"] == "你好，我是命理师"
        assert result["tool_calls_log"] == []
        assert len(result["messages"]) == 1  # 原始 messages

    @pytest.mark.asyncio
    def test_single_tool_call_round(self):
        asyncio.run(self._async_test_single_tool_call_round())

    async def _async_test_single_tool_call_round(self):
        """单轮工具调用后返回最终内容。"""
        # 第 1 轮：LLM 返回 tool_call
        tool_call = _make_tool_call("paipan", {"solar_datetime": "1990-05-15 08:30", "gender": "男"}, "call_1")
        round1_data = _make_llm_response(tool_calls=[tool_call])

        # 第 2 轮：LLM 返回最终文本
        round2_data = _make_llm_response(content="根据排盘结果，你的八字是...")

        with (
            patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, side_effect=[round1_data, round2_data]),
            patch(_PATCH_EXECUTE_TOOLS, new_callable=AsyncMock, return_value=[
                _make_tool_result("call_1", '{"八字": "庚午 辛巳 丙寅 壬辰"}'),
            ]),
        ):
            result = await chat_completion_with_tools(
                messages=[{"role": "user", "content": "帮我排盘"}],
                tools=[{"type": "function", "function": {"name": "paipan"}}],
            )

        assert result["content"] == "根据排盘结果，你的八字是..."
        assert len(result["tool_calls_log"]) == 1
        assert result["tool_calls_log"][0]["name"] == "paipan"
        assert result["tool_calls_log"][0]["id"] == "call_1"
        # messages 应包含：original + assistant(tool_call) + tool result
        assert len(result["messages"]) == 3

    @pytest.mark.asyncio
    def test_multi_round_tool_calls(self):
        asyncio.run(self._async_test_multi_round_tool_calls())

    async def _async_test_multi_round_tool_calls(self):
        """多轮工具调用（2 轮）后返回最终内容。"""
        tc1 = _make_tool_call("paipan", {"solar_datetime": "1990-05-15 08:30", "gender": "男"}, "call_1")
        tc2 = _make_tool_call("query_geju", {"bazi": "庚午 辛巳 丙寅 壬辰", "day_master": "丙"}, "call_2")

        round1 = _make_llm_response(tool_calls=[tc1])
        round2 = _make_llm_response(tool_calls=[tc2])
        round3 = _make_llm_response(content="格局分析结果...")

        with (
            patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, side_effect=[round1, round2, round3]),
            patch(_PATCH_EXECUTE_TOOLS, new_callable=AsyncMock, side_effect=[
                [_make_tool_result("call_1", '{"八字": "庚午 辛巳 丙寅 壬辰"}')],
                [_make_tool_result("call_2", '{"格局": "正官格"}')],
            ]),
        ):
            result = await chat_completion_with_tools(
                messages=[{"role": "user", "content": "排盘并查格局"}],
                tools=[],
            )

        assert result["content"] == "格局分析结果..."
        assert len(result["tool_calls_log"]) == 2
        assert result["tool_calls_log"][0]["name"] == "paipan"
        assert result["tool_calls_log"][1]["name"] == "query_geju"

    @pytest.mark.asyncio
    def test_max_tool_rounds_exceeded(self):
        asyncio.run(self._async_test_max_tool_rounds_exceeded())

    async def _async_test_max_tool_rounds_exceeded(self):
        """达到最大工具调用轮次时强制返回。"""
        tc = _make_tool_call("paipan", {"solar_datetime": "1990-05-15 08:30", "gender": "男"}, "call_1")
        # 每轮都返回 tool_call，永不返回纯文本
        always_tool = _make_llm_response(tool_calls=[tc])

        with (
            patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, return_value=always_tool),
            patch(_PATCH_EXECUTE_TOOLS, new_callable=AsyncMock, return_value=[
                _make_tool_result("call_1", '{"八字": "test"}'),
            ]),
        ):
            result = await chat_completion_with_tools(
                messages=[{"role": "user", "content": "test"}],
                tools=[],
                max_tool_rounds=2,
            )

        # 应该达到 max_tool_rounds=2 后强制返回
        assert "轮次已达上限" in result["content"] or result["content"] != ""
        assert len(result["tool_calls_log"]) >= 2

    @pytest.mark.asyncio
    def test_reasoning_fallback(self):
        asyncio.run(self._async_test_reasoning_fallback())

    async def _async_test_reasoning_fallback(self):
        """content 为空但有 reasoning_content 时降级。"""
        llm_data = _make_llm_response(content="", reasoning_content="这是推理过程")
        with patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, return_value=llm_data):
            result = await chat_completion_with_tools(
                messages=[{"role": "user", "content": "test"}],
                tools=[],
            )

        assert result["content"] == "这是推理过程"

    @pytest.mark.asyncio
    def test_empty_choices_raises(self):
        asyncio.run(self._async_test_empty_choices_raises())

    async def _async_test_empty_choices_raises(self):
        """LLM 返回空 choices 时抛异常。"""
        llm_data = {"choices": []}
        with patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, return_value=llm_data):
            with pytest.raises(RuntimeError, match="空 choices"):
                await chat_completion_with_tools(
                    messages=[{"role": "user", "content": "test"}],
                    tools=[],
                )

    @pytest.mark.asyncio
    def test_no_api_key_raises(self):
        asyncio.run(self._async_test_no_api_key_raises())

    async def _async_test_no_api_key_raises(self):
        """未配置 API key 时抛异常。"""
        import server.llm_client as mod
        mod._LLM_API_KEY = ""
        with pytest.raises(RuntimeError, match="LLM API key 未配置"):
            await chat_completion_with_tools(
                messages=[{"role": "user", "content": "test"}],
                tools=[],
            )

    @pytest.mark.asyncio
    def test_tool_calls_log_records_result(self):
        asyncio.run(self._async_test_tool_calls_log_records_result())

    async def _async_test_tool_calls_log_records_result(self):
        """工具调用日志应记录工具执行结果。"""
        tc = _make_tool_call("query_geju", {"bazi": "test", "day_master": "丙"}, "call_log")
        round1 = _make_llm_response(tool_calls=[tc])
        round2 = _make_llm_response(content="done")

        tool_result_content = '{"格局": "正官格", "置信度": "85%"}'
        with (
            patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, side_effect=[round1, round2]),
            patch(_PATCH_EXECUTE_TOOLS, new_callable=AsyncMock, return_value=[
                _make_tool_result("call_log", tool_result_content),
            ]),
        ):
            result = await chat_completion_with_tools(
                messages=[{"role": "user", "content": "test"}],
                tools=[],
            )

        log_entry = result["tool_calls_log"][0]
        assert log_entry["name"] == "query_geju"
        assert log_entry["round"] == 1
        assert log_entry["result"] == tool_result_content

    @pytest.mark.asyncio
    def test_multiple_tool_calls_in_one_round(self):
        asyncio.run(self._async_test_multiple_tool_calls_in_one_round())

    async def _async_test_multiple_tool_calls_in_one_round(self):
        """一轮中返回多个 tool_calls 时全部执行。"""
        tc1 = _make_tool_call("paipan", {"solar_datetime": "1990-05-15 08:30", "gender": "男"}, "call_a")
        tc2 = _make_tool_call("query_shensha", {"bazi": "test", "gender": "男"}, "call_b")
        round1 = _make_llm_response(tool_calls=[tc1, tc2])
        round2 = _make_llm_response(content="分析完毕")

        with (
            patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, side_effect=[round1, round2]),
            patch(_PATCH_EXECUTE_TOOLS, new_callable=AsyncMock, return_value=[
                _make_tool_result("call_a", '{"八字": "test"}'),
                _make_tool_result("call_b", '{"神煞": []}'),
            ]),
        ):
            result = await chat_completion_with_tools(
                messages=[{"role": "user", "content": "test"}],
                tools=[],
            )

        assert len(result["tool_calls_log"]) == 2
        assert result["tool_calls_log"][0]["name"] == "paipan"
        assert result["tool_calls_log"][1]["name"] == "query_shensha"


# ===================================================================
# 2. chat_completion_stream_with_tools 测试
# ===================================================================


class TestChatCompletionStreamWithTools:
    """chat_completion_stream_with_tools 测试。"""

    @pytest.fixture(autouse=True)
    def _set_api_key(self):
        """每个测试前设置 API key。"""
        import server.llm_client as mod
        orig = mod._LLM_API_KEY
        mod._LLM_API_KEY = "sk-test-key"
        yield
        mod._LLM_API_KEY = orig

    @pytest.mark.asyncio
    def test_no_tool_calls_yields_tokens(self):
        asyncio.run(self._async_test_no_tool_calls_yields_tokens())

    async def _async_test_no_tool_calls_yields_tokens(self):
        """无工具调用时，直接流式输出 token。"""
        llm_data = _make_llm_response(content="你好世界")
        with patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, return_value=llm_data):
            events = []
            async for event in chat_completion_stream_with_tools(
                messages=[{"role": "user", "content": "你好"}],
                tools=[],
            ):
                events.append(event)

        # 应有 heartbeat + token chunks + done
        types = [e["type"] for e in events]
        assert "heartbeat" in types
        assert "token" in types
        assert "done" in types

        # token 内容应包含 "你好世界"
        token_content = "".join(e["content"] for e in events if e["type"] == "token")
        assert "你好世界" in token_content

    @pytest.mark.asyncio
    def test_heartbeat_events(self):
        asyncio.run(self._async_test_heartbeat_events())

    async def _async_test_heartbeat_events(self):
        """每轮工具调用都应发出 heartbeat 事件。"""
        tc = _make_tool_call("paipan", {"solar_datetime": "1990-05-15 08:30", "gender": "男"}, "call_hb")
        round1 = _make_llm_response(tool_calls=[tc])
        round2 = _make_llm_response(content="done")

        with (
            patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, side_effect=[round1, round2]),
            patch(_PATCH_EXECUTE_TOOLS, new_callable=AsyncMock, return_value=[
                _make_tool_result("call_hb", '{"八字": "test"}'),
            ]),
        ):
            events = []
            async for event in chat_completion_stream_with_tools(
                messages=[{"role": "user", "content": "test"}],
                tools=[],
            ):
                events.append(event)

        heartbeats = [e for e in events if e["type"] == "heartbeat"]
        assert len(heartbeats) >= 2  # 至少 2 个：一轮开始 + 工具执行前

    @pytest.mark.asyncio
    def test_tool_call_and_result_events(self):
        asyncio.run(self._async_test_tool_call_and_result_events())

    async def _async_test_tool_call_and_result_events(self):
        """工具调用应产生 tool_call 和 tool_result 事件。"""
        tc = _make_tool_call("query_geju", {"bazi": "test", "day_master": "丙"}, "call_tc")
        round1 = _make_llm_response(tool_calls=[tc])
        round2 = _make_llm_response(content="分析结果")

        with (
            patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, side_effect=[round1, round2]),
            patch(_PATCH_EXECUTE_TOOLS, new_callable=AsyncMock, return_value=[
                _make_tool_result("call_tc", '{"格局": "正官格"}'),
            ]),
        ):
            events = []
            async for event in chat_completion_stream_with_tools(
                messages=[{"role": "user", "content": "test"}],
                tools=[],
            ):
                events.append(event)

        tool_call_events = [e for e in events if e["type"] == "tool_call"]
        tool_result_events = [e for e in events if e["type"] == "tool_result"]

        assert len(tool_call_events) == 1
        # tool_call content 应为 JSON 字符串，包含工具名
        tc_data = json.loads(tool_call_events[0]["content"])
        assert tc_data["name"] == "query_geju"

        assert len(tool_result_events) == 1
        assert "正官格" in tool_result_events[0]["content"]

    @pytest.mark.asyncio
    def test_max_rounds_exceeded(self):
        asyncio.run(self._async_test_max_rounds_exceeded())

    async def _async_test_max_rounds_exceeded(self):
        """达到最大轮次时输出提示并结束。"""
        tc = _make_tool_call("paipan", {"solar_datetime": "test", "gender": "男"}, "call_mr")
        always_tool = _make_llm_response(tool_calls=[tc])

        with (
            patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, return_value=always_tool),
            patch(_PATCH_EXECUTE_TOOLS, new_callable=AsyncMock, return_value=[
                _make_tool_result("call_mr", '{"八字": "test"}'),
            ]),
        ):
            events = []
            async for event in chat_completion_stream_with_tools(
                messages=[{"role": "user", "content": "test"}],
                tools=[],
                max_tool_rounds=2,
            ):
                events.append(event)

        token_events = [e for e in events if e["type"] == "token"]
        done_events = [e for e in events if e["type"] == "done"]
        assert len(token_events) >= 1
        assert "轮次已达上限" in token_events[-1]["content"]
        assert len(done_events) == 1

    @pytest.mark.asyncio
    def test_reasoning_fallback_in_stream(self):
        asyncio.run(self._async_test_reasoning_fallback_in_stream())

    async def _async_test_reasoning_fallback_in_stream(self):
        """stream 中 content 为空但有 reasoning_content 时降级。"""
        llm_data = _make_llm_response(content="", reasoning_content="推理结果")
        with patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, return_value=llm_data):
            events = []
            async for event in chat_completion_stream_with_tools(
                messages=[{"role": "user", "content": "test"}],
                tools=[],
            ):
                events.append(event)

        token_events = [e for e in events if e["type"] == "token"]
        token_content = "".join(e["content"] for e in token_events)
        assert "推理结果" in token_content

    @pytest.mark.asyncio
    def test_no_api_key_raises(self):
        asyncio.run(self._async_test_no_api_key_raises())

    async def _async_test_no_api_key_raises(self):
        """未配置 API key 时抛异常。"""
        import server.llm_client as mod
        mod._LLM_API_KEY = ""

        with pytest.raises(RuntimeError, match="LLM API key 未配置"):
            async for _ in chat_completion_stream_with_tools(
                messages=[{"role": "user", "content": "test"}],
                tools=[],
            ):
                pass

    @pytest.mark.asyncio
    def test_empty_choices_raises(self):
        asyncio.run(self._async_test_empty_choices_raises())

    async def _async_test_empty_choices_raises(self):
        """LLM 返回空 choices 时抛异常。"""
        llm_data = {"choices": []}
        with patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, return_value=llm_data):
            with pytest.raises(RuntimeError, match="空 choices"):
                async for _ in chat_completion_stream_with_tools(
                    messages=[{"role": "user", "content": "test"}],
                    tools=[],
                ):
                    pass

    @pytest.mark.asyncio
    def test_final_reply_chunked_output(self):
        asyncio.run(self._async_test_final_reply_chunked_output())

    async def _async_test_final_reply_chunked_output(self):
        """最终回复应按 20 字符分块输出。"""
        long_content = "这是一段较长的命理分析文本，用于测试分块输出效果。" * 3  # > 60 chars
        llm_data = _make_llm_response(content=long_content)
        with patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, return_value=llm_data):
            events = []
            async for event in chat_completion_stream_with_tools(
                messages=[{"role": "user", "content": "test"}],
                tools=[],
            ):
                events.append(event)

        token_events = [e for e in events if e["type"] == "token"]
        # 每个 token chunk 应 <= 20 字符
        for te in token_events:
            assert len(te["content"]) <= 20
        # 拼接后应与原文一致
        reconstructed = "".join(e["content"] for e in token_events)
        assert reconstructed == long_content

    @pytest.mark.asyncio
    def test_multi_round_with_events(self):
        asyncio.run(self._async_test_multi_round_with_events())

    async def _async_test_multi_round_with_events(self):
        """多轮工具调用的完整事件序列。"""
        tc = _make_tool_call("paipan", {"solar_datetime": "test", "gender": "男"}, "call_multi")
        round1 = _make_llm_response(tool_calls=[tc])
        round2 = _make_llm_response(content="最终回答")

        with (
            patch(_PATCH_POST_WITH_RETRY, new_callable=AsyncMock, side_effect=[round1, round2]),
            patch(_PATCH_EXECUTE_TOOLS, new_callable=AsyncMock, return_value=[
                _make_tool_result("call_multi", '{"八字": "甲子 乙丑 丙寅 丁卯"}'),
            ]),
        ):
            events = []
            async for event in chat_completion_stream_with_tools(
                messages=[{"role": "user", "content": "test"}],
                tools=[],
            ):
                events.append(event)

        types = [e["type"] for e in events]
        # 事件序列应包含：heartbeat, tool_call, heartbeat, tool_result, ..., token..., done
        assert types[0] == "heartbeat"
        assert "tool_call" in types
        assert "tool_result" in types
        assert "token" in types
        assert types[-1] == "done"
