"""Smoke tests for bazi-pro v5.0 — 核心命令可用性验证"""

import json
import os
import subprocess
from pathlib import Path

try:
    import pytest
except ImportError:
    import sys
    print("pytest not installed. Skipping tests.", file=sys.stderr)
    sys.exit(0)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30)


def test_retrieve_basic():
    """检索基本功能"""
    r = run(["python3", str(SCRIPTS / "retrieve_classical.py"), "食神 制杀 身弱", "-k", "3", "--json"])
    assert r.returncode == 0, f"exit={r.returncode} stderr={r.stderr}"
    data = json.loads(r.stdout)
    assert "queries" in data or "results" in data
    assert data.get("corpus_size", 0) > 0


def test_retrieve_batch():
    """批量检索"""
    r = run(["python3", str(SCRIPTS / "retrieve_classical.py"), "--batch", "食神", "七杀", "调候", "-k", "2", "--json"])
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert len(data.get("queries", [])) == 3


def test_retrieve_stats():
    """语料库统计"""
    r = run(["python3", str(SCRIPTS / "retrieve_classical.py"), "--stats"])
    assert r.returncode == 0
    assert "总条数" in r.stdout


def test_retrieve_cache_info():
    """缓存信息"""
    r = run(["python3", str(SCRIPTS / "retrieve_classical.py"), "--cache-info"])
    assert r.returncode == 0


def test_doctor():
    """环境诊断"""
    r = run(["python3", str(SCRIPTS / "doctor.py")])
    assert r.returncode == 0
    assert "Python" in r.stdout
    assert "jieba" in r.stdout


def test_evidence():
    """证据对象"""
    r = run(["python3", str(SCRIPTS / "evidence.py")])
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert "evidence_chain" in data
    assert len(data["evidence_chain"]) >= 3


def test_hybrid_status():
    """Hybrid Search 状态"""
    r = run(["python3", str(SCRIPTS / "hybrid_search.py")])
    assert r.returncode == 0
    assert "Hybrid Search 可用" in r.stdout


def test_report_markdown():
    """Markdown 报告生成"""
    sample = REPO_ROOT / "examples" / "sample_analysis.md"
    if not sample.exists():
        return  # skip
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        tmp = f.name
    try:
        r = run(["python3", str(SCRIPTS / "generate_report.py"), "--input", str(sample), "--output", tmp])
        assert r.returncode == 0
        assert os.path.getsize(tmp) > 100
    finally:
        os.unlink(tmp)


def test_report_dashboard():
    """仪表盘生成"""
    sample = REPO_ROOT / "examples" / "sample_analysis.md"
    if not sample.exists():
        return
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        tmp = f.name
    try:
        r = run(["python3", str(SCRIPTS / "generate_report.py"), "--input", str(sample),
                 "--theme", "dashboard", "--format", "html", "--output", tmp])
        assert r.returncode == 0
        actual_path = tmp.replace(".html", "_dashboard.html") if not tmp.endswith("_dashboard.html") else tmp
        if not Path(actual_path).exists():
            actual_path = tmp
        content = Path(actual_path).read_text()
        assert "ev-card" in content or "evidence-card" in content
        assert "reasoning-graph" in content or "relation-graph" in content
    finally:
        for p in [tmp, tmp.replace(".html", "_dashboard.html")]:
            if Path(p).exists():
                os.unlink(p)


def test_version_consistency():
    r = run(["python3", str(SCRIPTS / "check_version_consistency.py")])
    assert r.returncode == 0, f"Version check failed: {r.stdout}\n{r.stderr}"


def test_retrieve_single_json_schema():
    r = run(["python3", str(SCRIPTS / "retrieve_classical.py"), "食神", "-k", "2", "--json"])
    assert r.returncode == 0, f"exit={r.returncode} stderr={r.stderr}"
    data = json.loads(r.stdout)
    assert "queries" in data, f"Single query output missing 'queries' key: {list(data.keys())}"
    assert len(data["queries"]) == 1
    q = data["queries"][0]
    assert "query" in q
    assert "results" in q
    assert "counter_evidence" in q, "Single query output missing counter_evidence"
    assert isinstance(q["counter_evidence"], list)
    assert data.get("corpus_size", 0) > 0


def test_retrieve_batch_json_schema():
    r = run(["python3", str(SCRIPTS / "retrieve_classical.py"), "--batch", "食神", "七杀", "-k", "2", "--json"])
    assert r.returncode == 0, f"exit={r.returncode} stderr={r.stderr}"
    data = json.loads(r.stdout)
    assert "queries" in data, f"Batch output missing 'queries' key: {list(data.keys())}"
    assert len(data["queries"]) == 2
    for q in data["queries"]:
        assert "query" in q
        assert "results" in q
        assert "counter_evidence" in q, "Batch query item missing counter_evidence"
        assert isinstance(q["counter_evidence"], list)


if __name__ == "__main__":
    try:
    import pytest
except ImportError:
    import sys
    print("pytest not installed. Skipping tests.", file=sys.stderr)
    sys.exit(0)
    pytest.main([__file__, "-v"])
