"""
LLM 服务模块 — 支持 OpenAI 兼容 API (OpenAI, DeepSeek, 通义千问, Ollama 等)
"""
import asyncio
import json
import logging
import os
import re

import httpx

from bazi_pro.paipan import DIZHI, TIANGAN

logger = logging.getLogger("bazi-pro.llm")


def _get_year_ganzhi(year: int) -> str:
    """根据公历年份计算年柱干支"""
    gan_idx = (year - 4) % 10
    zhi_idx = (year - 4) % 12
    return TIANGAN[gan_idx] + DIZHI[zhi_idx]


def _get_month_ganzhi(year: int, month: int) -> str:
    """根据公历年月计算月柱干支（使用排盘引擎确保准确）"""
    try:
        from bazi_pro.paipan import paipan_from_datetime
        solar_str = f"{year:04d}-{month:02d}-15 12:00"
        result = paipan_from_datetime(solar_str, "男")
        if result.get("status") == "completed":
            pillars = result.get("pillars", [])
            if pillars and len(pillars) >= 2:
                return pillars[1].get("gan", "") + pillars[1].get("zhi", "")
    except Exception:
        pass
    # 降级：五虎遁简化计算
    year_gan_idx = (year - 4) % 10
    year_gan = TIANGAN[year_gan_idx]
    # 甲己之年丙作首，乙庚之岁戊为头...
    base_map = {"甲": 2, "己": 2, "乙": 4, "庚": 4, "丙": 6, "辛": 6, "丁": 8, "壬": 8, "戊": 0, "癸": 0}
    base_idx = base_map.get(year_gan, 2)
    gan_idx = (base_idx + month - 1) % 10
    zhi_idx = (month + 1) % 12  # 寅月为正月
    return TIANGAN[gan_idx] + DIZHI[zhi_idx]


def _get_day_ganzhi(d) -> str:
    """根据公历日期计算日柱干支（使用排盘引擎确保准确）"""
    try:
        from datetime import date

        from bazi_pro.paipan import paipan_from_datetime
        if isinstance(d, date):
            solar_str = f"{d.year:04d}-{d.month:02d}-{d.day:02d} 12:00"
            result = paipan_from_datetime(solar_str, "男")
            if result.get("status") == "completed":
                pillars = result.get("pillars", [])
                if pillars and len(pillars) >= 3:
                    return pillars[2].get("gan", "") + pillars[2].get("zhi", "")
    except Exception:
        pass
    # 降级：简化计算（1900-01-01 为甲戌日）
    from datetime import date
    base = date(1900, 1, 1)
    if isinstance(d, date):
        delta = (d - base).days
        gan_idx = (delta + 0) % 10  # 甲=0
        zhi_idx = (delta + 10) % 12  # 戌=10
        return TIANGAN[gan_idx] + DIZHI[zhi_idx]
    return ""

_LLM_API_BASE = os.environ.get("LLM_API_BASE", "https://api.openai.com/v1")
_LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
_LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
_LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "300"))


_MAX_TOOL_ROUNDS = 5
"""工具调用最大轮次，防止无限循环"""


def get_llm_config() -> dict:
    return {
        "api_base": _LLM_API_BASE,
        "api_key_set": bool(_LLM_API_KEY),
        "model": _LLM_MODEL,
    }


def update_llm_config(api_key: str | None = None, api_base: str | None = None, model: str | None = None):
    global _LLM_API_KEY, _LLM_API_BASE, _LLM_MODEL
    if api_key is not None:
        if not isinstance(api_key, str) or len(api_key) > 512:
            raise ValueError("api_key 格式不合法")
        _LLM_API_KEY = api_key
    if api_base is not None:
        if not isinstance(api_base, str):
            raise ValueError("api_base 必须为字符串")
        if api_base and not re.match(r'^https?://[\w.\-]+(:\d+)?(/.*)?$', api_base):
            raise ValueError("api_base URL 格式不合法")
        _LLM_API_BASE = api_base
    if model is not None:
        if not isinstance(model, str) or not re.match(r'^[a-zA-Z0-9._\-/]+$', model):
            raise ValueError("model 名称格式不合法")
        _LLM_MODEL = model
    logger.info("[llm] config updated: base=%s model=%s key_set=%s", _LLM_API_BASE, _LLM_MODEL, bool(_LLM_API_KEY))


def is_llm_configured() -> bool:
    return bool(_LLM_API_KEY)


