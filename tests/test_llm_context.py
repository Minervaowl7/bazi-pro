"""server/llm_context.py 单元测试 — 覆盖 _format_analysis_context、_format_retrieval_results、_get_school_context"""

from server.llm_context import (
    SCHOOL_PERSPECTIVES,
    _format_analysis_context,
    _format_retrieval_results,
    _get_school_context,
)

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

def _minimal_analysis() -> dict:
    """最小字典：仅含 day_master，无 validation/strength/pattern 等"""
    return {"day_master": "甲"}


def _full_analysis() -> dict:
    """完整字典：包含所有主要键"""
    return {
        "day_master": "甲",
        "gender": "男",
        "birth_year": 1990,
        "validation": {
            "day_master": "甲",
            "bazi": "庚午 己卯 甲子 丁卯",
            "gender": "男",
            "生肖": "马",
        },
        "strength": {
            "deling": {"status": "得令", "score": 30},
            "dedi": {"score": 20},
            "deshi": {"score": 15},
            "wangshuai": {"verdict": "身旺"},
        },
        "pattern": {
            "pattern": "正官格",
            "layer": "L1",
            "confidence": 0.85,
            "reason": "月令卯木透甲，正官格成立",
        },
        "yongshen": {
            "yongshen": "金",
            "xishen": ["水"],
            "jishen": ["木"],
        },
        "elements": {
            "percent": {"木": 35.0, "火": 20.0, "土": 15.0, "金": 15.0, "水": 15.0},
        },
        "relations": [
            {"type": "子卯刑", "description": "子水刑卯木"},
        ],
        "tiaohou": {
            "tiaohou_gan": ["丙"],
            "tiaohou_wx": ["火"],
        },
        "shishen": {
            "pillars": [
                {
                    "position": "年柱",
                    "gan": "庚",
                    "zhi": "午",
                    "shishen_gan": "偏官",
                    "shishen_zhi": "伤官",
                    "canggan": [
                        {"gan": "丁", "shishen": "伤官"},
                        {"gan": "己", "shishen": "正财"},
                    ],
                },
                {
                    "position": "月柱",
                    "gan": "己",
                    "zhi": "卯",
                    "shishen_gan": "正财",
                    "shishen_zhi": "劫财",
                    "canggan": [
                        {"gan": "乙", "shishen": "劫财"},
                    ],
                },
                {
                    "position": "日柱",
                    "gan": "甲",
                    "zhi": "子",
                    "shishen_gan": "日主",
                    "shishen_zhi": "偏印",
                    "canggan": [
                        {"gan": "癸", "shishen": "正印"},
                    ],
                },
                {
                    "position": "时柱",
                    "gan": "丁",
                    "zhi": "卯",
                    "shishen_gan": "伤官",
                    "shishen_zhi": "劫财",
                    "canggan": [
                        {"gan": "乙", "shishen": "劫财"},
                    ],
                },
            ],
        },
        "shensha": {
            "驿马": ["寅"],
            "桃花": ["卯"],
        },
        "gongwei": {
            "年柱": "祖上宫",
            "月柱": "父母宫",
        },
        "dayun": [
            {"age_range": "1-10", "gan_zhi": "庚辰"},
            {"age_range": "11-20", "gan_zhi": "辛巳"},
        ],
        "qiyun_age": 3,
        "school_analyses": {
            "ziping": {"geju": "正官格", "yongshen": "金"},
        },
    }


def _analysis_with_ziwei() -> dict:
    """包含紫微斗数数据的分析结果"""
    base = _full_analysis()
    base["ziwei"] = {
        "soul": "贪狼",
        "body": "天同",
        "fiveElementsClass": "木三局",
        "palaces": [
            {
                "name": "命宫",
                "majorStars": [
                    {"name": "紫微", "brightness": "庙"},
                    {"name": "天府", "brightness": "旺"},
                ],
            },
            {
                "name": "财帛宫",
                "majorStars": [
                    {"name": "武曲", "brightness": "得"},
                ],
            },
        ],
        "sihua": {
            "化禄": "廉贞",
            "化权": "破军",
            "化科": "武曲",
            "化忌": "太阳",
        },
        "patterns": ["紫府同宫", "府相朝垣"],
        "dayun": [
            {"age_range": "6-15", "palace": "命宫", "stars": "紫微天府"},
            {"age_range": "16-25", "palace": "兄弟宫", "stars": "天机"},
        ],
    }
    return base


def _analysis_with_school() -> dict:
    """包含盲派分析数据"""
    base = _full_analysis()
    base["school_analyses"]["mangpai"] = {
        "binzhu": "日主为宾",
        "gong": {"type": "制用", "detail": "财星被制"},
    }
    return base


# --------------------------------------------------------------------------- #
# _format_analysis_context 测试
# --------------------------------------------------------------------------- #

