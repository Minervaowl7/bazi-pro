"""server/agents/tools.py 单元测试

覆盖：
1. BAZI_TOOLS Schema 定义验证（5 个工具）
2. execute_tool 正常调用（mock 底层函数）
3. execute_tool 未知工具错误处理
4. execute_tool 异常传播
5. execute_tools 批量并行执行
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from server.agents.tools import (
    BAZI_TOOLS,
    _resolve_corpus_path,
    execute_tool,
    execute_tools,
)

# ---------------------------------------------------------------------------
# Mock 路径常量 — tools.py 内部使用 local import，需 patch 源模块
# ---------------------------------------------------------------------------
_PATCH_PAIPAN = "bazi_pro.paipan.paipan_from_datetime"
_PATCH_CORE = "bazi_pro.core.full_analysis"
_PATCH_SHENSHA = "server.shensha.calc_shensha"
_PATCH_RETRIEVE = "bazi_pro.retrieve_classical.retrieve"
_PATCH_RESOLVE_CORPUS = "bazi_pro.retrieve_classical._resolve_corpus"

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

EXPECTED_TOOL_NAMES = {"paipan", "query_geju", "query_yongshen", "query_shensha", "query_classical"}


# ---------------------------------------------------------------------------
# 辅助：构造 tool_calls 列表
# ---------------------------------------------------------------------------


def _make_tool_call(name: str, args: dict[str, Any], call_id: str = "call_001") -> dict[str, Any]:
    """构造 OpenAI 格式的 tool_call 字典。"""
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(args, ensure_ascii=False),
        },
    }


# ===================================================================
# 1. Schema 验证
# ===================================================================


class TestBAZIToolsSchema:
    """验证 5 个工具的 Schema 定义完整性。"""

    def test_tools_count(self):
        """BAZI_TOOLS 应恰好包含 5 个工具。"""
        assert len(BAZI_TOOLS) == 5

    def test_all_tool_names_present(self):
        """所有工具名称应齐全。"""
        names = {t["function"]["name"] for t in BAZI_TOOLS}
        assert names == EXPECTED_TOOL_NAMES

    @pytest.mark.parametrize("index", range(5))
    def test_tool_type_field(self, index: int):
        """每个工具的 type 字段应为 'function'。"""
        assert BAZI_TOOLS[index]["type"] == "function"

    @pytest.mark.parametrize("index", range(5))
    def test_tool_has_required_keys(self, index: int):
        """每个工具的 function 应包含 name、description、parameters。"""
        func = BAZI_TOOLS[index]["function"]
        assert "name" in func
        assert "description" in func
        assert "parameters" in func

    @pytest.mark.parametrize("index", range(5))
    def test_tool_parameters_is_object_type(self, index: int):
        """每个工具的 parameters.type 应为 'object'。"""
        params = BAZI_TOOLS[index]["function"]["parameters"]
        assert params["type"] == "object"

    @pytest.mark.parametrize("index", range(5))
    def test_tool_has_properties(self, index: int):
        """每个工具的 parameters 应包含 properties 和 required。"""
        params = BAZI_TOOLS[index]["function"]["parameters"]
        assert "properties" in params
        assert "required" in params

    # --- paipan 专属 ---

    def test_paipan_required_params(self):
        """paipan 工具应要求 solar_datetime 和 gender。"""
        paipan = next(t for t in BAZI_TOOLS if t["function"]["name"] == "paipan")
        required = paipan["function"]["parameters"]["required"]
        assert "solar_datetime" in required
        assert "gender" in required

    def test_paipan_gender_enum(self):
        """paipan 的 gender 应限定为 ['男', '女']。"""
        paipan = next(t for t in BAZI_TOOLS if t["function"]["name"] == "paipan")
        gender = paipan["function"]["parameters"]["properties"]["gender"]
        assert gender["enum"] == ["男", "女"]

    # --- query_geju 专属 ---

    def test_query_geju_required_params(self):
        """query_geju 应要求 bazi 和 day_master。"""
        geju = next(t for t in BAZI_TOOLS if t["function"]["name"] == "query_geju")
        required = geju["function"]["parameters"]["required"]
        assert "bazi" in required
        assert "day_master" in required

    # --- query_yongshen 专属 ---

    def test_query_yongshen_required_params(self):
        """query_yongshen 应要求 bazi 和 day_master。"""
        yongshen = next(t for t in BAZI_TOOLS if t["function"]["name"] == "query_yongshen")
        required = yongshen["function"]["parameters"]["required"]
        assert "bazi" in required
        assert "day_master" in required

    # --- query_shensha 专属 ---

    def test_query_shensha_required_params(self):
        """query_shensha 应要求 bazi 和 gender。"""
        shensha = next(t for t in BAZI_TOOLS if t["function"]["name"] == "query_shensha")
        required = shensha["function"]["parameters"]["required"]
        assert "bazi" in required
        assert "gender" in required

    def test_query_shensha_gender_enum(self):
        """query_shensha 的 gender 应限定为 ['男', '女']。"""
        shensha = next(t for t in BAZI_TOOLS if t["function"]["name"] == "query_shensha")
        gender = shensha["function"]["parameters"]["properties"]["gender"]
        assert gender["enum"] == ["男", "女"]

    # --- query_classical 专属 ---

    def test_query_classical_required_params(self):
        """query_classical 应要求 query。"""
        classical = next(t for t in BAZI_TOOLS if t["function"]["name"] == "query_classical")
        required = classical["function"]["parameters"]["required"]
        assert "query" in required

    def test_query_classical_k_default(self):
        """query_classical 的 k 应有默认值 5。"""
        classical = next(t for t in BAZI_TOOLS if t["function"]["name"] == "query_classical")
        k = classical["function"]["parameters"]["properties"]["k"]
        assert k["default"] == 5


# ===================================================================
# 2. execute_tool — 未知工具
# ===================================================================


class TestExecuteToolUnknown:
    """测试 execute_tool 对未知工具的处理。"""


    async def test_unknown_tool_returns_error_json(self):
        """传入未知工具名应返回含 error 字段的 JSON。"""
        result_str = await execute_tool("nonexistent_tool", {})
        result = json.loads(result_str)
        assert "error" in result
        assert "未知工具" in result["error"]
        assert "nonexistent_tool" in result["error"]


    async def test_unknown_tool_returns_valid_json(self):
        """返回值应为合法 JSON 字符串。"""
        result_str = await execute_tool("fake", {"a": 1})
        parsed = json.loads(result_str)
        assert isinstance(parsed, dict)


# ===================================================================
# 3. execute_tool — 正常调用（mock）
# ===================================================================


class TestExecuteToolPaipan:
    """测试 paipan 工具正常调用。"""


    async def test_paipan_success(self):
        """paipan 正常排盘应返回结构化结果。"""
        mock_result = {
            "status": "completed",
            "pillars": [
                {"gan": "庚", "zhi": "午", "position": "年柱"},
                {"gan": "辛", "zhi": "巳", "position": "月柱"},
                {"gan": "丙", "zhi": "寅", "position": "日柱"},
                {"gan": "壬", "zhi": "辰", "position": "时柱"},
            ],
            "day_master": "丙",
            "shengxiao": "马",
            "dayun": [
                {"age_range": "3-12", "gan_zhi": "壬午"},
            ],
            "qiyun_age": 3,
        }
        with patch(_PATCH_PAIPAN, return_value=mock_result):
            result_str = await execute_tool("paipan", {
                "solar_datetime": "1990-05-15 08:30",
                "gender": "男",
            })
            result = json.loads(result_str)

        assert "八字" in result
        assert "丙寅" in result["八字"]
        assert result["日主"] == "丙"
        assert result["性别"] == "男"
        assert result["生肖"] == "马"
        assert isinstance(result["四柱"], list)
        assert isinstance(result["大运"], list)


    async def test_paipan_failure_status(self):
        """paipan 排盘失败应返回 error。"""
        mock_result = {"status": "error", "message": "日期无效"}
        with patch(_PATCH_PAIPAN, return_value=mock_result):
            result_str = await execute_tool("paipan", {
                "solar_datetime": "invalid",
                "gender": "男",
            })
            result = json.loads(result_str)

        assert "error" in result
        assert "日期无效" in result["error"]


    async def test_paipan_failure_no_message(self):
        """paipan 排盘失败且无 message 时应返回默认错误信息。"""
        mock_result = {"status": "failed"}
        with patch(_PATCH_PAIPAN, return_value=mock_result):
            result_str = await execute_tool("paipan", {
                "solar_datetime": "2000-01-01 00:00",
                "gender": "女",
            })
            result = json.loads(result_str)

        assert "error" in result


class TestExecuteToolQueryGeju:
    """测试 query_geju 工具正常调用。"""


    async def test_query_geju_success(self):
        """query_geju 正常调用应返回格局信息。"""
        mock_result = {
            "status": "completed",
            "pattern": {
                "pattern": "正官格",
                "layer": "L3",
                "confidence": 0.85,
                "reason": "月令透正官",
            },
            "yongshen": {
                "yongshen": "印",
                "xishen": ["印", "比"],
                "jishen": ["财", "官"],
            },
            "strength": {
                "wangshuai": {"verdict": "身弱"},
            },
        }
        with patch(_PATCH_CORE, return_value=mock_result):
            result_str = await execute_tool("query_geju", {
                "bazi": "甲子 乙丑 丙寅 丁卯",
                "day_master": "丙",
            })
            result = json.loads(result_str)

        assert "格局" in result
        assert result["格局"]["类型"] == "正官格"
        assert result["格局"]["置信度"] == "85%"
        assert result["旺衰判定"] == "身弱"


    async def test_query_geju_failure(self):
        """query_geju 分析失败应返回 error。"""
        mock_result = {"status": "error", "errors": "数据格式错误"}
        with patch(_PATCH_CORE, return_value=mock_result):
            result_str = await execute_tool("query_geju", {
                "bazi": "invalid",
                "day_master": "丙",
            })
            result = json.loads(result_str)

        assert "error" in result


class TestExecuteToolQueryYongshen:
    """测试 query_yongshen 工具正常调用。"""


    async def test_query_yongshen_success(self):
        """query_yongshen 正常调用应返回用神信息。"""
        mock_result = {
            "status": "completed",
            "yongshen": {
                "yongshen": "印",
                "yongshen_wx": "木",
                "xishen": ["印", "比"],
                "jishen": ["财", "食"],
            },
            "tiaohou": {
                "tiaohou_gan": ["丙"],
                "tiaohou_wx": ["火"],
            },
            "pattern": {"pattern": "正印格"},
            "strength": {"wangshuai": {"verdict": "身弱"}},
        }
        with patch(_PATCH_CORE, return_value=mock_result):
            result_str = await execute_tool("query_yongshen", {
                "bazi": "甲子 乙丑 丙寅 丁卯",
                "day_master": "丙",
            })
            result = json.loads(result_str)

        assert result["用神"] == "印"
        assert result["用神五行"] == "木"
        assert result["格局"] == "正印格"
        assert isinstance(result["喜神"], list)
        assert isinstance(result["忌神"], list)


    async def test_query_yongshen_failure(self):
        """query_yongshen 分析失败应返回 error。"""
        mock_result = {"status": "error", "errors": "参数错误"}
        with patch(_PATCH_CORE, return_value=mock_result):
            result_str = await execute_tool("query_yongshen", {
                "bazi": "甲子 乙丑 丙寅 丁卯",
                "day_master": "丙",
            })
            result = json.loads(result_str)

        assert "error" in result


class TestExecuteToolQueryShensha:
    """测试 query_shensha 工具正常调用。"""


    async def test_query_shensha_success(self):
        """query_shensha 正常调用应返回神煞列表。"""
        mock_shensha_list = [
            {"name": "天乙贵人", "category": "吉神", "description": "贵人相助", "position": "年支"},
            {"name": "文昌", "category": "吉神", "description": "聪明好学", "position": "日支"},
        ]
        with patch(_PATCH_SHENSHA, return_value=mock_shensha_list):
            result_str = await execute_tool("query_shensha", {
                "bazi": "甲子 乙丑 丙寅 丁卯",
                "gender": "男",
            })
            result = json.loads(result_str)

        assert result["神煞数量"] == 2
        assert "吉神" in result["神煞"]
        assert len(result["神煞"]["吉神"]) == 2


    async def test_query_shensha_invalid_bazi_format(self):
        """query_shensha 传入非四柱八字应返回格式错误。"""
        result_str = await execute_tool("query_shensha", {
            "bazi": "甲子 乙丑 丙寅",
            "gender": "男",
        })
        result = json.loads(result_str)
        assert "error" in result
        assert "格式错误" in result["error"]


    async def test_query_shensha_gender_mapping(self):
        """query_shensha 应正确将性别映射为 1/0。"""
        mock_shensha_list: list[dict[str, Any]] = []
        with patch(_PATCH_SHENSHA, return_value=mock_shensha_list) as mock_calc:
            await execute_tool("query_shensha", {
                "bazi": "甲子 乙丑 丙寅 丁卯",
                "gender": "女",
            })
            # 验证 gender_int=0
            mock_calc.assert_called_once_with(["甲子", "乙丑", "丙寅", "丁卯"], 0)


class TestExecuteToolQueryClassical:
    """测试 query_classical 工具正常调用。"""


    async def test_query_classical_success(self):
        """query_classical 正常检索应返回条文列表。"""
        mock_raw = {
            "results": [
                {
                    "source": "子平真诠",
                    "topic": "食神制杀",
                    "content": "食神制杀，贵格也。",
                    "score": 0.95,
                },
            ],
        }
        with patch(_PATCH_RETRIEVE, return_value=mock_raw):
            result_str = await execute_tool("query_classical", {"query": "食神制杀", "k": 1})
            result = json.loads(result_str)

        assert result["查询"] == "食神制杀"
        assert result["结果数量"] == 1
        assert result["条文"][0]["来源"] == "子平真诠"
        assert result["条文"][0]["相关度"] == 0.95


    async def test_query_classical_no_corpus(self):
        """语料库未找到应返回 error。"""
        with patch("server.agents.tools._resolve_corpus_path", return_value=""):
            result_str = await execute_tool("query_classical", {"query": "测试"})
            result = json.loads(result_str)

        assert "error" in result
        assert "语料库" in result["error"]


# ===================================================================
# 4. execute_tool — 异常传播
# ===================================================================


class TestExecuteToolException:
    """测试 execute_tool 对底层异常的处理。"""


    async def test_executor_raises_returns_error_json(self):
        """底层执行函数抛异常应返回含 error 的 JSON，而非传播异常。"""
        with patch.dict(
            "server.agents.tools._TOOL_EXECUTORS",
            {"paipan": AsyncMock(side_effect=RuntimeError("boom"))},
        ):
            result_str = await execute_tool("paipan", {"solar_datetime": "x", "gender": "男"})
            result = json.loads(result_str)

        assert "error" in result
        assert "boom" in result["error"]


# ===================================================================
# 5. execute_tools — 批量并行执行
# ===================================================================


class TestExecuteTools:
    """测试 execute_tools 批量执行。"""


    async def test_execute_tools_single_call(self):
        """单个 tool_call 应返回一条 tool message。"""
        mock_result = {"status": "completed", "pillars": [], "day_master": "甲", "shengxiao": "鼠", "dayun": [], "qiyun_age": 1}
        with patch(_PATCH_PAIPAN, return_value=mock_result):
            tool_calls = [_make_tool_call("paipan", {"solar_datetime": "2000-01-01 00:00", "gender": "男"}, "call_abc")]
            messages = await execute_tools(tool_calls)

        assert len(messages) == 1
        msg = messages[0]
        assert msg["role"] == "tool"
        assert msg["tool_call_id"] == "call_abc"
        # content 应为合法 JSON
        parsed = json.loads(msg["content"])
        assert isinstance(parsed, dict)


    async def test_execute_tools_multiple_calls_parallel(self):
        """多个 tool_calls 应并行执行并返回对应数量的 messages。"""
        mock_paipan = {
            "status": "completed", "pillars": [], "day_master": "丙",
            "shengxiao": "马", "dayun": [], "qiyun_age": 3,
        }
        mock_geju = {
            "status": "completed",
            "pattern": {"pattern": "正官格", "layer": "L3", "confidence": 0.8, "reason": ""},
            "yongshen": {"yongshen": "印", "xishen": [], "jishen": []},
            "strength": {"wangshuai": {"verdict": "身弱"}},
        }
        with (
            patch(_PATCH_PAIPAN, return_value=mock_paipan),
            patch(_PATCH_CORE, return_value=mock_geju),
        ):
            tool_calls = [
                _make_tool_call("paipan", {"solar_datetime": "1990-05-15 08:30", "gender": "男"}, "call_1"),
                _make_tool_call("query_geju", {"bazi": "庚午 辛巳 丙寅 壬辰", "day_master": "丙"}, "call_2"),
            ]
            messages = await execute_tools(tool_calls)

        assert len(messages) == 2
        assert messages[0]["tool_call_id"] == "call_1"
        assert messages[1]["tool_call_id"] == "call_2"
        # 两个结果都应为合法 JSON
        for msg in messages:
            json.loads(msg["content"])


    async def test_execute_tools_empty_list(self):
        """空 tool_calls 应返回空列表。"""
        messages = await execute_tools([])
        assert messages == []


    async def test_execute_tools_unknown_tool_in_batch(self):
        """批量中包含未知工具应返回 error JSON 而不中断其他工具。"""
        mock_paipan = {
            "status": "completed", "pillars": [], "day_master": "甲",
            "shengxiao": "鼠", "dayun": [], "qiyun_age": 1,
        }
        with patch(_PATCH_PAIPAN, return_value=mock_paipan):
            tool_calls = [
                _make_tool_call("paipan", {"solar_datetime": "2000-01-01 00:00", "gender": "男"}, "call_ok"),
                _make_tool_call("unknown_tool", {}, "call_bad"),
            ]
            messages = await execute_tools(tool_calls)

        assert len(messages) == 2
        # 第一个应成功
        ok_result = json.loads(messages[0]["content"])
        assert "八字" in ok_result
        # 第二个应返回错误
        bad_result = json.loads(messages[1]["content"])
        assert "error" in bad_result


    async def test_execute_tools_malformed_arguments_json(self):
        """arguments 为非法 JSON 字符串时应降级为空 dict。"""
        tool_calls = [{
            "id": "call_malformed",
            "type": "function",
            "function": {
                "name": "paipan",
                "arguments": "NOT VALID JSON {{{",
            },
        }]
        # paipan 会因缺少参数而失败，但不应抛出 JSONDecodeError
        messages = await execute_tools(tool_calls)
        assert len(messages) == 1
        result = json.loads(messages[0]["content"])
        # 应返回 error（因为参数缺失导致 TypeError）
        assert "error" in result


    async def test_execute_tools_preserves_call_id_order(self):
        """返回的 messages 应与输入 tool_calls 的 call_id 顺序一致。"""
        mock_shensha: list[dict[str, Any]] = []
        mock_raw: dict[str, Any] = {"results": []}
        with (
            patch(_PATCH_SHENSHA, return_value=mock_shensha),
            patch(_PATCH_RETRIEVE, return_value=mock_raw),
        ):
            tool_calls = [
                _make_tool_call("query_shensha", {"bazi": "甲子 乙丑 丙寅 丁卯", "gender": "男"}, "id_1"),
                _make_tool_call("query_classical", {"query": "食神"}, "id_2"),
            ]
            messages = await execute_tools(tool_calls)

        assert messages[0]["tool_call_id"] == "id_1"
        assert messages[1]["tool_call_id"] == "id_2"


# ===================================================================
# 6. _resolve_corpus_path
# ===================================================================


class TestResolveCorpusPath:
    """测试 _resolve_corpus_path 辅助函数。"""

    def test_resolve_corpus_path_returns_string(self):
        """_resolve_corpus_path 应返回字符串。"""
        result = _resolve_corpus_path()
        assert isinstance(result, str)

    def test_resolve_corpus_path_with_mock_fallback(self):
        """当 _resolve_corpus 不可用时应走降级路径。"""
        with patch(_PATCH_RESOLVE_CORPUS, side_effect=ImportError):
            # 降级路径可能找到也可能找不到，但不应抛异常
            result = _resolve_corpus_path()
            assert isinstance(result, str)
