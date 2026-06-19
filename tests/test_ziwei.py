import os; os.environ["BAZI_ALLOW_UNAUTHED"] = "1"
"""
紫微斗数模块测试
"""

import pytest

from bazi_pro.core.ziwei.constants import SI_HUA_TABLE, STAR_NATURE
from bazi_pro.core.ziwei.narrator import narrate_ziwei
from bazi_pro.core.ziwei.patterns import detect_patterns, detect_zi_fu
from bazi_pro.core.ziwei.sihua import analyze_sihua, get_sihua_by_stem, get_year_branch, get_year_stem
from bazi_pro.core.ziwei.stars import analyze_ming_palace, analyze_star_in_palace
from bazi_pro.core.ziwei.utils import (
    get_ming_branch,
    get_palace_by_branch,
    get_palace_by_name,
    get_palace_major_stars,
    get_palace_minor_stars,
    get_star_brightness,
    has_star,
    is_bright,
    is_dim,
)


class TestConstants:
    """常量测试"""

    def test_sihua_table(self):
        """测试四化表完整性"""
        assert len(SI_HUA_TABLE) == 10
        for stem, sihua in SI_HUA_TABLE.items():
            assert "化禄" in sihua
            assert "化权" in sihua
            assert "化科" in sihua
            assert "化忌" in sihua

    def test_star_nature(self):
        """测试星曜性质完整性"""
        assert len(STAR_NATURE) == 14
        for star_name, nature in STAR_NATURE.items():
            assert nature.name == star_name
            assert nature.wuxing in ["木", "火", "土", "金", "水"]
            assert nature.jixiong in ["吉", "凶", "中"]
            assert len(nature.palace_effects) == 12


class TestUtils:
    """工具函数测试"""

    def test_get_palace_by_name(self):
        """测试根据宫位名称获取宫位"""
        chart = {
            "palaces": [
                {"name": "命宫", "earthlyBranch": "寅"},
                {"name": "财帛宫", "earthlyBranch": "午"},
            ]
        }
        palace = get_palace_by_name(chart, "命宫")
        assert palace is not None
        assert palace["name"] == "命宫"

    def test_get_palace_by_name_not_found(self):
        """测试宫位不存在"""
        chart = {"palaces": [{"name": "命宫", "earthlyBranch": "寅"}]}
        palace = get_palace_by_name(chart, "不存在的宫位")
        assert palace is None

    def test_get_palace_by_branch(self):
        """测试根据地支获取宫位"""
        chart = {
            "palaces": [
                {"name": "命宫", "earthlyBranch": "寅"},
                {"name": "财帛宫", "earthlyBranch": "午"},
            ]
        }
        palace = get_palace_by_branch(chart, "寅")
        assert palace is not None
        assert palace["earthlyBranch"] == "寅"

    def test_get_ming_branch(self):
        """测试获取命宫地支"""
        chart = {
            "palaces": [
                {"name": "命宫", "earthlyBranch": "寅"},
            ]
        }
        branch = get_ming_branch(chart)
        assert branch == "寅"

    def test_get_palace_major_stars(self):
        """测试获取宫位主星"""
        palace = {
            "majorStars": [
                {"name": "紫微", "brightness": "bright"},
                {"name": "天府", "brightness": "normal"},
            ]
        }
        stars = get_palace_major_stars(palace)
        assert stars == ["紫微", "天府"]

    def test_get_palace_minor_stars(self):
        """测试获取宫位辅星"""
        palace = {
            "minorStars": [
                {"name": "左辅", "brightness": "bright"},
                {"name": "右弼", "brightness": "normal"},
            ]
        }
        stars = get_palace_minor_stars(palace)
        assert stars == ["左辅", "右弼"]

    def test_has_star(self):
        """测试判断宫位是否有某星曜"""
        palace = {
            "majorStars": [{"name": "紫微", "brightness": "bright"}],
            "minorStars": [{"name": "左辅", "brightness": "normal"}],
        }
        assert has_star(palace, "紫微") is True
        assert has_star(palace, "左辅") is True
        assert has_star(palace, "天机") is False

    def test_is_bright(self):
        """测试判断星曜是否庙旺"""
        palace = {
            "majorStars": [{"name": "紫微", "brightness": "bright"}],
            "minorStars": [],
        }
        assert is_bright(palace, "紫微") is True
        assert is_bright(palace, "天机") is False

    def test_is_dim(self):
        """测试判断星曜是否落陷"""
        palace = {
            "majorStars": [{"name": "紫微", "brightness": "dim"}],
            "minorStars": [],
        }
        assert is_dim(palace, "紫微") is True
        assert is_dim(palace, "天机") is False

    def test_get_star_brightness(self):
        """测试获取星曜亮度"""
        palace = {
            "majorStars": [{"name": "紫微", "brightness": "bright"}],
            "minorStars": [],
        }
        assert get_star_brightness(palace, "紫微") == "bright"
        assert get_star_brightness(palace, "天机") == ""


