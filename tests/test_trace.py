"""Trace format smoke tests for v4.3"""

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_demo_trace():
    """demo_trace() 生成合法 trace"""
    from bazi_pro.trace import demo_trace, validate_trace
    trace = demo_trace()
    assert trace["schema_version"] == "trace.v1"
    assert len(trace["stages"]) >= 5
    assert len(trace["evidence"]) >= 2
    # Write + validate round-trip
    tmp = REPO / "examples" / "sample_trace.json"
    # Already written by trace.py demo, just validate
    ok, errors = validate_trace(str(tmp))
    assert ok, f"Validation failed: {errors}"


def test_trace_builder():
    """TraceBuilder 构建合法 trace"""
    from bazi_pro.trace import TraceBuilder
    tb = TraceBuilder("test")
    tb.set_input(day_master="丙", pillars=["癸卯", "壬戌", "丙午", "壬辰"])
    tb.add_stage("s1", title="Test", summary="...")
    tb.add_stage("s2", title="Test2", summary="...")
    tb.add_stage("s3", title="Test3", summary="...")
    tb.add_evidence("ev1", claim="test", basis_mcp=["a"], basis_rules=["b"])
    trace = tb.build()
    assert len(trace["stages"]) == 3
    assert trace["engine"]["version"] == "4.3.0"


def test_validate_invalid():
    """validate_trace 拒绝非法 trace"""
    from bazi_pro.trace import validate_trace
    import tempfile, json as _json
    bad = {"schema_version": "wrong"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        _json.dump(bad, f)
        tmp = f.name
    try:
        ok, errors = validate_trace(tmp)
        assert not ok
        assert any("schema_version" in e for e in errors)
    finally:
        Path(tmp).unlink()


def test_evidence_trace_out():
    """bazi-evidence --trace-out 生成合法trace"""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp = f.name
    try:
        r = subprocess.run(
            ["python3", "-m", "bazi_pro.evidence", "--trace-out", tmp],
            capture_output=True, text=True, timeout=10,
            cwd=str(REPO)
        )
        assert r.returncode == 0, r.stderr
        trace = json.loads(Path(tmp).read_text())
        assert trace["schema_version"] == "trace.v1"
        assert len(trace["stages"]) >= 5
    finally:
        Path(tmp).unlink(missing_ok=True)


def test_evidence_validate():
    """bazi-evidence --validate 校验正常"""
    r = subprocess.run(
        ["python3", "-m", "bazi_pro.evidence", "--validate", str(REPO / "examples" / "sample_trace.json")],
        capture_output=True, text=True, timeout=10,
        cwd=str(REPO)
    )
    assert r.returncode == 0, r.stderr
    assert "✅ Trace valid" in r.stdout


def test_replay_viewer_exists():
    """dist/index.html 包含 Replay Viewer 文案"""
    viewer = REPO / "dist" / "index.html"
    assert viewer.exists(), f"{viewer} not found"
    content = viewer.read_text()
    assert "Replay" in content or "回放" in content or "trace" in content.lower(), \
        "dist/index.html should mention Replay/Trace"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