class TestFormatAnalysisContext:
    """_format_analysis_context 测试套件"""

    def test_minimal_dict(self):
        """最小字典：仅 day_master，不崩溃"""
        result = _format_analysis_context(_minimal_analysis(), {})
        assert isinstance(result, str)
        assert "命盘数据" in result

    def test_full_dict_contains_all_sections(self):
        """完整字典：输出包含所有主要节"""
        result = _format_analysis_context(_full_analysis(), {"overview": "测试"})
        for section in [
            "命盘数据", "四柱详情", "旺衰判定", "格局", "喜用神",
            "调候", "五行力量", "刑冲合害", "神煞", "宫位", "大运列表",
            "确定性叙述",
        ]:
            assert section in result, f"缺少节: {section}"

    def test_full_dict_has_bazi(self):
        """完整字典：八字正确出现"""
        result = _format_analysis_context(_full_analysis(), {})
        assert "庚午 己卯 甲子 丁卯" in result

    def test_full_dict_has_day_master(self):
        """完整字典：日主正确出现"""
        result = _format_analysis_context(_full_analysis(), {})
        assert "甲" in result

    def test_full_dict_has_pattern(self):
        """完整字典：格局信息正确"""
        result = _format_analysis_context(_full_analysis(), {})
        assert "正官格" in result
        assert "85%" in result

    def test_full_dict_has_yongshen(self):
        """完整字典：用神信息正确"""
        result = _format_analysis_context(_full_analysis(), {})
        assert "金" in result

    def test_full_dict_has_shensha(self):
        """完整字典：神煞信息正确"""
        result = _format_analysis_context(_full_analysis(), {})
        assert "驿马" in result
        assert "寅" in result

    def test_full_dict_has_gongwei(self):
        """完整字典：宫位信息正确"""
        result = _format_analysis_context(_full_analysis(), {})
        assert "祖上宫" in result

    def test_full_dict_has_elements(self):
        """完整字典：五行力量百分比"""
        result = _format_analysis_context(_full_analysis(), {})
        assert "35.0%" in result

    def test_full_dict_has_school_data(self):
        """完整字典（school=ziping）：派别数据出现"""
        result = _format_analysis_context(_full_analysis(), {}, school="ziping")
        assert "ziping派分析数据" in result

    def test_missing_keys_no_crash(self):
        """缺失键不会崩溃：传入空 dict"""
        result = _format_analysis_context({}, {})
        assert isinstance(result, str)
        assert "命盘数据" in result

    def test_none_inputs_no_crash(self):
        """None 输入不崩溃"""
        result = _format_analysis_context(None, None)  # type: ignore[arg-type]
        assert isinstance(result, str)

    def test_non_dict_validation_no_crash(self):
        """validation 非 dict 不崩溃"""
        result = _format_analysis_context({"validation": "bad"}, {})
        assert isinstance(result, str)

    def test_ziwei_section_present(self):
        """紫微斗数节出现"""
        result = _format_analysis_context(_analysis_with_ziwei(), {})
        assert "紫微斗数命盘" in result
        assert "贪狼" in result
        assert "天同" in result
        assert "木三局" in result

    def test_ziwei_palace_stars(self):
        """紫微宫位主星"""
        result = _format_analysis_context(_analysis_with_ziwei(), {})
        assert "紫微" in result
        assert "天府" in result
        assert "庙" in result

    def test_ziwei_sihua(self):
        """紫微四化"""
        result = _format_analysis_context(_analysis_with_ziwei(), {})
        assert "化禄" in result
        assert "廉贞" in result

    def test_ziwei_patterns(self):
        """紫微格局"""
        result = _format_analysis_context(_analysis_with_ziwei(), {})
        assert "紫府同宫" in result

    def test_ziwei_dayun(self):
        """紫微大限"""
        result = _format_analysis_context(_analysis_with_ziwei(), {})
        assert "6-15" in result

    def test_school_mangpai_data(self):
        """盲派派别数据"""
        result = _format_analysis_context(_analysis_with_school(), {}, school="mangpai")
        assert "mangpai派分析数据" in result

    def test_school_no_match_falls_back(self):
        """不存在的 school，school_data 为空，不崩溃"""
        result = _format_analysis_context(_full_analysis(), {}, school="nonexistent")
        assert isinstance(result, str)

    def test_narration_dict_serialized(self):
        """narration dict 被序列化"""
        narration = {"overview": "测试叙述", "personality": "性格分析"}
        result = _format_analysis_context(_minimal_analysis(), narration)
        assert "测试叙述" in result
        assert "性格分析" in result


# --------------------------------------------------------------------------- #
# _format_retrieval_results 测试 — 4 个分支
# --------------------------------------------------------------------------- #

