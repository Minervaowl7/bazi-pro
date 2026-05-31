"""bazi-pro MCP Server — 将八字排盘计算暴露为 MCP 工具

可在 Claude Desktop / Cursor / Claude Code 中直接调用。

启动方式:
    python -m mcp_server.server
"""

import json
import sys
from typing import Any

from bazi_pro.core import full_analysis
from bazi_pro.paipan import paipan_from_datetime


def handle_tool_call(name: str, arguments: dict[str, Any]) -> dict:
    """处理 MCP 工具调用"""
    if name == "bazi_paipan":
        solar = arguments.get("solar_datetime", "")
        gender = arguments.get("gender", "男")
        if not solar:
            return {"error": "缺少 solar_datetime 参数"}
        try:
            result = paipan_from_datetime(solar, gender)
            return result
        except Exception as e:
            return {"error": str(e)}

    elif name == "bazi_analyze":
        bazi = arguments.get("bazi", "")
        day_master = arguments.get("day_master", "")
        gender = arguments.get("gender", "男")
        if not bazi or not day_master:
            return {"error": "缺少 bazi 或 day_master 参数"}
        try:
            mcp_json = {"八字": bazi, "日主": day_master, "性别": gender}
            result = full_analysis(mcp_json)
            return result
        except Exception as e:
            return {"error": str(e)}

    elif name == "bazi_daily_fortune":
        day_master = arguments.get("day_master", "")
        yongshen = arguments.get("yongshen", "")
        jishen = arguments.get("jishen", [])
        if not day_master:
            return {"error": "缺少 day_master 参数"}
        from datetime import date

        from server.daily_fortune import calc_daily_fortune
        return calc_daily_fortune(day_master, yongshen, jishen, date.today())

    return {"error": f"未知工具: {name}"}


TOOLS = [
    {
        "name": "bazi_paipan",
        "description": "八字排盘 — 输入阳历出生时间和性别，返回四柱八字、日主、生肖、大运等",
        "inputSchema": {
            "type": "object",
            "properties": {
                "solar_datetime": {"type": "string", "description": "阳历出生时间，格式 YYYY-MM-DD HH:MM"},
                "gender": {"type": "string", "enum": ["男", "女"], "description": "性别"},
            },
            "required": ["solar_datetime"],
        },
    },
    {
        "name": "bazi_analyze",
        "description": "八字全面分析 — 输入八字和日主，返回旺衰、格局、用神、十神、五行力量、刑冲合害等",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bazi": {"type": "string", "description": "八字，空格分隔四柱，如 '甲子 丙寅 戊辰 壬子'"},
                "day_master": {"type": "string", "description": "日主天干，如 '戊'"},
                "gender": {"type": "string", "enum": ["男", "女"]},
            },
            "required": ["bazi", "day_master"],
        },
    },
    {
        "name": "bazi_daily_fortune",
        "description": "每日运势 — 基于日主和用神计算今日六维度运势",
        "inputSchema": {
            "type": "object",
            "properties": {
                "day_master": {"type": "string", "description": "日主天干"},
                "yongshen": {"type": "string", "description": "用神五行"},
                "jishen": {"type": "array", "items": {"type": "string"}, "description": "忌神五行列表"},
            },
            "required": ["day_master"],
        },
    },
]


def run_stdio():
    """以 stdio 模式运行 MCP server"""
    server_info = {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "bazi-pro", "version": "5.2.0"},
    }

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = msg.get("method", "")
        msg_id = msg.get("id")

        if method == "initialize":
            response = {"jsonrpc": "2.0", "id": msg_id, "result": server_info}
        elif method == "tools/list":
            response = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            params = msg.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = handle_tool_call(tool_name, arguments)
            response = {
                "jsonrpc": "2.0", "id": msg_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]},
            }
        else:
            response = {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    run_stdio()
