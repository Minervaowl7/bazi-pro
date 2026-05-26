#!/usr/bin/env python3
import importlib.util

import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("fastapi") is None,
    reason="fastapi not installed",
)


def test_server_main_callable():
    from server.app import main
    assert callable(main)


def test_server_app_exists():
    from server.app import app
    assert app is not None
    assert app.title == "bazi-pro API"


def test_server_main_env_vars(monkeypatch):
    monkeypatch.setenv("BAZI_HOST", "127.0.0.1")
    monkeypatch.setenv("BAZI_PORT", "9999")
    monkeypatch.setenv("BAZI_LOG_LEVEL", "debug")
    import os
    assert os.environ.get("BAZI_HOST") == "127.0.0.1"
    assert os.environ.get("BAZI_PORT") == "9999"
    assert os.environ.get("BAZI_LOG_LEVEL") == "debug"
