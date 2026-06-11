#!/usr/bin/env python3

import pytest

pytest.importorskip("aiosqlite")
pytest.importorskip("fastapi")

from server.analysis import _make_cache_key, _validate_input


class TestValidateInput:

    def test_valid_input(self):
        mcp = {"性别": "女", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"}
        result = _validate_input(mcp)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_missing_bazi(self):
        mcp = {"性别": "女", "日主": "丁"}
        result = _validate_input(mcp)
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_missing_day_master(self):
        mcp = {"性别": "女", "八字": "壬午 乙巳 丁亥 癸卯"}
        result = _validate_input(mcp)
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_missing_gender(self):
        mcp = {"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"}
        result = _validate_input(mcp)
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_invalid_bazi_format(self):
        mcp = {"性别": "女", "八字": "abc", "日主": "丁"}
        result = _validate_input(mcp)
        assert result["valid"] is False
        assert any("八字" in e for e in result["errors"])

    def test_invalid_day_master(self):
        mcp = {"性别": "女", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "X"}
        result = _validate_input(mcp)
        assert result["valid"] is False
        assert any("日主" in e for e in result["errors"])

    def test_invalid_gender(self):
        mcp = {"性别": "unknown", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"}
        result = _validate_input(mcp)
        assert result["valid"] is False
        assert any("性别" in e for e in result["errors"])

    def test_empty_bazi(self):
        mcp = {"性别": "女", "八字": "", "日主": "丁"}
        result = _validate_input(mcp)
        assert result["valid"] is False

    def test_empty_day_master(self):
        mcp = {"性别": "女", "八字": "壬午 乙巳 丁亥 癸卯", "日主": ""}
        result = _validate_input(mcp)
        assert result["valid"] is False

    def test_empty_gender(self):
        mcp = {"性别": "", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"}
        result = _validate_input(mcp)
        assert result["valid"] is False


class TestCacheKey:

    def test_same_input_same_key(self):
        mcp = {"性别": "女", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"}
        key1 = _make_cache_key(mcp, "standard")
        key2 = _make_cache_key(mcp, "standard")
        assert key1 == key2

    def test_different_gender_different_key(self):
        mcp1 = {"性别": "女", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"}
        mcp2 = {"性别": "男", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"}
        key1 = _make_cache_key(mcp1, "standard")
        key2 = _make_cache_key(mcp2, "standard")
        assert key1 != key2

    def test_different_dayun_different_key(self):
        mcp1 = {"性别": "女", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "大运": []}
        mcp2 = {"性别": "女", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "大运": [{"gan": "甲", "zhi": "寅"}]}
        key1 = _make_cache_key(mcp1, "standard")
        key2 = _make_cache_key(mcp2, "standard")
        assert key1 != key2

    def test_field_order_independent(self):
        mcp1 = {"性别": "女", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"}
        mcp2 = {"日主": "丁", "八字": "壬午 乙巳 丁亥 癸卯", "性别": "女"}
        key1 = _make_cache_key(mcp1, "standard")
        key2 = _make_cache_key(mcp2, "standard")
        assert key1 == key2

    def test_key_format_bazi_v5_prefix(self):
        mcp = {"性别": "女", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"}
        key = _make_cache_key(mcp, "standard")
        assert key.startswith("bazi:v5:")
        hash_part = key[len("bazi:v5:"):]
        assert len(hash_part) == 24

    def test_different_detail_level_different_key(self):
        mcp = {"性别": "女", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"}
        key1 = _make_cache_key(mcp, "standard")
        key2 = _make_cache_key(mcp, "detailed")
        assert key1 != key2

    def test_different_yangli_different_key(self):
        mcp1 = {"性别": "女", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "阳历": "2002-05-19"}
        mcp2 = {"性别": "女", "八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "阳历": "2003-06-20"}
        key1 = _make_cache_key(mcp1, "standard")
        key2 = _make_cache_key(mcp2, "standard")
        assert key1 != key2
