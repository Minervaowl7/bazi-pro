#!/usr/bin/env python3
import importlib
import subprocess
import sys

try:
    import pytest
except ImportError:
    print("pytest not installed. Skipping tests.", file=sys.stderr)
    sys.exit(0)

_HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None

_CONSOLE_SCRIPTS = [
    ("bazi-retrieve", "bazi_pro.retrieve_classical", "main"),
    ("bazi-report", "bazi_pro.generate_report", "main"),
    ("bazi-doctor", "bazi_pro.doctor", "main"),
    ("bazi-evidence", "bazi_pro.evidence", "main"),
    ("bazi-trace", "bazi_pro.trace", "main"),
    pytest.param("bazi-server", "server.app", "main", marks=pytest.mark.skipif(
        not _HAS_FASTAPI, reason="fastapi not installed")),
]


class TestConsoleScriptsImportable:

    @pytest.mark.parametrize("cli_name,module,func", _CONSOLE_SCRIPTS)
    def test_entry_point_callable(self, cli_name, module, func):
        mod = importlib.import_module(module)
        entry = getattr(mod, func, None)
        assert entry is not None, f"{module}:{func} not found"
        assert callable(entry), f"{module}:{func} is not callable"

    @pytest.mark.parametrize("cli_name,module,func", _CONSOLE_SCRIPTS)
    def test_cli_help_no_import_error(self, cli_name, module, func):
        result = subprocess.run(
            [sys.executable, "-c", f"from {module} import {func}; assert callable({func})"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, f"Import {module}:{func} failed: {result.stderr}"


@pytest.mark.skipif(not _HAS_FASTAPI, reason="fastapi/pydantic not installed")
class TestServerEntrypointSmoke:

    def test_server_import_no_error(self):
        result = subprocess.run(
            [sys.executable, "-c", "from server.app import main, app; assert callable(main)"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, f"server.app import failed: {result.stderr}"

    def test_server_schema_import_no_error(self):
        result = subprocess.run(
            [sys.executable, "-c", "from server.schemas import BaziAnalysisRequest"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, f"server.schemas import failed: {result.stderr}"

    def test_server_analysis_import_no_error(self):
        result = subprocess.run(
            [sys.executable, "-c", "from server.analysis import run_analysis, _validate_input, _make_cache_key"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, f"server.analysis import failed: {result.stderr}"

    def test_server_taskstore_import_no_error(self):
        result = subprocess.run(
            [sys.executable, "-c", "from server.taskstore import TaskStore, MemoryTaskStore, RedisTaskStore, create_task_store"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, f"server.taskstore import failed: {result.stderr}"

    def test_server_ratelimiter_import_no_error(self):
        result = subprocess.run(
            [sys.executable, "-c", "from server.ratelimiter import RateLimiter, MemoryRateLimiter, RedisRateLimiter, create_rate_limiter"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, f"server.ratelimiter import failed: {result.stderr}"
