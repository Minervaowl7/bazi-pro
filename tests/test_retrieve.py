"""Smoke tests for bazi-pro v5.0 — 核心命令可用性验证"""

import json
import os
import subprocess
import sys
from pathlib import Path

try:
    import pytest
except ImportError:
    print("pytest not installed. Skipping tests.", file=sys.stderr)
    sys.exit(0)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
PYTHON = sys.executable


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8",
        cwd=str(REPO_ROOT), timeout=30, env=env,
    )


def test_retrieve_basic():
    """检索基本功能"""
    r = run([PYTHON, str(SCRIPTS / "retrieve_classical.py"), "食神 制杀 身弱", "-k", "3", "--json"])
    assert r.returncode == 0, f"exit={r.returncode} stderr={r.stderr}"
    data = json.loads(r.stdout)
    assert "queries" in data or "results" in data
    assert data.get("corpus_size", 0) > 0


def test_retrieve_batch():
    """批量检索"""
    r = run([PYTHON, str(SCRIPTS / "retrieve_classical.py"), "--batch", "食神", "七杀", "调候", "-k", "2", "--json"])
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert len(data.get("queries", [])) == 3


def test_retrieve_stats():
    """语料库统计"""
    r = run([PYTHON, str(SCRIPTS / "retrieve_classical.py"), "--stats"])
    assert r.returncode == 0
    assert "总条数" in r.stdout


def test_retrieve_cache_info():
    """缓存信息"""
    r = run([PYTHON, str(SCRIPTS / "retrieve_classical.py"), "--cache-info"])
    assert r.returncode == 0


def test_doctor():
    """环境诊断"""
    r = run([PYTHON, str(SCRIPTS / "doctor.py")])
    assert r.returncode == 0
    assert "Python" in r.stdout
    assert "jieba" in r.stdout


def test_evidence():
    """证据对象"""
    r = run([PYTHON, str(SCRIPTS / "evidence.py")])
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert "evidence_chain" in data
    assert len(data["evidence_chain"]) >= 3


def test_hybrid_status():
    """Hybrid Search 状态"""
    r = run([PYTHON, str(SCRIPTS / "hybrid_search.py")])
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
        r = run([PYTHON, str(SCRIPTS / "generate_report.py"), "--input", str(sample), "--output", tmp])
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
        r = run([PYTHON, str(SCRIPTS / "generate_report.py"), "--input", str(sample),
                 "--theme", "dashboard", "--format", "html", "--output", tmp])
        assert r.returncode == 0
        actual_path = tmp.replace(".html", "_dashboard.html") if not tmp.endswith("_dashboard.html") else tmp
        if not Path(actual_path).exists():
            actual_path = tmp
        content = Path(actual_path).read_text(encoding="utf-8")
        assert "ev-card" in content or "evidence-card" in content
        assert "reasoning-graph" in content or "relation-graph" in content
    finally:
        for p in [tmp, tmp.replace(".html", "_dashboard.html")]:
            if Path(p).exists():
                os.unlink(p)


def test_version_consistency():
    r = run([PYTHON, str(SCRIPTS / "check_version_consistency.py")])
    assert r.returncode == 0, f"Version check failed: {r.stdout}\n{r.stderr}"


def test_retrieve_single_json_schema():
    r = run([PYTHON, str(SCRIPTS / "retrieve_classical.py"), "食神", "-k", "2", "--json"])
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
    r = run([PYTHON, str(SCRIPTS / "retrieve_classical.py"), "--batch", "食神", "七杀", "-k", "2", "--json"])
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


# ---------------------------------------------------------------------------
# RAG Engine 兼容性测试
# ---------------------------------------------------------------------------


def test_retrieve_for_chat_backward_compat():
    """retrieve_for_chat 签名向后兼容：旧调用方不传新参数仍正常工作"""
    from server.rag_engine import retrieve_for_chat

    context = {"day_master": "甲", "pattern": {"pattern": "正官格"}, "strength": {"verdict": "身旺"}}
    # 旧调用方式：只传 question + analysis_context + k
    result = retrieve_for_chat("食神制杀是什么意思", context, k=3)
    assert isinstance(result, dict)
    assert "results" in result
    assert "category" in result
    assert "query" in result


def test_retrieve_for_chat_new_params():
    """retrieve_for_chat 新参数 retrieval_mode 正常工作"""
    from server.rag_engine import retrieve_for_chat

    context = {"day_master": "甲", "pattern": {"pattern": "正官格"}, "strength": {"verdict": "身旺"}}
    result = retrieve_for_chat("食神制杀", context, k=3, retrieval_mode="bm25")
    assert isinstance(result, dict)
    assert result.get("retrieval_mode") == "bm25"