class TestSihua:
    """四化分析测试"""

    def test_get_sihua_by_stem(self):
        """测试天干四化查询"""
        sihua = get_sihua_by_stem("甲")
        assert sihua == {
            "化禄": "廉贞",
            "化权": "破军",
            "化科": "武曲",
            "化忌": "太阳",
        }

    def test_get_sihua_by_stem_invalid(self):
        """测试无效天干"""
        sihua = get_sihua_by_stem("无效")
        assert sihua == {}

    def test_get_year_stem(self):
        """测试获取年柱天干"""
        assert get_year_stem(2024) == "甲"
        assert get_year_stem(2025) == "乙"
        assert get_year_stem(2026) == "丙"

    def test_get_year_branch(self):
        """测试获取年柱地支"""
        assert get_year_branch(2024) == "辰"
        assert get_year_branch(2025) == "巳"
        assert get_year_branch(2026) == "午"

    def test_analyze_benming_sihua(self):
        """测试本命四化分析"""
        chart = {
            "yearStem": "甲",
            "palaces": [
                {
                    "name": "命宫",
                    "majorStars": [
                        {"name": "廉贞", "brightness": "bright"},
                    ],
                },
                {
                    "name": "财帛宫",
                    "majorStars": [
                        {"name": "武曲", "brightness": "normal"},
                    ],
                },
            ]
        }

        result = analyze_sihua(chart)
        assert "benming" in result
        assert "sihua" in result["benming"]
        assert result["benming"]["sihua"]["化禄"] == "廉贞"

    def test_analyze_sihua_with_year(self):
        """测试带年份的四化分析"""
        chart = {
            "yearStem": "甲",
            "palaces": [
                {
                    "name": "命宫",
                    "majorStars": [
                        {"name": "廉贞", "brightness": "bright"},
                    ],
                },
            ]
        }

        result = analyze_sihua(chart, query_year=2026)
        assert "liunian" in result
        assert result["liunian"]["stem"] == "丙"


class TestPatterns:
    """格局识别测试"""

    def test_detect_zi_fu(self):
        """测试紫府同宫格检测"""
        chart = {
            "palaces": [
                {
                    "name": "命宫",
                    "earthlyBranch": "寅",
                    "majorStars": [
                        {"name": "紫微", "brightness": "bright"},
                        {"name": "天府", "brightness": "bright"},
                    ],
                    "minorStars": [],
                },
            ]
        }

        pattern = detect_zi_fu(chart)
        assert pattern is not None
        assert pattern.name == "紫府同宫"
        assert pattern.level == "excellent"

    def test_detect_zi_fu_no_pattern(self):
        """测试非紫府同宫格"""
        chart = {
            "palaces": [
                {
                    "name": "命宫",
                    "earthlyBranch": "寅",
                    "majorStars": [
                        {"name": "紫微", "brightness": "bright"},
                    ],
                    "minorStars": [],
                },
            ]
        }

        pattern = detect_zi_fu(chart)
        assert pattern is None

    def test_detect_patterns(self):
        """测试格局检测主函数"""
        chart = {
            "palaces": [
                {
                    "name": "命宫",
                    "earthlyBranch": "寅",
                    "majorStars": [
                        {"name": "紫微", "brightness": "bright"},
                        {"name": "天府", "brightness": "bright"},
                    ],
                    "minorStars": [],
                },
            ]
        }

        patterns = detect_patterns(chart)
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        assert patterns[0].name == "紫府同宫"


