"""server/llm.py 单元测试 — 覆盖 chat_completion、流式输出、配置管理"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# --------------------------------------------------------------------------- #
# 辅助工厂
# --------------------------------------------------------------------------- #

def _make_response(status_code: int = 200, json_data: dict | None = None) -> MagicMock:
    """构造 mock httpx.Response"""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        from httpx import HTTPStatusError, Request, Response
        req = Request("POST", "https://example.com")
        raw = Response(status_code, request=req)
        resp.raise_for_status.side_effect = HTTPStatusError(
            f"HTTP {status_code}", request=req, response=raw,
        )
    return resp


def _make_stream_response(lines: list[str]) -> AsyncMock:
    """构造 mock 流式响应（aiter_lines）"""
    resp = AsyncMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()

    async def _aiter_lines():
        for line in lines:
            yield line

    resp.aiter_lines = _aiter_lines
    # 支持 async context manager (client.stream)
    stream_ctx = AsyncMock()
    stream_ctx.__aenter__ = AsyncMock(return_value=resp)
    stream_ctx.__aexit__ = AsyncMock(return_value=False)
    return stream_ctx


def _make_mock_client(stream_ctx) -> MagicMock:
    """构造支持 async with 的 mock httpx 客户端，stream 返回 async context manager"""
    mock_client = MagicMock()
    # MagicMock.__aenter__ 默认返回新 mock，需显式返回自身
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    # stream 返回 async context manager（非 coroutine）
    mock_client.stream = MagicMock(return_value=stream_ctx)
    return mock_client


# --------------------------------------------------------------------------- #
# update_llm_config 测试
# --------------------------------------------------------------------------- #

class TestUpdateLlmConfig:

    def setup_method(self):
        """每个测试前重置全局配置"""
        import server.llm as llm_mod
        self._orig_key = llm_mod._LLM_API_KEY
        self._orig_base = llm_mod._LLM_API_BASE
        self._orig_model = llm_mod._LLM_MODEL

    def teardown_method(self):
        import server.llm as llm_mod
        llm_mod._LLM_API_KEY = self._orig_key
        llm_mod._LLM_API_BASE = self._orig_base
        llm_mod._LLM_MODEL = self._orig_model

    def test_update_api_key(self):
        import server.llm as llm_mod
        from server.llm import update_llm_config
        update_llm_config(api_key="sk-test-123")
        assert llm_mod._LLM_API_KEY == "sk-test-123"

    def test_update_api_key_too_long_raises(self):
        from server.llm import update_llm_config
        with pytest.raises(ValueError, match="api_key 格式不合法"):
            update_llm_config(api_key="x" * 513)

    def test_update_api_key_non_string_raises(self):
        from server.llm import update_llm_config
        with pytest.raises(ValueError, match="api_key 格式不合法"):
            update_llm_config(api_key=12345)  # type: ignore[arg-type]

    def test_update_api_base_valid(self):
        import server.llm as llm_mod
        from server.llm import update_llm_config
        update_llm_config(api_base="https://api.deepseek.com/v1")
        assert llm_mod._LLM_API_BASE == "https://api.deepseek.com/v1"

    def test_update_api_base_with_port(self):
        import server.llm as llm_mod
        from server.llm import update_llm_config
        update_llm_config(api_base="http://localhost:11434/v1")
        assert llm_mod._LLM_API_BASE == "http://localhost:11434/v1"

    def test_update_api_base_empty_string(self):
        """空字符串应被接受（清除自定义 base）"""
        import server.llm as llm_mod
        from server.llm import update_llm_config
        update_llm_config(api_base="")
        assert llm_mod._LLM_API_BASE == ""

    def test_update_api_base_invalid_raises(self):
        from server.llm import update_llm_config
        with pytest.raises(ValueError, match="api_base URL 格式不合法"):
            update_llm_config(api_base="ftp://invalid")

    def test_update_api_base_not_string_raises(self):
        from server.llm import update_llm_config
        with pytest.raises(ValueError, match="api_base 必须为字符串"):
            update_llm_config(api_base=123)  # type: ignore[arg-type]

    def test_update_model_valid(self):
        import server.llm as llm_mod
        from server.llm import update_llm_config
        update_llm_config(model="deepseek-chat")
        assert llm_mod._LLM_MODEL == "deepseek-chat"

    def test_update_model_with_slash(self):
        import server.llm as llm_mod
        from server.llm import update_llm_config
        update_llm_config(model="org/model-name")
        assert llm_mod._LLM_MODEL == "org/model-name"

    def test_update_model_invalid_chars_raises(self):
        from server.llm import update_llm_config
        with pytest.raises(ValueError, match="model 名称格式不合法"):
            update_llm_config(model="model with spaces")

    def test_update_model_special_chars_raises(self):
        from server.llm import update_llm_config
        with pytest.raises(ValueError, match="model 名称格式不合法"):
            update_llm_config(model="model@#$")

    def test_update_none_params_no_change(self):
        import server.llm as llm_mod
        from server.llm import update_llm_config
        orig_key = llm_mod._LLM_API_KEY
        update_llm_config()
        assert llm_mod._LLM_API_KEY == orig_key


# --------------------------------------------------------------------------- #
# is_llm_configured 测试
# --------------------------------------------------------------------------- #

class TestIsLlmConfigured:

    def setup_method(self):
        import server.llm as llm_mod
        self._orig_key = llm_mod._LLM_API_KEY

    def teardown_method(self):
        import server.llm as llm_mod
        llm_mod._LLM_API_KEY = self._orig_key

    def test_configured_when_key_set(self):
        import server.llm as llm_mod
        llm_mod._LLM_API_KEY = "sk-test"
        assert llm_mod.is_llm_configured() is True

    def test_not_configured_when_key_empty(self):
        import server.llm as llm_mod
        llm_mod._LLM_API_KEY = ""
        assert llm_mod.is_llm_configured() is False


# --------------------------------------------------------------------------- #
# get_llm_config 测试
# --------------------------------------------------------------------------- #

class TestGetLlmConfig:

    def test_returns_dict_with_expected_keys(self):
        from server.llm import get_llm_config
        cfg = get_llm_config()
        assert "api_base" in cfg
        assert "api_key_set" in cfg
        assert "model" in cfg

    def test_api_key_set_reflects_state(self):
        import server.llm as llm_mod
        from server.llm import get_llm_config
        orig = llm_mod._LLM_API_KEY
        try:
            llm_mod._LLM_API_KEY = "sk-abc"
            assert get_llm_config()["api_key_set"] is True
            llm_mod._LLM_API_KEY = ""
            assert get_llm_config()["api_key_set"] is False
        finally:
            llm_mod._LLM_API_KEY = orig


# --------------------------------------------------------------------------- #
# chat_completion 测试
# --------------------------------------------------------------------------- #

class TestChatCompletion:

    def setup_method(self):
        import server.llm as llm_mod
        self._orig_key = llm_mod._LLM_API_KEY
        llm_mod._LLM_API_KEY = "sk-test-key"

    def teardown_method(self):
        import server.llm as llm_mod
        llm_mod._LLM_API_KEY = self._orig_key


    def test_normal_call(self):
        """正常调用：返回 content"""
        asyncio.run(self._async_test_normal_call())

    async def _async_test_normal_call(self):
        """正常调用：返回 content"""
        from server.llm import chat_completion

        resp_data = {
            "choices": [{"message": {"content": "你好，我是命理师"}}],
        }
        mock_resp = _make_response(200, resp_data)
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client):
            result = await chat_completion([{"role": "user", "content": "测试"}])

        assert result == "你好，我是命理师"


    def test_no_api_key_raises(self):
        """未配置 API key 时抛出 RuntimeError"""
        asyncio.run(self._async_test_no_api_key_raises())

    async def _async_test_no_api_key_raises(self):
        """未配置 API key 时抛出 RuntimeError"""
        import server.llm as llm_mod
        llm_mod._LLM_API_KEY = ""

        with pytest.raises(RuntimeError, match="LLM API key 未配置"):
            await llm_mod.chat_completion([{"role": "user", "content": "测试"}])


    def test_429_retry_then_success(self):
        """429 限流后重试成功"""
        asyncio.run(self._async_test_429_retry_then_success())

    async def _async_test_429_retry_then_success(self):
        """429 限流后重试成功"""
        from server.llm import chat_completion

        resp_429 = _make_response(429)
        resp_ok_data = {"choices": [{"message": {"content": "重试成功"}}]}
        resp_ok = _make_response(200, resp_ok_data)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=[resp_429, resp_ok])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client), \
             patch("server.llm.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await chat_completion([{"role": "user", "content": "测试"}])

        assert result == "重试成功"
        mock_sleep.assert_called_once()  # 确认 sleep 被调用一次


    def test_429_exhausted_retries(self):
        """429 连续超过最大重试次数后仍失败"""
        asyncio.run(self._async_test_429_exhausted_retries())

    async def _async_test_429_exhausted_retries(self):
        """429 连续超过最大重试次数后仍失败"""
        from server.llm import chat_completion

        resp_429 = _make_response(429)
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=resp_429)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client), \
             patch("server.llm.asyncio.sleep", new_callable=AsyncMock):
            # 429 不触发 raise_for_status（代码中 continue 跳过了），
            # 但超过 max_retries 后循环结束，抛出 "unreachable"
            # 实际上 429 会 continue 4次（attempt 0~3），然后循环结束
            # 但 429 不调用 raise_for_status，所以不会抛 HTTPStatusError
            # 代码逻辑：for attempt in range(4)，每次都 continue，
            # 循环结束后执行 raise RuntimeError("unreachable")
            with pytest.raises(RuntimeError, match="unreachable"):
                await chat_completion([{"role": "user", "content": "测试"}])


    def test_empty_content_with_reasoning_fallback(self):
        """content 为空但有 reasoning_content 时降级返回 reasoning"""
        asyncio.run(self._async_test_empty_content_with_reasoning_fallback())

    async def _async_test_empty_content_with_reasoning_fallback(self):
        """content 为空但有 reasoning_content 时降级返回 reasoning"""
        from server.llm import chat_completion

        resp_data = {
            "choices": [{"message": {
                "content": None,
                "reasoning_content": "这是推理过程",
            }}],
        }
        mock_resp = _make_response(200, resp_data)
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client):
            result = await chat_completion([{"role": "user", "content": "测试"}])

        assert result == "这是推理过程"


    def test_empty_content_no_reasoning_raises(self):
        """content 和 reasoning_content 都为空时，bump max_tokens 后仍然为空则抛异常"""
        asyncio.run(self._async_test_empty_content_no_reasoning_raises())

    async def _async_test_empty_content_no_reasoning_raises(self):
        """content 和 reasoning_content 都为空时，bump max_tokens 后仍然为空则抛异常"""
        from server.llm import chat_completion

        resp_data = {
            "choices": [{"message": {"content": None, "reasoning_content": ""}}],
        }
        mock_resp = _make_response(200, resp_data)
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="LLM 返回空 content"):
                await chat_completion([{"role": "user", "content": "测试"}])


    def test_empty_choices_raises(self):
        """返回空 choices 时抛异常"""
        asyncio.run(self._async_test_empty_choices_raises())

    async def _async_test_empty_choices_raises(self):
        """返回空 choices 时抛异常"""
        from server.llm import chat_completion

        resp_data = {"choices": []}
        mock_resp = _make_response(200, resp_data)
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="LLM 返回空 choices"):
                await chat_completion([{"role": "user", "content": "测试"}])


    def test_401_raises_auth_error(self):
        """401 认证失败"""
        asyncio.run(self._async_test_401_raises_auth_error())

    async def _async_test_401_raises_auth_error(self):
        """401 认证失败"""
        from server.llm import chat_completion

        resp_401 = _make_response(401)
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=resp_401)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="认证失败"):
                await chat_completion([{"role": "user", "content": "测试"}])


    def test_500_retry_then_success(self):
        """500 服务端错误后重试成功"""
        asyncio.run(self._async_test_500_retry_then_success())

    async def _async_test_500_retry_then_success(self):
        """500 服务端错误后重试成功"""
        from server.llm import chat_completion

        resp_500 = _make_response(500)
        resp_ok_data = {"choices": [{"message": {"content": "服务恢复"}}]}
        resp_ok = _make_response(200, resp_ok_data)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=[resp_500, resp_ok])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client), \
             patch("server.llm.asyncio.sleep", new_callable=AsyncMock):
            result = await chat_completion([{"role": "user", "content": "测试"}])

        assert result == "服务恢复"


# --------------------------------------------------------------------------- #
# chat_completion_stream_typed 测试
# --------------------------------------------------------------------------- #

class TestChatCompletionStreamTyped:

    def setup_method(self):
        import server.llm as llm_mod
        self._orig_key = llm_mod._LLM_API_KEY
        llm_mod._LLM_API_KEY = "sk-test-key"

    def teardown_method(self):
        import server.llm as llm_mod
        llm_mod._LLM_API_KEY = self._orig_key


    def test_normal_stream(self):
        """正常流式输出：区分 reasoning 和 token"""
        asyncio.run(self._async_test_normal_stream())

    async def _async_test_normal_stream(self):
        """正常流式输出：区分 reasoning 和 token"""
        from server.llm import chat_completion_stream_typed

        sse_lines = [
            'data: {"choices":[{"delta":{"reasoning_content":"让我想想"}}]}',
            'data: {"choices":[{"delta":{"reasoning_content":"，分析一下"}}]}',
            'data: {"choices":[{"delta":{"content":"你好"}}]}',
            'data: {"choices":[{"delta":{"content":"世界"}}]}',
            'data: [DONE]',
        ]
        stream_resp = _make_stream_response(sse_lines)
        mock_client = _make_mock_client(stream_resp)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client):
            results = []
            async for chunk in chat_completion_stream_typed(
                [{"role": "user", "content": "测试"}],
            ):
                results.append(chunk)

        # 应该有 2 个 reasoning + 2 个 token + 1 个降级 token（reasoning_buffer 汇总）
        reasoning_chunks = [c for c in results if c["type"] == "reasoning"]
        token_chunks = [c for c in results if c["type"] == "token"]
        assert len(reasoning_chunks) == 2
        assert reasoning_chunks[0]["content"] == "让我想想"
        assert len(token_chunks) == 3  # 2个原始 + 1个降级汇总


    def test_reasoning_only_fallback(self):
        """只有 reasoning_content 没有 content 时，降级为 token 输出"""
        asyncio.run(self._async_test_reasoning_only_fallback())

    async def _async_test_reasoning_only_fallback(self):
        """只有 reasoning_content 没有 content 时，降级为 token 输出"""
        from server.llm import chat_completion_stream_typed

        sse_lines = [
            'data: {"choices":[{"delta":{"reasoning_content":"推理结果"}}]}',
            'data: [DONE]',
        ]
        stream_resp = _make_stream_response(sse_lines)
        mock_client = _make_mock_client(stream_resp)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client):
            results = []
            async for chunk in chat_completion_stream_typed(
                [{"role": "user", "content": "测试"}],
            ):
                results.append(chunk)

        # 1 个 reasoning + 1 个降级 token（汇总 reasoning_buffer）
        reasoning = [c for c in results if c["type"] == "reasoning"]
        tokens = [c for c in results if c["type"] == "token"]
        assert len(reasoning) == 1
        assert reasoning[0]["content"] == "推理结果"
        # 降级：reasoning_buffer 被作为 token 输出
        assert len(tokens) == 1
        assert tokens[0]["content"] == "推理结果"


    def test_no_content_raises(self):
        """流式返回无任何内容时抛异常"""
        asyncio.run(self._async_test_no_content_raises())

    async def _async_test_no_content_raises(self):
        """流式返回无任何内容时抛异常"""
        from server.llm import chat_completion_stream_typed

        sse_lines = [
            'data: {"choices":[{"delta":{}}]}',
            'data: [DONE]',
        ]
        stream_resp = _make_stream_response(sse_lines)
        mock_client = _make_mock_client(stream_resp)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client):
            results = []
            with pytest.raises(RuntimeError, match="LLM 流式返回无 content"):
                async for chunk in chat_completion_stream_typed(
                    [{"role": "user", "content": "测试"}],
                ):
                    results.append(chunk)


    def test_no_api_key_raises(self):
        """未配置 key 时抛异常"""
        asyncio.run(self._async_test_no_api_key_raises())

    async def _async_test_no_api_key_raises(self):
        """未配置 key 时抛异常"""
        import server.llm as llm_mod
        llm_mod._LLM_API_KEY = ""

        with pytest.raises(RuntimeError, match="LLM API key 未配置"):
            async for _ in llm_mod.chat_completion_stream_typed(
                [{"role": "user", "content": "测试"}],
            ):
                pass


    def test_malformed_lines_skipped(self):
        """畸形 JSON 行被跳过"""
        asyncio.run(self._async_test_malformed_lines_skipped())

    async def _async_test_malformed_lines_skipped(self):
        """畸形 JSON 行被跳过"""
        from server.llm import chat_completion_stream_typed

        sse_lines = [
            'data: {invalid json',
            'data: {"choices":[{"delta":{"content":"正常"}}]}',
            'data: [DONE]',
        ]
        stream_resp = _make_stream_response(sse_lines)
        mock_client = _make_mock_client(stream_resp)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client):
            results = []
            async for chunk in chat_completion_stream_typed(
                [{"role": "user", "content": "测试"}],
            ):
                results.append(chunk)

        tokens = [c for c in results if c["type"] == "token"]
        assert len(tokens) >= 1
        assert tokens[0]["content"] == "正常"


# --------------------------------------------------------------------------- #
# chat_completion_stream（非 typed 版本）测试
# --------------------------------------------------------------------------- #

class TestChatCompletionStream:

    def setup_method(self):
        import server.llm as llm_mod
        self._orig_key = llm_mod._LLM_API_KEY
        llm_mod._LLM_API_KEY = "sk-test-key"

    def teardown_method(self):
        import server.llm as llm_mod
        llm_mod._LLM_API_KEY = self._orig_key


    def test_normal_stream_yields_content(self):
        """正常流式输出 yield content 字符串"""
        asyncio.run(self._async_test_normal_stream_yields_content())

    async def _async_test_normal_stream_yields_content(self):
        """正常流式输出 yield content 字符串"""
        from server.llm import chat_completion_stream

        sse_lines = [
            'data: {"choices":[{"delta":{"content":"你"}}]}',
            'data: {"choices":[{"delta":{"content":"好"}}]}',
            'data: [DONE]',
        ]
        stream_resp = _make_stream_response(sse_lines)
        mock_client = _make_mock_client(stream_resp)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client):
            results = []
            async for chunk in chat_completion_stream(
                [{"role": "user", "content": "测试"}],
            ):
                results.append(chunk)

        assert results == ["你", "好"]


    def test_reasoning_content_also_yielded(self):
        """reasoning_content 也被 yield"""
        asyncio.run(self._async_test_reasoning_content_also_yielded())

    async def _async_test_reasoning_content_also_yielded(self):
        """reasoning_content 也被 yield"""
        from server.llm import chat_completion_stream

        sse_lines = [
            'data: {"choices":[{"delta":{"reasoning_content":"思考"}}]}',
            'data: {"choices":[{"delta":{"content":"答案"}}]}',
            'data: [DONE]',
        ]
        stream_resp = _make_stream_response(sse_lines)
        mock_client = _make_mock_client(stream_resp)

        with patch("server.llm.httpx.AsyncClient", return_value=mock_client):
            results = []
            async for chunk in chat_completion_stream(
                [{"role": "user", "content": "测试"}],
            ):
                results.append(chunk)

        assert "思考" in results
        assert "答案" in results


# --------------------------------------------------------------------------- #
# _get_year_ganzhi / _get_month_ganzhi / _get_day_ganzhi 辅助函数测试
# --------------------------------------------------------------------------- #

class TestGanzhiHelpers:

    def test_year_ganzhi_2024(self):
        from server.llm import _get_year_ganzhi
        result = _get_year_ganzhi(2024)
        # 2024年 = 甲辰年
        assert result == "甲辰"

    def test_year_ganzhi_2025(self):
        from server.llm import _get_year_ganzhi
        result = _get_year_ganzhi(2025)
        assert result == "乙巳"

    def test_month_ganzhi_returns_string(self):
        from server.llm import _get_month_ganzhi
        result = _get_month_ganzhi(2024, 6)
        assert isinstance(result, str)
        assert len(result) == 2

    def test_day_ganzhi_with_date(self):
        from datetime import date

        from server.llm import _get_day_ganzhi
        result = _get_day_ganzhi(date(2024, 1, 1))
        assert isinstance(result, str)
        assert len(result) == 2
