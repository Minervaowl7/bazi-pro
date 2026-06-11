"""API authentication coverage tests for verify_api_key() in server/deps.py.

Covers:
- No API key configured → returns True (non-production)
- No API key configured in production → raises APIKeyError
- Valid API key via X-API-Key header → returns True
- Invalid API key via header → raises APIKeyError
- Missing API key header → raises APIKeyError
- Valid API key via query param token → returns True
- Invalid API key via query param → raises APIKeyError
- Empty API key header treated as missing
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("fastapi")

from server.deps import APIKeyError, verify_api_key


def _make_request(query_params: dict | None = None) -> MagicMock:
    """Create a mock FastAPI Request with query_params."""
    request = MagicMock()
    request.query_params = query_params or {}
    return request


class TestNoAPIKeyConfigured:
    """When BAZI_API_KEY is not set."""

    @pytest.mark.asyncio
    async def test_no_key_returns_true_non_production(self):
        """No API key configured in non-prod → allow all requests."""
        request = _make_request()
        with patch.dict(os.environ, {"BAZI_API_KEY": "", "ENV": "development"}, clear=False):
            with patch("server.deps.API_KEY", ""):
                result = await verify_api_key(request, api_key=None)
        assert result is True

    @pytest.mark.asyncio
    async def test_no_key_raises_in_production(self):
        """No API key configured in production → raise APIKeyError."""
        request = _make_request()
        with patch.dict(os.environ, {"BAZI_API_KEY": "", "ENV": "production"}, clear=False):
            with patch("server.deps.API_KEY", ""):
                with pytest.raises(APIKeyError):
                    await verify_api_key(request, api_key=None)

    @pytest.mark.asyncio
    async def test_no_key_raises_in_prod_uppercase(self):
        """ENV=PRODUCTION should also trigger the production check."""
        request = _make_request()
        with patch.dict(os.environ, {"BAZI_API_KEY": "", "ENV": "PRODUCTION"}, clear=False):
            with patch("server.deps.API_KEY", ""):
                with pytest.raises(APIKeyError):
                    await verify_api_key(request, api_key=None)


class TestAPIKeyViaHeader:
    """Authentication via X-API-Key header."""

    @pytest.mark.asyncio
    async def test_valid_key_returns_true(self):
        """Correct API key in header → allow."""
        request = _make_request()
        with patch("server.deps.API_KEY", "test-secret-key"):
            result = await verify_api_key(request, api_key="test-secret-key")
        assert result is True

    @pytest.mark.asyncio
    async def test_wrong_key_raises(self):
        """Wrong API key in header → raise APIKeyError."""
        request = _make_request()
        with patch("server.deps.API_KEY", "correct-key"):
            with pytest.raises(APIKeyError):
                await verify_api_key(request, api_key="wrong-key")

    @pytest.mark.asyncio
    async def test_empty_key_raises_when_key_required(self):
        """Empty string API key treated as missing → raise APIKeyError."""
        request = _make_request()
        with patch("server.deps.API_KEY", "required-key"):
            with pytest.raises(APIKeyError):
                await verify_api_key(request, api_key="")

    @pytest.mark.asyncio
    async def test_none_key_raises_when_key_required(self):
        """None API key (header missing) → raise APIKeyError."""
        request = _make_request()
        with patch("server.deps.API_KEY", "required-key"):
            with pytest.raises(APIKeyError):
                await verify_api_key(request, api_key=None)


class TestAPIKeyViaQueryParam:
    """Authentication via ?token= query parameter."""

    @pytest.mark.asyncio
    async def test_valid_token_in_query(self):
        """Correct token in query params → allow."""
        request = _make_request({"token": "query-secret"})
        with patch("server.deps.API_KEY", "query-secret"):
            result = await verify_api_key(request, api_key=None)
        assert result is True

    @pytest.mark.asyncio
    async def test_invalid_token_in_query(self):
        """Wrong token in query params → raise APIKeyError."""
        request = _make_request({"token": "wrong-token"})
        with patch("server.deps.API_KEY", "correct-token"):
            with pytest.raises(APIKeyError):
                await verify_api_key(request, api_key=None)

    @pytest.mark.asyncio
    async def test_empty_token_in_query_falls_through(self):
        """Empty token in query params → falls through to raise APIKeyError."""
        request = _make_request({"token": ""})
        with patch("server.deps.API_KEY", "required-key"):
            with pytest.raises(APIKeyError):
                await verify_api_key(request, api_key=None)

    @pytest.mark.asyncio
    async def test_no_token_no_header_raises(self):
        """No token in query, no header → raise APIKeyError."""
        request = _make_request({})
        with patch("server.deps.API_KEY", "required-key"):
            with pytest.raises(APIKeyError):
                await verify_api_key(request, api_key=None)


class TestHeaderPriorityOverQuery:
    """Header should be checked before query param."""

    @pytest.mark.asyncio
    async def test_valid_header_ignores_query(self):
        """Valid header → allow, even if query has wrong token."""
        request = _make_request({"token": "wrong"})
        with patch("server.deps.API_KEY", "correct-key"):
            result = await verify_api_key(request, api_key="correct-key")
        assert result is True

    @pytest.mark.asyncio
    async def test_invalid_header_falls_to_query(self):
        """Invalid header → falls through to query param → allow if valid."""
        request = _make_request({"token": "fallback-key"})
        with patch("server.deps.API_KEY", "fallback-key"):
            # Wrong header → hmac.compare_digest returns False → falls to query
            # Query has correct token → returns True
            result = await verify_api_key(request, api_key="wrong-header")
        assert result is True


class TestTimingSafeComparison:
    """Verify hmac.compare_digest is used (timing-safe)."""

    @pytest.mark.asyncio
    async def test_uses_hmac_compare_digest(self):
        """Verify that hmac.compare_digest is used for comparison."""
        request = _make_request()
        with patch("server.deps.API_KEY", "test-key"):
            with patch("server.deps.hmac.compare_digest", return_value=True) as mock_compare:
                await verify_api_key(request, api_key="test-key")
        mock_compare.assert_called()


class TestAPIKeyErrorType:
    """APIKeyError is a proper exception class."""

    def test_api_key_error_is_exception(self):
        assert issubclass(APIKeyError, Exception)

    def test_api_key_error_can_be_raised(self):
        with pytest.raises(APIKeyError):
            raise APIKeyError()