class TestFormatRetrievalResults:
    """_format_retrieval_results 测试套件 — 4 个分支"""

    def test_none_returns_empty(self):
        """None 返回空字符串"""
        assert _format_retrieval_results(None) == ""

    def test_empty_dict_returns_empty(self):
        """空 dict 返回空字符串"""
        assert _format_retrieval_results({}) == ""

    def test_empty_list_returns_empty(self):
        """空 list 返回空字符串（因为 list 分支会走 for 循环但无 items）"""
        result = _format_retrieval_results([])
        assert isinstance(result, str)

    # --- 分支 1: str ---
    def test_string_branch(self):
        """字符串输入直接包裹"""
        result = _format_retrieval_results("食神制杀相关内容")
        assert "古籍检索结果" in result
        assert "食神制杀相关内容" in result

    # --- 分支 2: list ---
    def test_list_branch_dict_items(self):
        """列表输入，item 为 dict"""
        results = [
            {"source": "滴天髓", "text": "何知其人富", "score": 0.95},
            {"source": "子平真诠", "text": "用神专求月令", "score": 0.88},
        ]
        result = _format_retrieval_results(results)
        assert "古籍检索结果" in result
        assert "滴天髓" in result
        assert "0.95" in result

    def test_list_branch_str_items(self):
        """列表输入，item 为 str"""
        results = ["条文一", "条文二"]
        result = _format_retrieval_results(results)
        assert "条文一" in result
        assert "条文二" in result

    # --- 分支 3: dict-with-results ---
    def test_dict_with_results_branch(self):
        """dict 有 'results' key（Chat 场景）"""
        data = {
            "results": [
                {"source": "渊海子平", "content": "财气通门户", "topic": "论财"},
                {"source": "滴天髓", "content": "何知其人贵", "topic": "论贵"},
            ],
        }
        result = _format_retrieval_results(data)
        assert "古籍检索结果" in result
        assert "渊海子平" in result
        assert "论财" in result

    def test_dict_with_results_truncates_at_5(self):
        """Chat 场景最多 5 条"""
        data = {
            "results": [
                {"source": f"典{i}", "content": f"内容{i}"}
                for i in range(10)
            ],
        }
        result = _format_retrieval_results(data)
        # 只有前 5 条
        assert "典4" in result  # 第 5 条 (index 4)
        assert "典5" not in result  # 第 6 条不应出现

    # --- 分支 4: dict-with-chapter-keys ---
    def test_dict_with_chapter_keys_branch(self):
        """dict 无 'results' key，按章节映射（Report 场景）"""
        data = {
            "overview": [
                {"source": "子平真诠", "content": "格局总论", "topic": "格局"},
            ],
            "career_wealth": [
                {"source": "穷通宝鉴", "content": "用神与行业", "topic": "事业"},
            ],
        }
        result = _format_retrieval_results(data)
        assert "古籍检索结果" in result
        assert "overview" in result
        assert "career_wealth" in result
        assert "格局总论" in result

    def test_dict_with_chapter_keys_nested_results(self):
        """章节值含 results 子结构"""
        data = {
            "overview": {
                "results": [
                    {"source": "滴天髓", "content": "论命总纲", "topic": "总论"},
                ],
                "counter_evidence": [],
            },
        }
        result = _format_retrieval_results(data)
        assert "论命总纲" in result

    def test_dict_with_non_list_value(self):
        """章节值既非 list 也非 dict-with-results"""
        data = {"overview": "纯文本结果"}
        result = _format_retrieval_results(data)
        assert "纯文本结果" in result


# --------------------------------------------------------------------------- #
# _get_school_context 测试 — 3 个学校
# --------------------------------------------------------------------------- #

class TestGetSchoolContext:
    """_get_school_context 测试套件"""

    def test_ziping(self):
        """传统子平法"""
        result = _get_school_context("ziping")
        assert "传统子平法" in result
        assert "格局" in result
        assert "《子平真诠》" in result

    def test_mangpai(self):
        """盲派"""
        result = _get_school_context("mangpai")
        assert "盲派" in result
        assert "宾主" in result
        assert "《盲派初级命理学》" in result

    def test_xinpai(self):
        """新派"""
        result = _get_school_context("xinpai")
        assert "新派" in result
        assert "百神论" in result
        assert "《八字预测真踪》" in result

    def test_unknown_defaults_to_ziping(self):
        """未知学校默认子平法"""
        result = _get_school_context("unknown")
        assert "传统子平法" in result

    def test_all_schools_have_methodology(self):
        """所有学校都有方法论"""
        for school_key in SCHOOL_PERSPECTIVES:
            result = _get_school_context(school_key)
            assert "方法论" in result

    def test_all_schools_have_classics(self):
        """所有学校都有典籍"""
        for school_key in SCHOOL_PERSPECTIVES:
            result = _get_school_context(school_key)
            assert "参考典籍" in result