class TestStars:
    """星曜解读测试"""

    def test_analyze_star_in_palace(self):
        """测试星曜在宫位的影响"""
        result = analyze_star_in_palace("紫微", "命宫", "bright")
        assert result["star"] == "紫微"
        assert result["palace"] == "命宫"
        assert result["brightness"] == "bright"
        assert "庙旺" in result["description"]

    def test_analyze_star_in_palace_dim(self):
        """测试星曜落陷"""
        result = analyze_star_in_palace("紫微", "命宫", "dim")
        assert "落陷" in result["description"]

    def test_analyze_star_in_palace_unknown(self):
        """测试未知星曜"""
        result = analyze_star_in_palace("未知星", "命宫")
        assert "error" in result

    def test_analyze_ming_palace(self):
        """测试命宫主星分析"""
        chart = {
            "palaces": [
                {
                    "name": "命宫",
                    "majorStars": [
                        {"name": "紫微", "brightness": "bright"},
                    ],
                    "minorStars": [],
                },
            ]
        }

        result = analyze_ming_palace(chart)
        assert "major_stars" in result
        assert "summary" in result
        assert len(result["major_stars"]) == 1


class TestNarrator:
    """叙述器测试"""

    def test_narrate_ming_palace(self):
        """测试命宫叙述"""
        from bazi_pro.core.ziwei.narrator import narrate_ming_palace

        chart = {
            "palaces": [
                {
                    "name": "命宫",
                    "majorStars": [
                        {"name": "紫微", "brightness": "bright"},
                    ],
                    "minorStars": [],
                },
            ]
        }

        result = narrate_ming_palace(chart)
        assert "命宫分析" in result
        assert "紫微" in result

    def test_narrate_patterns(self):
        """测试格局叙述"""
        from bazi_pro.core.ziwei.narrator import narrate_patterns

        chart = {
            "palaces": [
                {
                    "name": "命宫",
                    "earthlyBranch": "寅",
                    "majorStars": [
                        {"name": "紫微", "brightness": "bright"},
                        {"name": "天府", "brightness": "bright"},
                    ],
                    "minorStars": [],
                },
            ]
        }

        result = narrate_patterns(chart)
        assert "格局分析" in result
        assert "紫府同宫" in result

    def test_narrate_sihua(self):
        """测试四化叙述"""
        from bazi_pro.core.ziwei.narrator import narrate_sihua

        chart = {
            "yearStem": "甲",
            "palaces": [
                {
                    "name": "命宫",
                    "majorStars": [
                        {"name": "廉贞", "brightness": "bright"},
                    ],
                    "minorStars": [],
                },
            ]
        }

        result = narrate_sihua(chart)
        assert "四化分析" in result
        assert "化禄" in result

    def test_narrate_ziwei(self):
        """测试紫微斗数叙述器"""
        chart = {
            "soul": "紫微",
            "body": "天机",
            "fiveElementsClass": "水二局",
            "yearStem": "甲",
            "palaces": [
                {
                    "name": "命宫",
                    "earthlyBranch": "寅",
                    "majorStars": [
                        {"name": "紫微", "brightness": "bright"},
                    ],
                    "minorStars": [],
                },
                {
                    "name": "财帛宫",
                    "earthlyBranch": "午",
                    "majorStars": [
                        {"name": "武曲", "brightness": "normal"},
                    ],
                    "minorStars": [],
                },
                {
                    "name": "官禄宫",
                    "earthlyBranch": "戌",
                    "majorStars": [
                        {"name": "天同", "brightness": "bright"},
                    ],
                    "minorStars": [],
                },
                {
                    "name": "夫妻宫",
                    "earthlyBranch": "辰",
                    "majorStars": [
                        {"name": "太阴", "brightness": "normal"},
                    ],
                    "minorStars": [],
                },
                {
                    "name": "疾厄宫",
                    "earthlyBranch": "子",
                    "majorStars": [
                        {"name": "天机", "brightness": "bright"},
                    ],
                    "minorStars": [],
                },
            ]
        }

        result = narrate_ziwei(chart)
        assert "ming_palace" in result
        assert "pattern" in result
        assert "sihua" in result
        assert "wealth" in result
        assert "career" in result
        assert "marriage" in result
        assert "health" in result
        assert "summary" in result
        assert "overview" in result


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_chart(self):
        """测试空命盘"""
        chart = {"palaces": []}
        patterns = detect_patterns(chart)
        assert isinstance(patterns, list)
        assert len(patterns) == 0

    def test_missing_year_stem(self):
        """测试缺失年干"""
        chart = {"palaces": []}
        result = analyze_sihua(chart)
        assert "benming" in result

    def test_palace_no_major_stars(self):
        """测试宫位无主星"""
        palace = {"majorStars": [], "minorStars": []}
        assert has_star(palace, "紫微") is False
        assert is_bright(palace, "紫微") is False
        assert is_dim(palace, "紫微") is False
        assert get_star_brightness(palace, "紫微") == ""

    def test_narrate_empty_chart(self):
        """测试空命盘叙述"""
        chart = {"palaces": []}
        result = narrate_ziwei(chart)
        assert "ming_palace" in result
        assert "pattern" in result

    def test_find_star_not_found(self):
        """测试查找不存在的星曜"""
        from bazi_pro.core.ziwei.utils import _find_star
        palace = {"majorStars": [{"name": "紫微", "brightness": "bright"}], "minorStars": []}
        assert _find_star(palace, "天机") is None
        assert _find_star(palace, "紫微") is not None


