"""命理工具集 — 定义 LLM function calling 的工具 Schema 与执行函数

5 个工具：
1. paipan         — 排盘（根据出生信息计算八字）
2. query_geju     — 查格局（查询命盘格局判定）
3. query_yongshen  — 查用神（查询喜用神推导）
4. query_shensha   — 查神煞（查询神煞信息）
5. query_classical — 查古籍（检索古籍条文）
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger("bazi-pro.agents.tools")

# ---------------------------------------------------------------------------
# 1. OpenAI Function Calling 工具 Schema 定义
# ---------------------------------------------------------------------------

BAZI_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "paipan",
            "description": "根据出生日期时间排盘，计算四柱八字、十神、藏干、五行力量等确定性数据。当用户提到具体的出生日期时间时调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "solar_datetime": {
                        "type": "string",
                        "description": "公历出生日期时间，格式：YYYY-MM-DD HH:MM，如 '1990-05-15 08:30'",
                    },
                    "gender": {
                        "type": "string",
                        "enum": ["男", "女"],
                        "description": "性别",
                    },
                },
                "required": ["solar_datetime", "gender"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_geju",
            "description": "查询命盘的格局判定结果，包括格局类型（正格/专旺格/从格/化气格等）、破格条件、置信度。需要先排盘获取八字数据后才能调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "bazi": {
                        "type": "string",
                        "description": "八字，四柱用空格分隔，如 '甲子 乙丑 丙寅 丁卯'",
                    },
                    "day_master": {
                        "type": "string",
                        "description": "日主天干，如 '丙'",
                    },
                },
                "required": ["bazi", "day_master"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_yongshen",
            "description": "查询命盘的喜用神推导结果，包括用神、喜神、忌神及其五行属性。需要先排盘获取八字数据后才能调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "bazi": {
                        "type": "string",
                        "description": "八字，四柱用空格分隔，如 '甲子 乙丑 丙寅 丁卯'",
                    },
                    "day_master": {
                        "type": "string",
                        "description": "日主天干，如 '丙'",
                    },
                },
                "required": ["bazi", "day_master"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_shensha",
            "description": "查询命盘的神煞信息，包括天乙贵人、文昌、驿马、桃花、华盖、将星、禄神、羊刃等 40+ 种神煞。需要先排盘获取八字数据后才能调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "bazi": {
                        "type": "string",
                        "description": "八字，四柱用空格分隔，如 '甲子 乙丑 丙寅 丁卯'",
                    },
                    "gender": {
                        "type": "string",
                        "enum": ["男", "女"],
                        "description": "性别（部分神煞男女有别）",
                    },
                },
                "required": ["bazi", "gender"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_classical",
            "description": "检索古籍命理条文，支持按关键词搜索《子平真诠》《滴天髓》《渊海子平》《穷通宝鉴》《神峰通考》《三命通会》等经典。当需要引用古籍原文或查找命理依据时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "检索关键词或问题，如 '食神制杀 身弱'、'伤官见官 格局'",
                    },
                    "k": {
                        "type": "integer",
                        "description": "返回结果数量，默认 5",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# 2. 工具执行函数
# ---------------------------------------------------------------------------


async def _run_paipan(solar_datetime: str, gender: str) -> dict[str, Any]:
    """执行排盘，返回八字、十神、藏干等确定性数据。"""
    from bazi_pro.paipan import paipan_from_datetime

    result = await asyncio.to_thread(paipan_from_datetime, solar_datetime, gender)
    if result.get("status") != "completed":
        return {"error": result.get("message", "排盘失败")}

    # 提取关键信息，避免返回过大的数据
    pillars = result.get("pillars", [])
    dayun = result.get("dayun", [])

    pillar_strs = []
    for p in pillars:
        gan = p.get("gan", "")
        zhi = p.get("zhi", "")
        pos = p.get("position", "")
        pillar_strs.append(f"{pos}: {gan}{zhi}")

    dayun_strs = []
    for dy in dayun:
        age_range = dy.get("age_range", "")
        gan_zhi = dy.get("gan_zhi", "")
        dayun_strs.append(f"{age_range}: {gan_zhi}")

    return {
        "八字": " ".join(p.get("gan", "") + p.get("zhi", "") for p in pillars),
        "四柱": pillar_strs,
        "日主": result.get("day_master", ""),
        "性别": gender,
        "阳历": solar_datetime,
        "生肖": result.get("shengxiao", ""),
        "大运": dayun_strs,
        "起运年龄": result.get("qiyun_age", 0),
    }


async def _run_query_geju(bazi: str, day_master: str) -> dict[str, Any]:
    """查询格局判定结果。"""
    from bazi_pro.core import full_analysis

    mcp_json = {"八字": bazi, "日主": day_master}
    result = await asyncio.to_thread(full_analysis, mcp_json)

    if result.get("status") != "completed":
        return {"error": result.get("errors", "分析失败")}

    pattern = result.get("pattern", {})
    yongshen = result.get("yongshen", {})
    wangshuai = result.get("strength", {}).get("wangshuai", {})

    return {
        "格局": {
            "类型": pattern.get("pattern", ""),
            "层级": pattern.get("layer", ""),
            "置信度": f"{pattern.get('confidence', 0):.0%}",
            "理由": pattern.get("reason", ""),
        },
        "旺衰判定": wangshuai.get("verdict", ""),
        "用神": yongshen.get("yongshen", ""),
        "喜神": yongshen.get("xishen", []),
        "忌神": yongshen.get("jishen", []),
    }


async def _run_query_yongshen(bazi: str, day_master: str) -> dict[str, Any]:
    """查询喜用神推导结果。"""
    from bazi_pro.core import full_analysis

    mcp_json = {"八字": bazi, "日主": day_master}
    result = await asyncio.to_thread(full_analysis, mcp_json)

    if result.get("status") != "completed":
        return {"error": result.get("errors", "分析失败")}

    yongshen = result.get("yongshen", {})
    tiaohou = result.get("tiaohou", {})
    pattern = result.get("pattern", {})
    wangshuai = result.get("strength", {}).get("wangshuai", {})

    return {
        "格局": pattern.get("pattern", ""),
        "旺衰": wangshuai.get("verdict", ""),
        "用神": yongshen.get("yongshen", ""),
        "用神五行": yongshen.get("yongshen_wx", ""),
        "喜神": yongshen.get("xishen", []),
        "忌神": yongshen.get("jishen", []),
        "调候用神": tiaohou.get("tiaohou_gan", []),
        "调候五行": tiaohou.get("tiaohou_wx", []),
    }


async def _run_query_shensha(bazi: str, gender: str) -> dict[str, Any]:
    """查询神煞信息。"""
    from server.shensha import calc_shensha

    bazi_parts = bazi.split()
    if len(bazi_parts) != 4:
        return {"error": "八字格式错误，需四柱用空格分隔"}

    gender_int = 1 if gender == "男" else 0
    shensha_list = await asyncio.to_thread(calc_shensha, bazi_parts, gender_int)

    # 按类别分组
    grouped: dict[str, list[dict[str, str]]] = {}
    for item in shensha_list:
        name = item.get("name", "")
        category = item.get("category", "其他")
        desc = item.get("description", "")
        position = item.get("position", "")
        if name:
            grouped.setdefault(category, []).append({
                "名称": name,
                "位置": position,
                "含义": desc,
            })

    return {
        "神煞数量": len(shensha_list),
        "神煞": grouped,
    }


async def _run_query_classical(query: str, k: int = 5) -> dict[str, Any]:
    """检索古籍条文。"""
    from bazi_pro.retrieve_classical import retrieve

    # 解析语料库路径
    corpus_path = _resolve_corpus_path()
    if not corpus_path:
        return {"error": "古籍语料库未找到"}

    raw = await asyncio.to_thread(retrieve, corpus_path, query, k=k)

    results = raw.get("results", [])
    formatted = []
    for r in results:
        formatted.append({
            "来源": r.get("source", ""),
            "主题": r.get("topic", ""),
            "内容": r.get("content", ""),
            "相关度": round(r.get("score", 0), 4),
        })

    return {
        "查询": query,
        "结果数量": len(formatted),
        "条文": formatted,
    }


def _resolve_corpus_path() -> str:
    """解析古籍语料库路径。"""
    import os

    try:
        from bazi_pro.retrieve_classical import _resolve_corpus
        return _resolve_corpus()
    except (ImportError, AttributeError):
        pass

    # 降级：手动查找
    try:
        from importlib.resources import files
        data_dir = files("bazi_pro.data")
        corpus = data_dir.joinpath("classical_corpus.md")
        if corpus.is_file():
            return str(corpus)
    except Exception:
        pass

    script_dir = os.path.dirname(os.path.abspath(__file__))
    for candidate in [
        os.path.join(script_dir, "..", "..", "bazi_pro", "data", "classical_corpus.md"),
        os.path.join(script_dir, "..", "..", "references", "classical_corpus.md"),
    ]:
        if os.path.exists(candidate):
            return candidate
    return ""


# ---------------------------------------------------------------------------
# 3. 工具调度器
# ---------------------------------------------------------------------------

_TOOL_EXECUTORS: dict[str, Any] = {
    "paipan": _run_paipan,
    "query_geju": _run_query_geju,
    "query_yongshen": _run_query_yongshen,
    "query_shensha": _run_query_shensha,
    "query_classical": _run_query_classical,
}


async def execute_tool(name: str, arguments: dict[str, Any]) -> str:
    """执行指定工具，返回 JSON 字符串结果。

    Args:
        name: 工具名称
        arguments: 工具参数

    Returns:
        JSON 格式的工具执行结果字符串
    """
    executor = _TOOL_EXECUTORS.get(name)
    if not executor:
        return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)

    try:
        result = await executor(**arguments)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("工具 %s 执行失败: %s", name, e, exc_info=True)
        return json.dumps({"error": f"工具执行失败: {e}"}, ensure_ascii=False)


async def execute_tools(tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """批量执行工具调用，返回 tool message 列表。

    Args:
        tool_calls: LLM 返回的 tool_calls 列表

    Returns:
        OpenAI 格式的 tool message 列表，每条包含 role="tool", tool_call_id, content
    """
    messages: list[dict[str, Any]] = []

    # 并行执行所有工具调用
    tasks = []
    call_ids = []
    for tc in tool_calls:
        func = tc.get("function", {})
        name = func.get("name", "")
        args_str = func.get("arguments", "{}")
        call_id = tc.get("id", "")

        try:
            args = json.loads(args_str) if isinstance(args_str, str) else args_str
        except (json.JSONDecodeError, TypeError):
            args = {}

        tasks.append(execute_tool(name, args))
        call_ids.append(call_id)

    results = await asyncio.gather(*tasks)

    for call_id, result_content in zip(call_ids, results):
        messages.append({
            "role": "tool",
            "tool_call_id": call_id,
            "content": result_content,
        })

    return messages
