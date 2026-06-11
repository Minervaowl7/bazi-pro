"""LLM retry logic tests for _post_with_retry() in server/llm_client.py.

Covers:
- 429 rate limit → retry with backoff, eventual success
- 5xx server error → retry, eventual success
- 401/403 auth failure → no retry, raise immediately
- 4xx client error (non-auth) → no retry, raise_for_status
- All retries exhausted → raise RuntimeError
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from server.llm_client import _post_with_retry


def _make_response(status_code: int, json_data: dict | None = None) -> MagicMock:
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
    return resp


def _make_mock_client():
    """Create a mock httpx.AsyncClient that supports async context manager."""
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


class TestRetryOn429:
    """429 rate limit should trigger retry with backoff."""

    def test_429_then_success(self):
        """First call returns 429, second returns 200."""
        asyncio.run(self._async_test_429_then_success())

    async def _async_test_429_then_success(self):
        mock_client = _make_mock_client()
        success_resp = _make_response(200, {"choices": [{"message": {"content": "ok"}}]})
        rate_limit_resp = _make_response(429)
        mock_client.post = AsyncMock(side_effect=[rate_limit_resp, success_resp])

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client), \
             patch("server.llm_client.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await _post_with_retry("http://test.com/api", {}, {})

        assert result == {"choices": [{"message": {"content": "ok"}}]}
        mock_sleep.assert_called_once()

    def test_429_multiple_retries_then_success(self):
        """Two 429s then success."""
        asyncio.run(self._async_test_429_multiple_retries_then_success())

    async def _async_test_429_multiple_retries_then_success(self):
        mock_client = _make_mock_client()
        success_resp = _make_response(200, {"ok": True})
        rate_limit_resp = _make_response(429)
        mock_client.post = AsyncMock(side_effect=[rate_limit_resp, rate_limit_resp, success_resp])

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client), \
             patch("server.llm_client.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await _post_with_retry("http://test.com/api", {}, {})

        assert result == {"ok": True}
        assert mock_sleep.call_count == 2

    def test_429_exhausted_retries(self):
        """All retries on 429 → RuntimeError."""
        asyncio.run(self._async_test_429_exhausted_retries())

    async def _async_test_429_exhausted_retries(self):
        mock_client = _make_mock_client()
        resp_429 = _make_response(429)
        mock_client.post = AsyncMock(return_value=resp_429)

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client), \
             patch("server.llm_client.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError, match="已重试"):
                await _post_with_retry("http://test.com/api", {}, {}, max_retries=2)


class TestRetryOn5xx:
    """5xx server error should trigger retry."""

    def test_500_then_success(self):
        asyncio.run(self._async_test_500_then_success())

    async def _async_test_500_then_success(self):
        mock_client = _make_mock_client()
        success_resp = _make_response(200, {"ok": True})
        error_resp = _make_response(500)
        mock_client.post = AsyncMock(side_effect=[error_resp, success_resp])

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client), \
             patch("server.llm_client.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await _post_with_retry("http://test.com/api", {}, {})

        assert result == {"ok": True}
        mock_sleep.assert_called_once()

    def test_502_then_success(self):
        asyncio.run(self._async_test_502_then_success())

    async def _async_test_502_then_success(self):
        mock_client = _make_mock_client()
        error_resp = _make_response(502)
        success_resp = _make_response(200, {"ok": True})
        mock_client.post = AsyncMock(side_effect=[error_resp, success_resp])

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client), \
             patch("server.llm_client.asyncio.sleep", new_callable=AsyncMock):
            result = await _post_with_retry("http://test.com/api", {}, {})

        assert result == {"ok": True}

    def test_503_then_success(self):
        asyncio.run(self._async_test_503_then_success())

    async def _async_test_503_then_success(self):
        mock_client = _make_mock_client()
        error_resp = _make_response(503)
        success_resp = _make_response(200, {"ok": True})
        mock_client.post = AsyncMock(side_effect=[error_resp, success_resp])

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client), \
             patch("server.llm_client.asyncio.sleep", new_callable=AsyncMock):
            result = await _post_with_retry("http://test.com/api", {}, {})

        assert result == {"ok": True}

    def test_5xx_exhausted_retries(self):
        asyncio.run(self._async_test_5xx_exhausted_retries())

    async def _async_test_5xx_exhausted_retries(self):
        mock_client = _make_mock_client()
        error_resp = _make_response(500)
        mock_client.post = AsyncMock(return_value=error_resp)

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client), \
             patch("server.llm_client.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(httpx.HTTPStatusError):
                await _post_with_retry("http://test.com/api", {}, {}, max_retries=2)


class TestNoRetryOnAuth:
    """401/403 should not retry."""

    def test_401_no_retry(self):
        asyncio.run(self._async_test_401_no_retry())

    async def _async_test_401_no_retry(self):
        mock_client = _make_mock_client()
        auth_resp = _make_response(401)
        mock_client.post = AsyncMock(return_value=auth_resp)

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="认证失败"):
                await _post_with_retry("http://test.com/api", {}, {})

    def test_403_no_retry(self):
        asyncio.run(self._async_test_403_no_retry())

    async def _async_test_403_no_retry(self):
        mock_client = _make_mock_client()
        auth_resp = _make_response(403)
        mock_client.post = AsyncMock(return_value=auth_resp)

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="认证失败"):
                await _post_with_retry("http://test.com/api", {}, {})

    def test_401_only_called_once(self):
        asyncio.run(self._async_test_401_only_called_once())

    async def _async_test_401_only_called_once(self):
        mock_client = _make_mock_client()
        auth_resp = _make_response(401)
        mock_client.post = AsyncMock(return_value=auth_resp)

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(RuntimeError):
                await _post_with_retry("http://test.com/api", {}, {}, max_retries=3)

        assert mock_client.post.call_count == 1


class TestNoRetryOnOther4xx:
    """4xx (non-auth) should not retry."""

    def test_400_no_retry(self):
        asyncio.run(self._async_test_400_no_retry())

    async def _async_test_400_no_retry(self):
        mock_client = _make_mock_client()
        error_resp = _make_response(400)
        mock_client.post = AsyncMock(return_value=error_resp)

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(httpx.HTTPStatusError):
                await _post_with_retry("http://test.com/api", {}, {})

    def test_404_no_retry(self):
        asyncio.run(self._async_test_404_no_retry())

    async def _async_test_404_no_retry(self):
        mock_client = _make_mock_client()
        error_resp = _make_response(404)
        mock_client.post = AsyncMock(return_value=error_resp)

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(httpx.HTTPStatusError):
                await _post_with_retry("http://test.com/api", {}, {})


class TestSuccessfulCall:
    """200 should return immediately."""

    def test_200_immediate_success(self):
        asyncio.run(self._async_test_200_immediate_success())

    async def _async_test_200_immediate_success(self):
        mock_client = _make_mock_client()
        success_resp = _make_response(200, {"choices": [{"message": {"content": "hello"}}]})
        mock_client.post = AsyncMock(return_value=success_resp)

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client):
            result = await _post_with_retry("http://test.com/api", {}, {})

        assert result == {"choices": [{"message": {"content": "hello"}}]}
        assert mock_client.post.call_count == 1


class TestCustomMaxRetries:
    """max_retries parameter should be respected."""

    def test_max_retries_1(self):
        asyncio.run(self._async_test_max_retries_1())

    async def _async_test_max_retries_1(self):
        mock_client = _make_mock_client()
        error_resp = _make_response(500)
        success_resp = _make_response(200, {"ok": True})
        mock_client.post = AsyncMock(side_effect=[error_resp, success_resp])

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client), \
             patch("server.llm_client.asyncio.sleep", new_callable=AsyncMock):
            result = await _post_with_retry("http://test.com/api", {}, {}, max_retries=1)

        assert result == {"ok": True}

    def test_max_retries_0_no_retry(self):
        asyncio.run(self._async_test_max_retries_0_no_retry())

    async def _async_test_max_retries_0_no_retry(self):
        mock_client = _make_mock_client()
        error_resp = _make_response(500)
        mock_client.post = AsyncMock(return_value=error_resp)

        with patch("server.llm_client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(httpx.HTTPStatusError):
                await _post_with_retry("http://test.com/api", {}, {}, max_retries=0)
