"""server/llm_prompts.py 单元测试 — 覆盖 build_chat_system_prompt、build_report_system_prompt、build_analysis_system_prompt"""

from server.llm_prompts import (
    build_analysis_system_prompt,
    build_chat_system_prompt,
    build_report_system_prompt,
)

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

def _base_analysis() -> dict:
    """基础分析结果 dict"""
    return {
        "validation": {
            "day_master": "甲",
            "bazi": "庚午 己卯 甲子 丁卯",
            "gender": "男",
            "生肖": "马",
        },
        "birth_year": 1990,
        "strength": {
            "deling": {"status": "得令", "score": 30},
            "dedi": {"score": 20},
            "deshi": {"score": 15},
            "wangshuai": {"verdict": "身旺"},
        },
        "pattern": {"pattern": "正官格", "layer": "L1", "confidence": 0.85, "reason": "月令透干"},
        "yongshen": {"yongshen": "金", "xishen": ["水"], "jishen": ["木"]},
        "elements": {"percent": {"木": 35.0, "火": 20.0, "土": 15.0, "金": 15.0, "水": 15.0}},
        "relations": [],
        "tiaohou": {"tiaohou_gan": [], "tiaohou_wx": []},
        "shishen": {"pillars": []},
        "shensha": {},
        "gongwei": {},
        "dayun": [],
        "disease": {},
    }


def _analysis_with_pattern(pattern_name: str) -> dict:
    """指定格局名称的分析结果"""
    d = _base_analysis()
    d["pattern"] = {"pattern": pattern_name, "layer": "L0", "confidence": 0.9, "reason": "测试"}
    return d


# --------------------------------------------------------------------------- #
# build_chat_system_prompt 测试
# --------------------------------------------------------------------------- #

class TestBuildChatSystemPrompt:
    """build_chat_system_prompt 测试套件"""

    # --- 5 种格局类型检测 ---

    def test_pattern_zhuanwang(self):
        """专旺格 → 开场模板包含'专旺'"""
        d = _analysis_with_pattern("曲直格（专旺）")
        result = build_chat_system_prompt(d, {})
        assert "专旺" in result or "一行专旺" in result

    def test_pattern_cong(self):
        """从格 → 开场模板包含'从格'或'从'"""
        d = _analysis_with_pattern("从财格")
        result = build_chat_system_prompt(d, {})
        assert "从格" in result or "从者" in result or "从论" in result

    def test_pattern_jianlu(self):
        """建禄格 → 开场模板包含'建禄'或'禄'"""
        d = _analysis_with_pattern("建禄格")
        result = build_chat_system_prompt(d, {})
        assert "建禄" in result or "禄神" in result or "禄" in result

    def test_pattern_huaqi(self):
        """化气格 → 开场模板包含'化气'或'化'"""
        d = _analysis_with_pattern("甲己化土格")
        result = build_chat_system_prompt(d, {})
        assert "化气" in result or "合化" in result or "化象" in result

    def test_pattern_zhengge(self):
        """正格 → 开场模板包含'正格'或'中和'"""
        d = _analysis_with_pattern("正官格")
        result = build_chat_system_prompt(d, {})
        assert "正格" in result or "中和" in result

    # --- 日主提取 ---

    def test_day_master_from_validation(self):
        """日主从 validation 中提取"""
        d = _base_analysis()
        result = build_chat_system_prompt(d, {})
        assert "甲" in result

    def test_day_master_fallback(self):
        """validation 无 day_master 时从顶层取"""
        d = _base_analysis()
        d["validation"] = {"bazi": "庚午 己卯 甲子 丁卯"}
        d["day_master"] = "乙"
        result = build_chat_system_prompt(d, {})
        assert "乙" in result

    # --- 基本结构检查 ---

    def test_contains_school_context(self):
        """输出包含派别上下文"""
        result = build_chat_system_prompt(_base_analysis(), {}, school="ziping")
        assert "传统子平法" in result

    def test_contains_anti_hallucination(self):
        """输出包含防幻觉规则"""
        result = build_chat_system_prompt(_base_analysis(), {})
        assert "防幻觉" in result

    def test_contains_rhythm_template(self):
        """输出包含断命节奏模板"""
        result = build_chat_system_prompt(_base_analysis(), {})
        assert "观大局" in result

    def test_contains_retrieval_results(self):
        """输出包含检索结果"""
        retrieval = "食神制杀相关内容"
        result = build_chat_system_prompt(_base_analysis(), {}, retrieval_results=retrieval)
        assert "食神制杀" in result

    def test_contains_retrieval_list(self):
        """检索结果为 list 时"""
        retrieval = [{"source": "滴天髓", "text": "何知其人富", "score": 0.9}]
        result = build_chat_system_prompt(_base_analysis(), {}, retrieval_results=retrieval)
        assert "滴天髓" in result

    def test_mangpai_school(self):
        """盲派"""
        result = build_chat_system_prompt(_base_analysis(), {}, school="mangpai")
        assert "盲派" in result

    def test_xinpai_school(self):
        """新派"""
        result = build_chat_system_prompt(_base_analysis(), {}, school="xinpai")
        assert "新派" in result


