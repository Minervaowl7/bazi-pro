#!/usr/bin/env python3
"""
bazi doctor — 环境诊断工具
检查 bazi-pro v4.2 运行环境，列出各组件状态
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path


def _check_python():
    v = sys.version_info
    ok = v >= (3, 10)
    return ok, f"{v.major}.{v.minor}.{v.micro}"


def _check_jieba():
    try:
        import jieba
        return True, "installed"
    except ImportError:
        return False, "missing (pip install jieba)"


def _check_corpus(corpus_path: str = None):
    if not corpus_path:
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "classical_corpus.md"),
            os.path.join(os.path.expanduser("~"), ".hermes", "skills", "bazi-pro", "references", "classical_corpus.md"),
        ]
        corpus_path = next((c for c in candidates if os.path.exists(c)), None)
    if not corpus_path or not os.path.exists(corpus_path):
        return False, "missing"
    with open(corpus_path) as f:
        count = sum(1 for l in f if l.strip() and not l.startswith("#"))
    return True, f"{count} entries"


def _check_bm25_cache(corpus_path: str = None):
    try:
        from bazi_pro.retrieve_classical import _cache_path, _resolve_corpus
        cp = corpus_path or _resolve_corpus()
        cf = _cache_path(cp)
        if os.path.exists(cf):
            size_kb = os.path.getsize(cf) / 1024
            return True, f"warm ({size_kb:.0f} KB)"
        return False, "cold (will build on first run)"
    except Exception:
        return False, "unknown"


def _check_dashboard():
    try:
        from bazi_pro.dashboard import generate_dashboard
        return True, "OK"
    except ImportError:
        return False, "missing"


def _check_markdown():
    try:
        import markdown
        return True, "installed"
    except ImportError:
        return True, "stdlib fallback"  # OK, we have fallback


def _check_weasyprint():
    try:
        import weasyprint
        return True, "installed"
    except ImportError:
        return False, "PDF disabled"


def _check_hybrid():
    try:
        import numpy, faiss
        from sentence_transformers import SentenceTransformer
        return True, "ready"
    except ImportError:
        return False, "downgraded to BM25-only"


def _check_examples():
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")
    if os.path.isdir(d):
        files = os.listdir(d)
        return True, f"{len(files)} files"
    return False, "missing"


def main():
    print("bazi-pro v4.2 — 环境诊断")
    print("=" * 40)

    checks = [
        ("Python", *_check_python()),
        ("jieba", *_check_jieba()),
        ("Corpus", *_check_corpus()),
        ("BM25 cache", *_check_bm25_cache()),
        ("Dashboard", *_check_dashboard()),
        ("Markdown", *_check_markdown()),
        ("PDF (weasyprint)", *_check_weasyprint()),
        ("Hybrid Search", *_check_hybrid()),
        ("Examples", *_check_examples()),
    ]

    for name, ok, detail in checks:
        icon = "✅" if ok else "⚠️ "
        print(f"  {icon} {name}: {detail}")

    print()
    all_ok = all(ok for _, ok, _ in checks)
    if all_ok:
        print("✅ 环境就绪")
    else:
        print("⚠️  部分组件缺失，详见上方标注")


if __name__ == "__main__":
    main()
