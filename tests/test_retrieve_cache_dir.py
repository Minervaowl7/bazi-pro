#!/usr/bin/env python3
import os

try:
    import pytest
except ImportError:
    import sys
    print("pytest not installed. Skipping tests.", file=sys.stderr)
    sys.exit(0)

from bazi_pro.retrieve_classical import _cache_dir, _cache_path, get_bm25, load_corpus


class TestCacheDir:

    def test_default_cache_dir(self, monkeypatch, tmp_path):
        monkeypatch.delenv("BAZI_CACHE_DIR", raising=False)
        monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
        d = _cache_dir()
        assert "bazi-pro" in d

    def test_custom_cache_dir(self, monkeypatch, tmp_path):
        custom = str(tmp_path / "my-cache")
        monkeypatch.setenv("BAZI_CACHE_DIR", custom)
        d = _cache_dir()
        assert d == custom
        assert os.path.isdir(d)

    def test_readonly_fallback(self, monkeypatch, tmp_path):
        monkeypatch.setenv("BAZI_CACHE_DIR", "/proc/nonexistent/path")
        d = _cache_dir()
        assert os.path.isdir(d)

    def test_cache_hit_on_second_call(self, monkeypatch, tmp_path):
        monkeypatch.setenv("BAZI_CACHE_DIR", str(tmp_path))
        from bazi_pro.retrieve_classical import _resolve_corpus
        corpus_path = _resolve_corpus()
        if not os.path.exists(corpus_path):
            pytest.skip("corpus not available")
        entries = load_corpus(corpus_path)
        bm25_1, hit_1 = get_bm25(corpus_path, entries, force_rebuild=True)
        assert hit_1 is False
        bm25_2, hit_2 = get_bm25(corpus_path, entries, force_rebuild=False)
        assert hit_2 is True

    def test_cache_path_uses_sha256(self, monkeypatch, tmp_path):
        monkeypatch.setenv("BAZI_CACHE_DIR", str(tmp_path))
        from bazi_pro.retrieve_classical import _resolve_corpus
        corpus_path = _resolve_corpus()
        if not os.path.exists(corpus_path):
            pytest.skip("corpus not available")
        path = _cache_path(corpus_path)
        basename = os.path.basename(path)
        hash_part = basename.replace("bm25_", "").replace(".pkl", "")
        assert len(hash_part) >= 16