# --------------------------------------------------------------------------- #
# build_report_system_prompt 测试
# --------------------------------------------------------------------------- #

REPORT_CHAPTER_KEYS = [
    "overview",
    "past_validation",
    "future_luck",
    "career_wealth",
    "marriage_love",
    "family",
    "health",
    "guidance",
    "ziwei",
]


class TestBuildReportSystemPrompt:
    """build_report_system_prompt 测试套件"""

    def test_contains_all_9_chapter_keys(self):
        """输出包含所有 9 个章节键"""
        result = build_report_system_prompt(_base_analysis(), {})
        for key in REPORT_CHAPTER_KEYS:
            assert key in result, f"缺少章节键: {key}"

    def test_contains_report_structure_json(self):
        """输出包含 JSON 结构"""
        result = build_report_system_prompt(_base_analysis(), {})
        assert "overview" in result
        assert "命盘总论" in result or "总览" in result

    def test_contains_school_context(self):
        """输出包含派别上下文"""
        result = build_report_system_prompt(_base_analysis(), {}, school="ziping")
        assert "传统子平法" in result

    def test_contains_anti_hallucination(self):
        """输出包含防幻觉规则"""
        result = build_report_system_prompt(_base_analysis(), {})
        assert "防幻觉" in result

    def test_contains_time_chain(self):
        """输出包含流年推理链"""
        result = build_report_system_prompt(_base_analysis(), {})
        assert "流年" in result

    def test_with_dayun_data(self):
        """大运数据注入"""
        dayun = [
            {"age_range": "1-10", "gan_zhi": "庚辰", "description": "早年"},
        ]
        result = build_report_system_prompt(_base_analysis(), {}, dayun_data=dayun)
        assert "庚辰" in result

    def test_with_disease_data(self):
        """格局之病数据注入"""
        d = _base_analysis()
        d["disease"] = {
            "has_disease": True,
            "items": [{"name": "伤官见官", "description": "官星被伤官克制"}],
        }
        result = build_report_system_prompt(d, {})
        assert "伤官见官" in result

    def test_with_retrieval_results(self):
        """检索结果注入"""
        retrieval = {"overview": [{"source": "子平真诠", "content": "格局论"}]}
        result = build_report_system_prompt(_base_analysis(), {}, retrieval_results=retrieval)
        assert "格局论" in result

    def test_no_dayun_fallback(self):
        """无大运数据时的降级"""
        result = build_report_system_prompt(_base_analysis(), {}, dayun_data=None)
        assert isinstance(result, str)


# --------------------------------------------------------------------------- #
# build_analysis_system_prompt 测试
# --------------------------------------------------------------------------- #

class TestBuildAnalysisSystemPrompt:
    """build_analysis_system_prompt 测试套件"""

    def test_basic_call(self):
        """基本调用不崩溃"""
        result = build_analysis_system_prompt(_base_analysis(), {})
        assert isinstance(result, str)
        assert len(result) > 100

    def test_contains_school_context(self):
        """输出包含派别上下文"""
        result = build_analysis_system_prompt(_base_analysis(), {}, school="ziping")
        assert "传统子平法" in result

    def test_contains_analysis_context(self):
        """输出包含命盘数据"""
        result = build_analysis_system_prompt(_base_analysis(), {})
        assert "命盘数据" in result

    def test_contains_role_description(self):
        """输出包含角色描述"""
        result = build_analysis_system_prompt(_base_analysis(), {})
        assert "命理师" in result

    def test_different_schools(self):
        """不同学校输出不同"""
        r1 = build_analysis_system_prompt(_base_analysis(), {}, school="ziping")
        r2 = build_analysis_system_prompt(_base_analysis(), {}, school="mangpai")
        assert r1 != r2

    def test_with_narration(self):
        """narration 注入"""
        narration = {"overview": "测试叙述"}
        result = build_analysis_system_prompt(_base_analysis(), narration)
        assert "测试叙述" in result