async def chat_completion(messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
    if not _LLM_API_KEY:
        raise RuntimeError("LLM API key 未配置。请设置 LLM_API_KEY 环境变量。")

    url = f"{_LLM_API_BASE.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {_LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    effective_max = max_tokens
    bumped = False
    max_retries = 3
    for attempt in range(max_retries + 1):
        payload = {
            "model": _LLM_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": effective_max,
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(_LLM_TIMEOUT, connect=5.0)) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in (401, 403):
                raise RuntimeError(f"LLM API 认证失败 (HTTP {resp.status_code})，请检查 LLM_API_KEY")
            if resp.status_code == 429:
                wait = min(5 * (attempt + 1), 30)
                logger.warning("[llm] rate limited (429), retry %d/%d after %ds", attempt + 1, max_retries, wait)
                await asyncio.sleep(wait)
                continue
            if resp.status_code >= 500 and attempt < max_retries:
                logger.warning("[llm] server error %d, retry %d/%d", resp.status_code, attempt + 1, max_retries)
                await asyncio.sleep(1 * (attempt + 1))
                continue
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError("LLM 返回空 choices")
            message = choices[0].get("message", {})
            content = message.get("content")
            reasoning = message.get("reasoning_content", "")
            if not content:
                if reasoning:
                    return reasoning
                if not bumped and effective_max < 16384:
                    effective_max = min(effective_max * 4, 16384)
                    bumped = True
                    logger.warning("[llm] content empty (reasoning model), retry with max_tokens=%d", effective_max)
                    continue
                raise RuntimeError("LLM 返回空 content。推理模型 token 不足，请增大 max_tokens。")
            return content
    raise RuntimeError("unreachable")


async def chat_completion_stream(messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096):
    if not _LLM_API_KEY:
        raise RuntimeError("LLM API key 未配置。请设置 LLM_API_KEY 环境变量。")

    url = f"{_LLM_API_BASE.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {_LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    has_content = False
    async with httpx.AsyncClient(timeout=httpx.Timeout(_LLM_TIMEOUT, connect=5.0)) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta") or {}
                    content = delta.get("content") or delta.get("reasoning_content") or ""
                    if content:
                        has_content = True
                        yield content
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue
    if not has_content:
        raise RuntimeError("LLM 流式返回无 content。推理模型 token 不足，请增大 max_tokens。")


async def chat_completion_stream_typed(messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096):
    """流式 LLM 调用，区分 reasoning_content 和 content，逐块 yield {"type": ..., "content": ...} 字典。

    type 取值：
    - "reasoning" — 推理/思考过程（reasoning_content）
    - "token"     — 正文内容（content）
    """
    if not _LLM_API_KEY:
        raise RuntimeError("LLM API key 未配置。请设置 LLM_API_KEY 环境变量。")

    url = f"{_LLM_API_BASE.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {_LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    has_content = False
    reasoning_buffer = ""
    async with httpx.AsyncClient(timeout=httpx.Timeout(_LLM_TIMEOUT, connect=5.0)) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta") or {}
                    reasoning = delta.get("reasoning_content") or ""
                    content = delta.get("content") or ""
                    if reasoning:
                        has_content = True
                        reasoning_buffer += reasoning
                        yield {"type": "reasoning", "content": reasoning}
                    if content:
                        has_content = True
                        yield {"type": "token", "content": content}
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue
    # 推理模型降级：只有 reasoning_content 没有 content 时，将 reasoning 作为 token 输出
    if has_content and reasoning_buffer:
        yield {"type": "token", "content": reasoning_buffer}
    if not has_content:
        raise RuntimeError("LLM 流式返回无 content。推理模型 token 不足，请增大 max_tokens。")


# ============ Function Calling 支持 ============


async def chat_completion_with_tools(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    max_tool_rounds: int = _MAX_TOOL_ROUNDS,
) -> dict:
    """支持 function calling 的 LLM 调用。

    自动处理工具调用循环：
    1. 发送带 tools 的请求给 LLM
    2. 若 LLM 返回 tool_calls，执行工具并将结果注入消息
    3. 重复直到 LLM 返回纯文本或达到最大轮次

    Args:
        messages: 消息列表
        tools: OpenAI function calling 工具定义列表
        temperature: 温度
        max_tokens: 最大 token 数
        max_tool_rounds: 最大工具调用轮次

    Returns:
        dict: {
            "content": str,           # LLM 最终文本回复
            "tool_calls_log": list,   # 工具调用日志（含输入输出，可追溯）
            "messages": list,         # 完整的消息历史（含工具调用和结果）
        }
    """
    if not _LLM_API_KEY:
        raise RuntimeError("LLM API key 未配置。请设置 LLM_API_KEY 环境变量。")

    from server.agents.tools import execute_tools

    url = f"{_LLM_API_BASE.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {_LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    working_messages = list(messages)
    tool_calls_log: list[dict] = []

    for round_idx in range(max_tool_rounds):
        payload: dict = {
            "model": _LLM_MODEL,
            "messages": working_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=httpx.Timeout(_LLM_TIMEOUT, connect=5.0)) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in (401, 403):
                raise RuntimeError(f"LLM API 认证失败 (HTTP {resp.status_code})，请检查 LLM_API_KEY")
            resp.raise_for_status()
            data = resp.json()

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("LLM 返回空 choices")

        message = choices[0].get("message", {})
        content = message.get("content") or ""
        tool_calls = message.get("tool_calls") or []

        # 无工具调用 → 返回最终结果
        if not tool_calls:
            # 推理模型可能 content 为空但有 reasoning_content
            if not content:
                reasoning = message.get("reasoning_content", "")
                if reasoning:
                    content = reasoning

            return {
                "content": content,
                "tool_calls_log": tool_calls_log,
                "messages": working_messages,
            }

        # 有工具调用 → 将 assistant 消息（含 tool_calls）加入历史
        assistant_msg: dict = {"role": "assistant", "content": content or ""}
        assistant_msg["tool_calls"] = tool_calls
        working_messages.append(assistant_msg)

        # 记录工具调用日志
        for tc in tool_calls:
            func = tc.get("function", {})
            tool_calls_log.append({
                "id": tc.get("id", ""),
                "name": func.get("name", ""),
                "arguments": func.get("arguments", ""),
                "round": round_idx + 1,
            })

        # 执行工具并注入结果
        tool_messages = await execute_tools(tool_calls)
        working_messages.extend(tool_messages)

        # 记录工具结果到日志
        for tm in tool_messages:
            for log_entry in tool_calls_log:
                if log_entry["id"] == tm.get("tool_call_id"):
                    log_entry["result"] = tm.get("content", "")
                    break

    # 达到最大轮次 → 强制返回
    logger.warning("[llm] 达到最大工具调用轮次 %d，强制返回", max_tool_rounds)
    return {
        "content": content or "（工具调用轮次已达上限）",
        "tool_calls_log": tool_calls_log,
        "messages": working_messages,
    }


async def chat_completion_stream_with_tools(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    max_tool_rounds: int = _MAX_TOOL_ROUNDS,
):
    """支持 function calling 的流式 LLM 调用。

    工具调用期间为非流式（等待工具执行完成），最终回复为流式输出。

    Yields:
        dict: {"type": "token"|"reasoning"|"tool_call"|"tool_result"|"done", "content": ...}
    """
    if not _LLM_API_KEY:
        raise RuntimeError("LLM API key 未配置。请设置 LLM_API_KEY 环境变量。")

    from server.agents.tools import execute_tools

    url = f"{_LLM_API_BASE.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {_LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    working_messages = list(messages)
    tool_calls_log: list[dict] = []

    for round_idx in range(max_tool_rounds):
        # 非流式请求（工具调用必须同步处理）
        yield {"type": "heartbeat", "content": f"正在调用 LLM（第{round_idx + 1}轮）..."}
        payload: dict = {
            "model": _LLM_MODEL,
            "messages": working_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=httpx.Timeout(_LLM_TIMEOUT, connect=5.0)) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in (401, 403):
                raise RuntimeError(f"LLM API 认证失败 (HTTP {resp.status_code})，请检查 LLM_API_KEY")
            resp.raise_for_status()
            data = resp.json()

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("LLM 返回空 choices")

        message = choices[0].get("message", {})
        content = message.get("content") or ""
        tool_calls = message.get("tool_calls") or []

        # 无工具调用 → 流式输出最终回复
        if not tool_calls:
            if not content:
                reasoning = message.get("reasoning_content", "")
                if reasoning:
                    content = reasoning
            if content:
                # 将最终回复分块流式输出
                chunk_size = 20
                for i in range(0, len(content), chunk_size):
                    yield {"type": "token", "content": content[i:i + chunk_size]}
            yield {"type": "done", "content": ""}
            return

        # 有工具调用 → 通知前端正在调用工具
        assistant_msg: dict = {"role": "assistant", "content": content or ""}
        assistant_msg["tool_calls"] = tool_calls
        working_messages.append(assistant_msg)

        for tc in tool_calls:
            func = tc.get("function", {})
            tool_name = func.get("name", "")
            tool_calls_log.append({
                "id": tc.get("id", ""),
                "name": tool_name,
                "arguments": func.get("arguments", ""),
                "round": round_idx + 1,
            })
            yield {"type": "tool_call", "content": json.dumps({
                "name": tool_name,
                "arguments": func.get("arguments", ""),
            }, ensure_ascii=False)}

        # 执行工具（发送心跳防止前端 stall timer 触发）
        yield {"type": "heartbeat", "content": "正在执行命理工具..."}
        tool_messages = await execute_tools(tool_calls)
        working_messages.extend(tool_messages)

        # 通知前端工具结果
        for tm in tool_messages:
            yield {"type": "tool_result", "content": tm.get("content", "")}

    # 达到最大轮次
    logger.warning("[llm] 达到最大工具调用轮次 %d，强制返回", max_tool_rounds)
    yield {"type": "token", "content": "（工具调用轮次已达上限）"}
    yield {"type": "done", "content": ""}


def _format_analysis_context(analysis_result: dict, narration: dict, school: str = "ziping") -> str:
    """格式化命盘数据为文本上下文，支持不同派别视角"""
    if not isinstance(analysis_result, dict):
        analysis_result = {}
    if not isinstance(narration, dict):
        narration = {}

    validation = analysis_result.get("validation", {}) if isinstance(analysis_result.get("validation"), dict) else {}
    strength = analysis_result.get("strength", {}) if isinstance(analysis_result.get("strength"), dict) else {}
    if not strength and "wangshuai" in analysis_result:
        strength = {"wangshuai": analysis_result["wangshuai"]}
    pattern_info = analysis_result.get("pattern", {}) if isinstance(analysis_result.get("pattern"), dict) else {}
    yongshen_info = analysis_result.get("yongshen", {}) if isinstance(analysis_result.get("yongshen"), dict) else {}
    elements = analysis_result.get("elements", {}) if isinstance(analysis_result.get("elements"), dict) else {}
    if not elements:
        elements = analysis_result.get("element_forces", {}) if isinstance(analysis_result.get("element_forces"), dict) else {}
    relations = analysis_result.get("relations", []) if isinstance(analysis_result.get("relations"), list) else []
    tiaohou = analysis_result.get("tiaohou", {}) if isinstance(analysis_result.get("tiaohou"), dict) else {}
    shishen = analysis_result.get("shishen", {}) if isinstance(analysis_result.get("shishen"), dict) else {}
    shensha = analysis_result.get("shensha", {}) if isinstance(analysis_result.get("shensha"), dict) else {}
    gongwei = analysis_result.get("gongwei", {}) if isinstance(analysis_result.get("gongwei"), dict) else {}

    day_master = validation.get("day_master", "") or analysis_result.get("day_master", "")
    bazi = validation.get("bazi", "")
    if not bazi:
        # full_analysis() 返回 pillars 列表，需重构八字字符串
        pillars_raw = analysis_result.get("pillars", []) or (shishen.get("pillars", []) if isinstance(shishen, dict) else [])
        if pillars_raw:
            bazi = " ".join(p.get("gan", "") + p.get("zhi", "") for p in pillars_raw if isinstance(p, dict) and p.get("gan") and p.get("zhi"))
    gender = validation.get("gender", "") or analysis_result.get("gender", "")

    ws = strength.get("wangshuai", {}) if isinstance(strength, dict) else {}
    pattern = pattern_info.get("pattern", "") if isinstance(pattern_info, dict) else ""
    yongshen = yongshen_info.get("yongshen", "") if isinstance(yongshen_info, dict) else ""
    xishen = yongshen_info.get("xishen", []) if isinstance(yongshen_info, dict) else []
    jishen = yongshen_info.get("jishen", []) if isinstance(yongshen_info, dict) else []

    pillars_info = ""
    for p in (shishen.get("pillars", []) if isinstance(shishen, dict) else []):
        if not isinstance(p, dict):
            continue
        pos = p.get("position", "")
        gan = p.get("gan", "")
        zhi = p.get("zhi", "")
        ss_gan = p.get("shishen_gan", "")
        ss_zhi = p.get("shishen_zhi", "")
        canggan = p.get("canggan", []) if isinstance(p.get("canggan"), list) else []
        cg_str = " ".join(f"{c.get('gan','')}({c.get('shishen','')})" for c in canggan if isinstance(c, dict))
        pillars_info += f"  {pos}: {gan}{zhi} 天干十神={ss_gan} 地支十神={ss_zhi} 藏干={cg_str}\n"

    relations_str = ""
    for r in relations:
        if isinstance(r, dict):
            relations_str += f"  {r.get('type','')}: {r.get('description','')}\n"

    percent = elements.get("percent", {}) if isinstance(elements, dict) else {}
    try:
        elements_str = " ".join(f"{k}:{v:.1f}%" for k, v in sorted(percent.items(), key=lambda x: -x[1]))
    except Exception:
        elements_str = ""

    # 神煞信息
    shensha_str = ""
    if shensha and isinstance(shensha, dict):
        for category, items in shensha.items():
            if items:
                if isinstance(items, list):
                    shensha_str += f"  {category}: {', '.join(str(i) for i in items)}\n"
                elif isinstance(items, dict):
                    shensha_str += f"  {category}: {items}\n"

    # 宫位信息
    gongwei_str = ""
    if gongwei and isinstance(gongwei, dict):
        for key, val in gongwei.items():
            gongwei_str += f"  {key}: {val}\n"

    # 派别特定数据
    school_analyses = analysis_result.get("school_analyses", {}) if isinstance(analysis_result.get("school_analyses"), dict) else {}
    school_data = school_analyses.get(school, {}) if isinstance(school_analyses, dict) else {}
    school_str = ""
    if school_data and isinstance(school_data, dict):
        try:
            school_json = json.dumps(school_data, ensure_ascii=False, indent=2)
            # 将JSON中的 { 和 } 替换为安全字符，避免f-string解析问题
            school_str = "\n## " + school + "派分析数据\n" + school_json + "\n"
        except Exception:
            school_str = ""

    # 安全获取嵌套值
    deling_status = ""
    deling_score = 0
    if isinstance(strength, dict):
        deling = strength.get("deling", {})
        if isinstance(deling, dict):
            deling_status = deling.get("status", "")
            deling_score = deling.get("score", 0)

    dedi_score = 0
    deshi_score = 0
    if isinstance(strength, dict):
        dedi = strength.get("dedi", {})
        deshi = strength.get("deshi", {})
        if isinstance(dedi, dict):
            dedi_score = dedi.get("score", 0)
        if isinstance(deshi, dict):
            deshi_score = deshi.get("score", 0)

    ws_verdict = ""
    if isinstance(ws, dict):
        ws_verdict = ws.get("verdict", "")

    pattern_layer = "?"
    pattern_confidence = 0
    pattern_reason = ""
    if isinstance(pattern_info, dict):
        pattern_layer = pattern_info.get("layer", "?")
        pattern_confidence = pattern_info.get("confidence", 0)
        pattern_reason = pattern_info.get("reason", "")

    tiaohou_gan = []
    tiaohou_wx = []
    if isinstance(tiaohou, dict):
        tiaohou_gan = tiaohou.get("tiaohou_gan", []) if isinstance(tiaohou.get("tiaohou_gan"), list) else []
        tiaohou_wx = tiaohou.get("tiaohou_wx", []) if isinstance(tiaohou.get("tiaohou_wx"), list) else []

    xishen_str = "、".join(str(x) for x in xishen) if isinstance(xishen, list) else ""
    jishen_str = "、".join(str(j) for j in jishen) if isinstance(jishen, list) else ""

    shengxiao = validation.get("生肖", "") if isinstance(validation, dict) else ""

    # 出生年份与年龄计算
    birth_year = analysis_result.get("birth_year", 0)
    from datetime import datetime
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    current_day = now.day
    current_hour = now.hour
    current_minute = now.minute
    current_age = current_year - birth_year if birth_year else 0
    current_liunian_gan_zhi = _get_year_ganzhi(current_year)
    current_liuyue_gan_zhi = _get_month_ganzhi(current_year, current_month)
    current_liuri_gan_zhi = _get_day_ganzhi(now.date())

    # 大运数据
    dayun_list = analysis_result.get("dayun", []) if isinstance(analysis_result.get("dayun"), list) else []
    qiyun_age = analysis_result.get("qiyun_age", 0)
    dayun_str = ""
    current_dayun = ""
    for dy in dayun_list:
        if isinstance(dy, dict):
            age_range = dy.get("age_range", "")
            gan_zhi = dy.get("gan_zhi", "")
            dayun_str += f"  {age_range}: {gan_zhi}\n"
            # 判断当前正在走的大运
            if age_range and "-" in age_range:
                try:
                    start, end = age_range.split("-")
                    start_age = int(start.strip())
                    end_age = int(end.strip())
                    if start_age <= current_age <= end_age:
                        current_dayun = gan_zhi
                except (ValueError, TypeError):
                    pass

    narration_str = ""
    try:
        narration_str = json.dumps(narration, ensure_ascii=False, indent=2)
    except Exception:
        narration_str = "{}"

    # 使用字符串拼接而非f-string，避免JSON中的{和}被解析为格式占位符
    parts = [
        "## 命盘数据",
        f"- 八字: {bazi}",
        f"- 日主: {day_master}（{gender}命）",
        f"- 生肖: {shengxiao}",
        f"- 出生年份: {birth_year}年" if birth_year else "",
        f"- 当前时间: {current_year}年{current_month}月{current_day}日 {current_hour:02d}:{current_minute:02d}",
        f"- 当前流年: {current_liunian_gan_zhi}（{current_year}年）",
        f"- 当前流月: {current_liuyue_gan_zhi}（{current_month}月）",
        f"- 当前流日: {current_liuri_gan_zhi}（{current_month}月{current_day}日）",
        f"- 当前年龄: {current_age}岁" if birth_year else "",
        f"- 起运年龄: {qiyun_age}岁" if qiyun_age else "",
        f"- 当前大运: {current_dayun}" if current_dayun else "",
        "",
        "## 四柱详情",
        pillars_info,
        "",
        "## 旺衰判定",
        f"- 得令: {deling_status} (分数: {deling_score})",
        f"- 得地分数: {dedi_score}",
        f"- 得势分数: {deshi_score}",
        f"- 综合判定: {ws_verdict}",
        "",
        "## 格局",
        f"- 格局: {pattern} (第{pattern_layer}层, 置信度: {pattern_confidence:.0%})",
        f"- 判定理由: {pattern_reason}",
        "",
        "## 喜用神",
        f"- 用神: {yongshen}",
        f"- 喜神: {xishen_str}",
        f"- 忌神: {jishen_str}",
        "",
        "## 调候",
        f"- 调候用神: {'、'.join(str(t) for t in tiaohou_gan)} ({'、'.join(str(t) for t in tiaohou_wx)})",
        "",
        "## 五行力量",
        elements_str,
        "",
        "## 刑冲合害",
        relations_str if relations_str else "无",
        "",
        "## 神煞",
        shensha_str if shensha_str else "无",
        "",
        "## 宫位",
        gongwei_str if gongwei_str else "无",
        "",
        "## 大运列表",
        dayun_str if dayun_str else "未提供大运数据",
        "",
        "## 确定性叙述",
        narration_str,
    ]

    # 紫微斗数数据
    ziwei = analysis_result.get("ziwei", {}) if isinstance(analysis_result.get("ziwei"), dict) else {}
    if ziwei:
        ziwei_parts = []
        # 命盘基本信息
        soul = ziwei.get("soul", "")
        body = ziwei.get("body", "")
        five_class = ziwei.get("fiveElementsClass", "")
        if soul or body or five_class:
            ziwei_parts.append(f"- 命主: {soul}, 身主: {body}, 五行局: {five_class}")

        # 宫位主星
        palaces = ziwei.get("palaces", []) if isinstance(ziwei.get("palaces"), list) else []
        if palaces:
            palace_lines = []
            for p in palaces:
                if not isinstance(p, dict):
                    continue
                name = p.get("name", "")
                stars = [s.get("name", "") for s in p.get("majorStars", []) if isinstance(s, dict) and s.get("name")]
                brightness = [s.get("brightness", "") for s in p.get("majorStars", []) if isinstance(s, dict) and s.get("brightness")]
                if stars:
                    star_str = "、".join(stars)
                    bright_str = "、".join(brightness) if brightness else ""
                    palace_lines.append(f"  {name}: {star_str} ({bright_str})" if bright_str else f"  {name}: {star_str}")
            if palace_lines:
                ziwei_parts.append("- 宫位主星:\n" + "\n".join(palace_lines))

        # 四化信息
        sihua = ziwei.get("sihua", {}) if isinstance(ziwei.get("sihua"), dict) else {}
        if sihua:
            sihua_lines = []
            for key, val in sihua.items():
                if val:
                    sihua_lines.append(f"  {key}: {val}")
            if sihua_lines:
                ziwei_parts.append("- 四化:\n" + "\n".join(sihua_lines))

        # 格局
        ziwei_patterns = ziwei.get("patterns", []) if isinstance(ziwei.get("patterns"), list) else []
        if ziwei_patterns:
            pattern_lines = [f"  - {p}" for p in ziwei_patterns if isinstance(p, str)]
            if pattern_lines:
                ziwei_parts.append("- 紫微格局:\n" + "\n".join(pattern_lines))

        # 大限
        dayun_ziwei = ziwei.get("dayun", []) if isinstance(ziwei.get("dayun"), list) else []
        if dayun_ziwei:
            dayun_lines = []
            for d in dayun_ziwei[:8]:
                if isinstance(d, dict):
                    age = d.get("age_range", "")
                    palace = d.get("palace", "")
                    stars = d.get("stars", "")
                    dayun_lines.append(f"  {age}: {palace} {stars}")
            if dayun_lines:
                ziwei_parts.append("- 大限:\n" + "\n".join(dayun_lines))

        if ziwei_parts:
            parts.append("")
            parts.append("## 紫微斗数命盘")
            parts.extend(ziwei_parts)

    if school_str:
        parts.append(school_str)
    # 过滤空字符串
    return "\n".join(p for p in parts if p is not None and p != "")


# ============ 派别视角定义 ============

SCHOOL_PERSPECTIVES = {
    "ziping": {
        "name": "传统子平法",
        "core_concepts": ["格局", "用神", "旺衰", "月令", "透干", "通根"],
        "classics": ["《子平真诠》", "《渊海子平》", "《滴天髓》", "《神峰通考》"],
        "methodology": """
以月令取格，看格局成败；以旺衰定用忌，看扶抑得失。
- 格局法：月令透干为格，无格看局，格局清纯为贵
- 旺衰法：得令得地得势，身强身弱定用神方向
- 调候法：寒暖燥湿，调候为先
- 病药法：有病方为贵，无伤不是奇""",
    },
    "mangpai": {
        "name": "盲派",
        "core_concepts": ["宾主", "体用", "做功", "功神", "废神", "贼神捕神", "象法"],
        "classics": ["《盲派初级命理学》", "《命理珍宝》", "《命理瑰宝》"],
        "methodology": """
以宾主体用分定位，以做功论富贵贫贱。
- 宾主：日主为主，他干支为宾；日柱为主，年月时为宾
- 体用：日主、比劫、印禄为体；财官食伤为用
- 做功：制用、化用、生用、合用、墓用、穿用、刑用
- 贼神捕神：寻贼捕贼，制化得宜
- 五党成势：党多势众，顺其气势""",
    },
    "xinpai": {
        "name": "新派",
        "core_concepts": ["百神论", "空亡论", "反断论", "格局分类", "从强从弱", "扶抑"],
        "classics": ["《八字预测真踪》"],
        "methodology": """
以格局分类定大方向，以百神论看六亲，以空亡论看应期。
- 格局分类：扶抑格、从强格、从弱格、化气格
- 百神论：无某六亲时，以其他十神替代看六亲
- 空亡论：空亡支在流年大运出空时发生作用
- 反断论：同宗对反断，旺极反弱、弱极反旺
- 虚实论：天干为虚，地支为实""",
    },
}


def _get_school_context(school: str) -> str:
    """获取派别视角上下文"""
    school_info = SCHOOL_PERSPECTIVES.get(school, SCHOOL_PERSPECTIVES["ziping"])
    return f"""
【当前分析视角：{school_info['name']}】

核心概念：{', '.join(school_info['core_concepts'])}

参考典籍：{', '.join(school_info['classics'])}

方法论：{school_info['methodology']}
"""


def _get_anti_hallucination_rules() -> str:
    """获取防幻觉规则"""
    return """
【强制性防幻觉规则 - 违者必究】

1. **数据来源限制**：你只能基于以下确定性计算数据进行论述，不得编造不存在的干支、十神、神煞或流年事件
   - 允许的：已提供的八字、十神、格局、旺衰、用神、神煞、刑冲合害、大运流年
   - 禁止的：未提及的干支组合、虚构的流年事件、臆测的六亲情况

2. **古籍引用规范**：
   - 引用时必须注明具体典籍名称（如《滴天髓》）
   - 必须引用原文或准确概括，不得杜撰
   - 优先引用：{classics}

3. **论断边界**：
   - 只能说"根据命盘显示..."、"从格局来看..."
   - 不能说"你肯定会..."、"一定会在某年..."
   - 时间预测必须有干支依据，如"丙午年（2026）"而非模糊的"明年"

4. **不确定性表达**：
   - 对于无法确定的事项，明确说明"命盘未显示明确信息"
   - 对于多种可能，列出条件分支"若...则...；若...则..."

5. **禁止内容**：
   - 禁止虚构具体的流年事件（如"2025年会升职"）
   - 禁止臆测未提及的六亲关系（如"你父亲..."）
   - 禁止给出绝对化的命运判断
"""


# ============ 新增：大师断命节奏模板 ============

def _get_master_rhythm_template() -> str:
    """返回四步断命节奏模板"""
    return """
【大师断命四步节奏 - 必须遵循】

第一步：观大局
- 用3-5句话概括命局核心特征
- 包含：格局定性、旺衰判定、用神方向
- 语气沉稳，如"观此命局，日主XX生于XX月，得令/失令，格局属XX..."

第二步：论细节
- 引用具体典籍原文或准确概括
- 分析具体干支关系：天干合化、地支刑冲、藏干作用
- 结合十神定位：财官印食伤在具体柱位的表现
- 例：「《子平真诠·论用神》：用神专求月令」——观你月令XX，透干XX...

第三步：断应期
- 给出具体干支年份（如丙午年2026、丁未年2027）
- 每断一年必须说明：该年干支与日主的关系、与用神的关系、与大运的关系
- 用[吉]/[凶]/[平]明确标记每一年
- 对[吉]年，找出相关的十神（如财星、官星）

第四步：给建议
- 基于用神喜忌给出可执行建议
- 包括：有利方位、颜色、行业、贵人属相
- 对[凶]年给出化解方向，对[吉]年给出把握建议
- 建议必须具体，避免"多努力"等空话
"""


def _get_master_opening_templates(pattern_type: str) -> str:
    """根据格局类型返回5个大师开场模板"""
    templates = {
        "专旺格": """
1. 观此命局，五行一气成象，日主得时得地，气势专聚一方。老夫四十年阅命无数，此等格局颇为罕见。
2. 此命格局清纯，一行专旺，如长江大河一泻千里。喜顺其气势，不可逆其性。
3. 专旺之格，贵在纯粹。观你八字，比劫印绶成局，日主强旺无制，当以泄秀生财为妙。
""",
        "从格": """
1. 此命日主孤立无援，满盘皆是克泄耗之力。老夫细看，此乃从格之象，宜顺不宜逆。
2. 从者，顺其旺神也。观你命局，财官食伤成势，日主弱极而从，当以从论。
3. 从格之命，如顺水行舟。只要大运流年不逢根气，反能因势利导，成就一番事业。
""",
        "正格": """
1. 观此命局，日主中和，五行流通有情。格局清正，用神可得，乃寻常中之贵格也。
2. 此命月令当令，透干有根，格局成败皆在用神取舍之间。老夫为你细细道来。
3. 正格之命，重在平衡。观你八字，旺衰分明，用神有力，只要大运配合，必有所成。
""",
        "建禄格": """
1. 此命日主得禄于月令，建禄生提月，财官喜透天。老夫观你八字，禄神当令，身旺无疑。
2. 建禄之格，身旺任财官。观你命局，比劫帮身太过，宜取财官为用以成格局。
3. 月令建禄，日主根深蒂固。此等命局，最喜财官食伤来调和，方为贵气。
""",
        "化气格": """
1. 观此命局，天干合化有情，化神当令得时。此乃化气之格，变化莫测，贵在看化神之旺衰。
2. 化气之格，如蛹化蝶。观你八字，甲己合化土，生于季月，化神得助，化象成真。
3. 此命合化成功，日主变性。老夫四十年经验，化气格贵在纯粹，忌争合妒合破格。
""",
    }
    return templates.get(pattern_type, templates["正格"])


def _get_transition_phrases() -> str:
    """返回大师级转折用语"""
    return """
【大师转折用语库 - 适时穿插使用】

- 然而，细究之...
- 值得注意的是...
- 老夫再看...
- 换言之...
- 细究之...
- 不过...
- 反观之...
- 进一步说...
- 从另一个角度看...
- 老夫再提醒你一点...
- 话虽如此...
- 但有一条不可忽视...
- 若论及...
- 说到此处...
- 顺带一提...
"""


def _get_assertion_patterns() -> str:
    """返回大师论断句式模板"""
    return """
【大师论断句式 - 每段开头可选用】

- 此命...
- 观你八字...
- 以老夫四十年经验...
- 格局所示...
- 从命盘来看...
- 依老夫之见...
- 命理而言...
- 细观干支...
- 以典籍所载...
- 从五行配置观之...
- 据大运流年推算...
- 以用神喜忌论之...
"""


# ============ 新增：流年预测严格推理链 ============

def _get_time_prediction_chain() -> str:
    """返回流年预测的严格推理链模板"""
    return """
【流年预测严格推理链 - 必须执行】

1. **列出未来10年流年干支**
   - 从当前年份开始，逐年列出：干支 + 公历年份
   - 格式：「丙午年（2026）」、「丁未年（2027）」...

2. **逐年分析**
   对每一年，必须分析以下三点：
   a) 该年天干与日主的关系（生/克/比/泄/耗）
   b) 该年地支与日主的关系（合/冲/刑/害/会/根气）
   c) 该年与用神的关系（助用神/伤用神/无关）
   d) 该年与当前大运的关系（大运干支与流年干支的互动）

3. **吉凶标记**
   - 每分析完一年，必须用以下标签明确标记：
     - [吉]：流年助用神、合日主、解原局之病
     - [凶]：流年伤用神、冲克日主、引发刑冲
     - [平]：流年对命局无明显损益

4. **十神关联（仅对[吉]年）**
   - 对标记为[吉]的年份，找出该年对应的十神
   - 说明该十神代表的事项（财/官/印/食伤/比劫）
   - 给出具体建议："此年财星透干，宜把握求财机会"

5. **最吉/最凶年份判定**
   - 从10年中选出最可能应事的年份
   - 必须给出干支和公历年份
   - 必须说明判定依据（如：该年天干为用神、地支合入夫妻宫等）
   - 格式："以老夫推断，最吉之年为XX年（20XX），因..."

6. **禁忌**
   - 禁止只说"某年不错"而不给干支
   - 禁止只说"未来几年"而不列具体年份
   - 每一年必须有独立的分析段落
"""


# ============ 新增：增强版防幻觉规则 ============

def _get_anti_hallucination_v2() -> str:
    """返回增强版防幻觉规则"""
    return """
【增强版防幻觉规则 v2 - 违者必究】

1. **禁用绝对化词汇**
   - 严禁使用："肯定会"、"一定会"、"绝对"、"毫无疑问"
   - 替换为："从命盘来看"、"格局显示"、"以老夫推断"

2. **强制引用标记**
   - 每段分析至少使用一次："从命盘来看"、"格局显示"、"《XX》有云"
   - 古籍引用必须具体到书名和章节，如「《滴天髓·体象论》：...」
   - 禁止只写书名不写章节

3. **数据追溯要求**
   - 每一句话必须能追溯到：命盘具体干支 / 确定性计算数据 / 古籍原文
   - 禁止出现无法追溯的模糊表述，如"总体运势不错"
   - 所有论断必须有"因为...所以..."的逻辑链

4. **时间预测双标注**
   - 所有时间预测必须同时给出：干支年份 + 公历年份
   - 正确示例："丙午年（2026）"
   - 错误示例："明年"、"2026年"、"丙午年"

5. **古籍引用精确性**
   - 必须注明：书名 + 章节/篇名
   - 正确示例：「《子平真诠·论用神》：用神专求月令」
   - 错误示例：「《子平真诠》说...」（缺少章节）
   - 若不确定章节，用「《滴天髓》原文有云：...」并确保内容准确

6. **禁止臆测**
   - 禁止虚构：具体事件（升职、结婚日期）、未提及的六亲关系、未计算的流年吉凶
   - 对不确定事项，必须使用："命盘此处信息不足"、"需结合大运再看"

7. **十神定位**
   - 提及十神时必须标注所在柱位，如"年干正官"、"月令偏财"
   - 禁止笼统说"你命中有官星"而不指明位置
"""


# ============ 新增：检索结果格式化 ============

def _format_retrieval_results(retrieval_results: dict | list | str | None) -> str:
    """将检索结果格式化为提示词文本"""
    if not retrieval_results:
        return ""

    if isinstance(retrieval_results, str):
        return f"\n## 古籍检索结果\n{retrieval_results}\n"

    if isinstance(retrieval_results, list):
        lines = ["\n## 古籍检索结果"]
        for idx, item in enumerate(retrieval_results, 1):
            if isinstance(item, dict):
                source = item.get("source", "")
                text = item.get("text", "")
                score = item.get("score", "")
                lines.append(f"{idx}. [{source}] {text}" + (f" (相关度: {score:.2f})" if isinstance(score, (int, float)) else ""))
            else:
                lines.append(f"{idx}. {item}")
        lines.append("")
        return "\n".join(lines)

    if isinstance(retrieval_results, dict):
        # Chat 场景：顶层有 "results" list（来自 retrieve_for_chat）
        if "results" in retrieval_results and isinstance(retrieval_results.get("results"), list):
            lines = ["\n## 古籍检索结果"]
            for idx, item in enumerate(retrieval_results["results"][:5], 1):
                if isinstance(item, dict):
                    source = item.get("source", "")
                    content = item.get("content") or ""
                    topic = item.get("topic", "")
                    label = f"{source}@{topic}" if topic else source
                    lines.append(f"  {idx}. [{label}] {content[:200]}")
                else:
                    lines.append(f"  {idx}. {item}")
            lines.append("")
            return "\n".join(lines)

        # Report 场景：chapter_key -> retrieval_result 映射
        lines = ["\n## 古籍检索结果"]
        for chapter_key, results in retrieval_results.items():
            lines.append(f"\n### {chapter_key}")
            # results 可能是 retrieve_for_report 返回的完整结构（含 results/counter_evidence），
            # 也可能是简单的 list
            items = results
            if isinstance(results, dict) and "results" in results:
                items = results.get("results", [])
            if isinstance(items, list):
                for idx, item in enumerate(items, 1):
                    if isinstance(item, dict):
                        source = item.get("source", "")
                        content = item.get("content") or ""
                        topic = item.get("topic", "")
                        label = f"{source}@{topic}" if topic else source
                        lines.append(f"  {idx}. [{label}] {content[:200]}")
                    else:
                        lines.append(f"  {idx}. {item}")
            else:
                lines.append(f"  {results}")
        lines.append("")
        return "\n".join(lines)

    return ""


# ============ 修改后的系统提示词构建函数 ============

def build_chat_system_prompt(analysis_result: dict, narration: dict, school: str = "ziping", retrieval_results: dict | list | str | None = None) -> str:
    """
    构建命理问答系统提示词 - 大师口吻 + 古籍引用 + 防幻觉
    新增：支持检索结果注入、大师节奏模板、流年推理链、增强防幻觉
    """
    ctx = _format_analysis_context(analysis_result, narration, school)
    school_ctx = _get_school_context(school)
    anti_hallucination = _get_anti_hallucination_rules().format(
        classics="、".join(SCHOOL_PERSPECTIVES.get(school, SCHOOL_PERSPECTIVES["ziping"])["classics"])
    )
    anti_hallucination_v2 = _get_anti_hallucination_v2()
    rhythm = _get_master_rhythm_template()
    time_chain = _get_time_prediction_chain()
    transitions = _get_transition_phrases()
    assertions = _get_assertion_patterns()
    retrieval_ctx = _format_retrieval_results(retrieval_results)

    # 安全获取日主，避免f-string嵌套问题
    day_master = ""
    if isinstance(analysis_result, dict):
        validation = analysis_result.get("validation", {})
        if isinstance(validation, dict):
            day_master = validation.get("day_master", "") or ""
        if not day_master:
            day_master = analysis_result.get("day_master", "")

    # 获取格局类型用于开场模板
    pattern_type = "正格"
    if isinstance(analysis_result, dict):
        pattern_info = analysis_result.get("pattern", {})
        if isinstance(pattern_info, dict):
            raw_pattern = pattern_info.get("pattern", "")
            if "专旺" in raw_pattern:
                pattern_type = "专旺格"
            elif "从" in raw_pattern:
                pattern_type = "从格"
            elif "建禄" in raw_pattern or "月劫" in raw_pattern:
                pattern_type = "建禄格"
            elif "化" in raw_pattern:
                pattern_type = "化气格"
    opening_templates = _get_master_opening_templates(pattern_type)

    return f"""你是一位精通中国传统命理学的资深命理师，从业四十余年，深谙子平八字、穷通宝鉴、滴天髓等典籍。你说话沉稳有力，不急不躁，每句话都经过深思熟虑。

你的语言风格：
- 像一位真正的算命大师，用第一人称"老夫"或"我"与命主对话
- 语气从容、笃定，带有长者的智慧和温度
- 善用古籍原文支撑论断，如"《滴天髓》有云：..."
- 不说套话空话，每句都紧扣命盘具体干支
- 对命主的问题，先沉思片刻，再给出精准回答

{school_ctx}

{ctx}

{retrieval_ctx}

{rhythm}

{time_chain}

{transitions}

{assertions}

{anti_hallucination}

{anti_hallucination_v2}

---

【开场模板库（根据格局类型选用）】
{opening_templates}

【对话要求】

1. **开场白**：首次对话时，从上述开场模板中选用或改编，简要概括命局核心特征（3-5句话），让命主感受到你的专业

2. **回答风格**：
   - 遵循"观大局→论细节→断应期→给建议"四步节奏
   - 先引古籍或命理原理
   - 再结合命盘具体干支分析
   - 最后给出针对性建议
   - 例："《滴天髓》云：'何知其人富，财气通门户。'观你命盘，日主{day_master}生于..."
   - 适时使用转折用语库中的短语，使行文有起伏

3. **时间预测规范**：
   - 必须遵循"流年预测严格推理链"
   - 列出未来10年流年干支，逐年分析
   - 每断一年必须说明：该年干支与日主的关系、与用神的关系、与大运的关系
   - 用[吉]/[凶]/[平]明确标记每一年
   - 在[吉]年中找出相关十神并给出建议
   - 给出最可能应事的年份及依据
   - 必须给出具体干支年份，如'丙午年（2026）'、'丁未年（2027）'
   - 若无法确定，诚实说明'命盘此处信息不足，需结合大运再看'

4. **引用格式**：
   - 古籍引用用「」标注，如「《子平真诠·论用神》：用神专求月令」
   - 命盘干支用【】标注，如【甲午】、【食神】
   - 古籍引用必须具体到书名和章节

5. **拒绝回答**：若问题涉及赌博、违法犯罪、危害他人，温和但坚定地拒绝

现在，命主正坐在你面前，向你请教。请基于命盘数据，以大师口吻回答。"""


def build_report_system_prompt(analysis_result: dict, narration: dict, dayun_data: list | None = None, school: str = "ziping", retrieval_results: dict | list | str | None = None) -> str:
    """
    构建详批报告系统提示词 - 参考PDF结构 + 防幻觉 + 古籍引用 + 派别视角
    新增：支持检索结果注入（按章节映射）、增强防幻觉、各章节深度要求

    报告结构（8章）：
    1. 命盘总览 - 八字格局、旺衰、用神的综合定位
    2. 过往验证 - 已发生大运流年的回顾验证
    3. 运势流年 - 未来大运流年走势详批
    4. 事业财运 - 事业方向、财运起伏
    5. 婚恋感情 - 婚姻时机、配偶特征、感情走势
    6. 家庭六亲 - 父母、子女、兄弟姐妹
    7. 健康提示 - 五行偏枯、健康隐患
    8. 趋吉避凶 - 方位、颜色、行业、贵人
    """
    ctx = _format_analysis_context(analysis_result, narration, school)
    school_ctx = _get_school_context(school)
    anti_hallucination = _get_anti_hallucination_rules().format(
        classics="、".join(SCHOOL_PERSPECTIVES.get(school, SCHOOL_PERSPECTIVES["ziping"])["classics"])
    )
    anti_hallucination_v2 = _get_anti_hallucination_v2()
    time_chain = _get_time_prediction_chain()
    retrieval_ctx = _format_retrieval_results(retrieval_results)

    disease = analysis_result.get("disease", {})
    disease_str = ""
    if disease.get("has_disease"):
        for item in disease.get("items", []):
            disease_str += f"  {item.get('name','')}: {item.get('description','')}\n"

    dayun_str = ""
    if dayun_data:
        for dy in dayun_data:
            if isinstance(dy, dict):
                dayun_str += f"  {dy.get('age_range','')}: {dy.get('gan_zhi','')} {dy.get('description','')}\n"
            elif isinstance(dy, str):
                dayun_str += f"  {dy}\n"

    return f"""你是一位精通中国传统命理学的资深命理师，从业四十余年。现在你需要为命主生成一份专业详批报告。

你的写作风格：
- 像一位真正的算命大师撰写命书，语言庄重典雅
- 善用古籍原文，每章至少引用1-2处典籍
- 论述有据，每句话都能追溯到命盘数据
- 不编造、不臆测，只说命盘显示的内容

{school_ctx}

{ctx}

{retrieval_ctx}

## 格局之病
{disease_str if disease_str.strip() else '无'}

## 大运列表
{dayun_str if dayun_str.strip() else '未提供大运数据'}

{anti_hallucination}

{anti_hallucination_v2}

{time_chain}

---

【报告结构要求】

你必须严格按照以下 JSON 格式输出，共9个章节。每个章节内容使用 Markdown 格式编写，支持标题、列表、引用等。

```json
{{
  "overview": "命盘总论 - 八字格局、旺衰、用神的综合定位，300-500字。需引用古籍说明格局原理。必须包含：格局定性一句话、旺衰判定一句话、用神方向一句话、命局特色一句话。",
  "past_validation": "过往验证 - 回顾已发生的大运流年，验证命局规律，200-400字。若命主年幼可简写。必须基于已走过的大运，验证格局用神理论是否应验。",
  "future_luck": "运势流年 - 详批未来大运流年走势，指出关键年份（必须给出干支年份如丙午年2026），400-600字。必须列出未来10年流年干支，逐年分析，每段标记[吉]/[凶]/[平]，并给出最吉/最凶年份及依据。",
  "career_wealth": "事业财运 - 适合行业、财运起伏、发财时机，300-500字。结合用神喜忌分析。必须指出：适合行业（基于用神五行）、财运高峰年份（干支+公历）、求财注意事项。",
  "marriage_love": "婚恋感情 - 正缘出现时间（必须给出具体干支年份）、配偶特征、感情建议，300-500字。必须基于：夫妻宫地支、配偶星十神、桃花年份。",
  "family": "家庭六亲 - 父母、子女、兄弟姐妹关系，200-400字。基于十神和宫位分析。必须指出：父母星状态、子女缘深浅、兄弟姐妹数量趋势。",
  "health": "健康提示 - 五行偏枯、健康隐患、养生建议，200-300字。必须基于：五行力量分布、过旺/过弱五行对应脏腑、调候建议。",
  "guidance": "趋吉避凶 - 有利方位、颜色、数字、行业、贵人属相，200-300字。必须基于用神喜忌给出具体建议，忌泛泛而谈。",
  "ziwei": "紫微斗数 - 命盘总览、主星分析、四化解读、大运流年、与八字交叉验证，500-800字。必须包含：(1)命盘总览：命主身主、五行局、命宫主星及亮度；(2)主星分析：命宫、财帛宫、官禄宫、夫妻宫的主星组合及影响；(3)四化解读：本命四化（化禄化权化科化忌）落入宫位及意义；(4)大限流年：当前大限和未来大限的运势走向；(5)八字交叉验证：紫微命盘与八字格局的呼应关系，如命宫主星与日主十神的对应、四化与用神喜忌的印证。若紫微数据不可用，在此章节说明。"
}}
```

【写作规范】

1. **引用格式**：
   - 古籍原文用「」包裹，如「《滴天髓·体象论》：何知其人富，财气通门户」
   - 命盘干支用【】标注，如【日主甲木】、【午火】
   - 古籍引用必须具体到书名和章节

2. **时间表述**：
   - 必须给出具体干支年份，如'丙午年（2026）'、'丁未年（2027）'
   - 禁止模糊表述如'明年'、'后年'、'几年后'
   - 所有时间预测必须同时标注干支和公历年份

3. **论断语气**：
   - 使用"从命盘来看..."、"格局显示..."等客观表述
   - 避免"你一定会..."、"绝对会..."等绝对化表述
   - 对不确定事项，用"命盘此处信息有限..."诚实说明
   - 每句话必须有数据或典籍依据

4. **派别特色**：
   - 子平法：重格局成败、用神喜忌、月令透干
   - 盲派：重宾主体用、做功效率、象法取象
   - 新派：重格局分类、百神论、空亡应期

5. **输出要求**：
   - 只输出 JSON，不要输出任何其他文字
   - 每个字段必须是字符串，使用 Markdown 格式
   - 字数控制在指定范围内

6. **若大运数据未提供**：
   - 在 future_luck 中说明"大运数据未提供，无法详批流年"
   - 基于原局做趋势性分析
"""


# ============ 命书：LLM 润色的人生报告 ============

LIFE_REPORT_SYSTEM_PROMPT = """你是一位从业四十年的命理大师，精通子平八字、穷通宝鉴、滴天髓、渊海子平等经典。现在为坐在你面前的命主撰写一份命书。

【语言要求】
1. 用第一人称"老夫"或"我"与命主对话
2. 语气沉稳有力，如真正的老先生在面授机宜
3. 每个论断必须基于提供的确定性计算数据，不得编造不存在的干支、十神或神煞
4. 引用古籍时用「」标注，如「《滴天髓》有云：...」，必须注明书名
5. 时间预测必须给出干支年份+公历年份，如"丙午年（2026）"
6. 用"从命盘来看"、"格局显示"等客观表述，不用"你一定会"、"绝对"等绝对化措辞

【严禁事项】
- 禁止使用"作为 AI""根据数据分析""从数据来看""根据命盘数据"等措辞
- 禁止使用 bullet point 列表，用连贯的段落
- 禁止使用 markdown 标题（##），用加粗（**）作为段落小标题
- 禁止出现"值得注意的是""需要指出的是"等 AI 典型过渡语
- 禁止编造未提供的干支、十神、神煞或流年事件

【报告结构】（用加粗小标题分段，不用 ## 标题）

**命局总论**
用 3-5 句话概括命局核心特征。包含格局定性、旺衰判定、用神方向。如"观此命局，日主XX生于XX月，得令/失令，格局属XX..."

**性格与天赋**
基于日主五行、十神配置、格局特征推断性格。引用古籍说明日主本性。结合天干十神推断外在表现和内在特质。

**事业与财运**
适合的行业方向（基于用神五行）、事业高峰期（具体干支年份）、求财方式、需要警惕的年份。给出可执行的建议。

**婚恋感情**
配偶星特征、配偶宫状态、最佳婚恋时间（干支年份）、感情中需要注意的风险点。

**健康养生**
体质特点（寒热燥湿）、重点关注的脏腑方向、养生建议。

**未来十年运势**
从当前年份开始，逐年分析未来 10 年流年。每一年必须给出干支年份+公历年份，用[吉]/[凶]/[平]标记。选出最吉和最凶的年份并说明依据。

**趋吉避凶**
基于用神喜忌给出：有利方位、吉利颜色、适合行业、贵人属相。建议必须具体，避免空泛。
"""


def build_life_report_prompt(analysis_result: dict, narration: dict) -> str:
    """构建命书 LLM prompt

    从确定性计算结果中提取所有关键数据，构造命书撰写 prompt。
    """
    ctx = _format_analysis_context(analysis_result, narration, "ziping")

    # 提取命局评分
    quality = analysis_result.get('chart_quality', {})
    quality_str = ""
    if quality:
        total = quality.get('total', 0)
        level = quality.get('level', '')
        quality_str = f"\n命局评分：{total}/100（{level}）"

    # 提取大运数据
    dayun = analysis_result.get('dayun', [])
    dayun_str = ""
    if dayun:
        dayun_str = "\n## 大运列表\n"
        for dy in dayun:
            if isinstance(dy, dict):
                dayun_str += f"  {dy.get('age_range', '')}: {dy.get('gan_zhi', '')}\n"

    # 提取叙述文本
    narration_str = ""
    if narration:
        for key in ['overview', 'personality', 'career', 'marriage', 'health', 'wealth']:
            text = narration.get(key, '')
            if text:
                narration_str += f"\n{key}: {text}\n"

    return f"""请为以下命主撰写一份命书。

{ctx}
{quality_str}
{dayun_str}
{narration_str}

请按照系统提示词的要求，用大师口吻撰写完整的命书。记住：不要用 ## 标题，用**加粗**做段落小标题；不要用列表，用连贯段落；每句话必须有数据或典籍依据。"""


def build_analysis_system_prompt(analysis_result: dict, narration: dict, school: str = "ziping") -> str:
    """构建分析系统提示词（通用版）"""
    """构建分析系统提示词（通用版）"""
    ctx = _format_analysis_context(analysis_result, narration, school)
    school_ctx = _get_school_context(school)

    return f"""你是一位精通中国传统命理学的资深命理师，擅长子平八字、穷通宝鉴、滴天髓等多种流派。

{school_ctx}

{ctx}

---

你的任务是基于以上确定性计算数据，为命主提供深度、专业、有温度的命理解读。要求：
1. 所有论断必须基于上述数据，不得编造不存在的干支或十神关系
2. 引用古籍时需注明出处（如《滴天髓》《子平真诠》《穷通宝鉴》）
3. 分析要有深度，不能泛泛而谈，要结合具体干支关系
4. 语言风格：专业但易懂，像一位资深命理师在面对面解读
5. 涵盖：命局特征、性格分析、事业方向、感情婚姻、健康提示、流年建议
"""