class TestSihuaApi:
    """四化 API 端点测试"""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from server.app import app
        return TestClient(app)

    def test_sihua_basic(self, client):
        """测试基本四化查询（不带 query_year）"""
        resp = client.post("/api/v2/ziwei/sihua", json={
            "solar_date": "1990-01-01",
            "hour": 8,
            "gender": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "benming" in data
        assert "daxian" in data
        # 大限四化正常返回
        assert len(data["daxian"]) == 12
        assert "sihua" in data["daxian"][0]
        # 不带 query_year 时不应有 liunian
        assert "liunian" not in data

    def test_sihua_with_query_year(self, client):
        """测试带 query_year 的四化查询"""
        resp = client.post("/api/v2/ziwei/sihua", json={
            "solar_date": "1990-01-01",
            "hour": 8,
            "gender": 1,
            "query_year": 2026,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "benming" in data
        assert "daxian" in data
        assert "liunian" in data
        # 2026 年干为丙
        assert data["liunian"]["stem"] == "丙"
        assert "sihua" in data["liunian"]

    def test_sihua_daxian_count(self, client):
        """测试大限四化返回 12 个"""
        resp = client.post("/api/v2/ziwei/sihua", json={
            "solar_date": "1990-01-01",
            "hour": 8,
            "gender": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["daxian"]) == 12

    def test_sihua_missing_required_field(self, client):
        """测试缺少必填字段"""
        resp = client.post("/api/v2/ziwei/sihua", json={
            "hour": 8,
        })
        assert resp.status_code == 422

    def test_sihua_invalid_hour(self, client):
        """测试无效小时值"""
        resp = client.post("/api/v2/ziwei/sihua", json={
            "solar_date": "1990-01-01",
            "hour": 25,
            "gender": 1,
        })
        assert resp.status_code == 422


class TestDayunApi:
    """大限（大运）API 端点测试"""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from server.app import app
        return TestClient(app)

    def test_dayun_basic(self, client):
        """测试基本大限查询"""
        resp = client.post("/api/v2/ziwei/dayun", json={
            "solar_date": "1990-01-01",
            "hour": 8,
            "gender": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "dayun" in data
        assert isinstance(data["dayun"], list)
        assert len(data["dayun"]) > 0

    def test_dayun_structure(self, client):
        """测试大限返回结构"""
        resp = client.post("/api/v2/ziwei/dayun", json={
            "solar_date": "1990-01-01",
            "hour": 8,
            "gender": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        first = data["dayun"][0]
        # 必须包含的字段
        assert "age_range" in first
        assert "palace" in first
        assert "major_stars" in first
        assert "sihua_flow" in first
        assert "heavenly_stem" in first
        assert "earthly_branch" in first

    def test_dayun_sorted_by_age(self, client):
        """测试大限按年龄排序"""
        resp = client.post("/api/v2/ziwei/dayun", json={
            "solar_date": "1990-01-01",
            "hour": 8,
            "gender": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        ages = [d["age_start"] for d in data["dayun"]]
        assert ages == sorted(ages)

    def test_dayun_chart_summary(self, client):
        """测试大限包含命盘摘要"""
        resp = client.post("/api/v2/ziwei/dayun", json={
            "solar_date": "1990-01-01",
            "hour": 8,
            "gender": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "chart_summary" in data
        summary = data["chart_summary"]
        assert "soul" in summary
        assert "body" in summary
        assert "fiveElementsClass" in summary

    def test_dayun_female(self, client):
        """测试女性大限查询"""
        resp = client.post("/api/v2/ziwei/dayun", json={
            "solar_date": "1990-01-01",
            "hour": 8,
            "gender": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["dayun"]) > 0

    def test_dayun_missing_required_field(self, client):
        """测试缺少必填字段"""
        resp = client.post("/api/v2/ziwei/dayun", json={
            "hour": 8,
        })
        assert resp.status_code == 422

    def test_dayun_invalid_hour(self, client):
        """测试无效小时值"""
        resp = client.post("/api/v2/ziwei/dayun", json={
            "solar_date": "1990-01-01",
            "hour": 25,
            "gender": 1,
        })
        assert resp.status_code == 422


class TestLiunianApi:
    """流年 API 端点测试"""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from server.app import app
        return TestClient(app)

    def test_liunian_basic(self, client):
        """测试基本流年查询"""
        resp = client.post("/api/v2/ziwei/liunian", json={
            "solar_date": "1990-01-01",
            "hour": 8,
            "gender": 1,
            "query_year": 2026,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "year" in data
        assert data["year"] == 2026

    def test_liunian_structure(self, client):
        """测试流年返回结构"""
        resp = client.post("/api/v2/ziwei/liunian", json={
            "solar_date": "1990-01-01",
            "hour": 8,
            "gender": 1,
            "query_year": 2026,
        })
        assert resp.status_code == 200
        data = resp.json()
        # 流年基本信息
        assert "nominal_age" in data
        assert "lunar_date" in data
        # 流年干支
        assert "yearly" in data
        yearly = data["yearly"]
        assert "heavenly_stem" in yearly
        assert "earthly_branch" in yearly
        assert "ganzhi" in yearly
        assert "sihua" in yearly
        # 大限信息
        assert "decadal" in data
        decadal = data["decadal"]
        assert "heavenly_stem" in decadal
        assert "earthly_branch" in decadal
        assert "ganzhi" in decadal

    def test_liunian_sihua_keys(self, client):
        """测试流年四化包含标准四化键"""
        resp = client.post("/api/v2/ziwei/liunian", json={
            "solar_date": "1990-01-01",
            "hour": 8,
            "gender": 1,
            "query_year": 2026,
        })
        assert resp.status_code == 200
        data = resp.json()
        sihua = data["yearly"]["sihua"]
        # 四化应包含化禄、化权、化科、化忌
        assert "化禄" in sihua
        assert "化权" in sihua
        assert "化科" in sihua
        assert "化忌" in sihua

    def test_liunian_default_year(self, client):
        """测试不指定年份时使用当年"""
        resp = client.post("/api/v2/ziwei/liunian", json={
            "solar_date": "1990-01-01",
            "hour": 8,
            "gender": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        from datetime import date
        assert data["year"] == date.today().year

    def test_liunian_missing_required_field(self, client):
        """测试缺少必填字段"""
        resp = client.post("/api/v2/ziwei/liunian", json={
            "hour": 8,
        })
        assert resp.status_code == 422

    def test_liunian_invalid_hour(self, client):
        """测试无效小时值"""
        resp = client.post("/api/v2/ziwei/liunian", json={
            "solar_date": "1990-01-01",
            "hour": 25,
            "gender": 1,
        })
        assert resp.status_code == 422


class TestIntegration:
    """集成测试"""

    def test_ziwei_module_import(self):
        """测试紫微斗数模块导入"""
        from bazi_pro.core.ziwei import (
            SI_HUA_TABLE,
            STAR_NATURE,
            analyze_ming_palace,
            analyze_sihua,
            analyze_star_in_palace,
            detect_patterns,
            get_sihua_by_stem,
            narrate_ziwei,
        )

        assert SI_HUA_TABLE is not None
        assert STAR_NATURE is not None
        assert callable(detect_patterns)
        assert callable(analyze_sihua)
        assert callable(get_sihua_by_stem)
        assert callable(analyze_star_in_palace)
        assert callable(analyze_ming_palace)
        assert callable(narrate_ziwei)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
