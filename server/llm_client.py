"""
LLM 客户端模块 — 配置管理 + HTTP 调用 + 函数调用
"""
import asyncio
import json
import logging
import os
import re

import httpx

logger = logging.getLogger("bazi-pro.llm")

# ============ 配置管理 ============

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


# ============ 核心 LLM 调用 ============


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


async def _post_with_retry(
    url: str,
    headers: dict,
    payload: dict,
    *,
    max_retries: int = 3,
) -> dict:
    """带重试逻辑的 HTTP POST 请求。

    - 429 限流：指数退避 min(5*(attempt+1), 30)，最多重试 max_retries 次
    - 5xx 服务端错误：延迟 1*(attempt+1)，最多重试 max_retries 次
    - 401/403 认证失败：不重试，直接抛异常
    - 其他 4xx：不重试，raise_for_status
    """
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        async with httpx.AsyncClient(timeout=httpx.Timeout(_LLM_TIMEOUT, connect=5.0)) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in (401, 403):
                raise RuntimeError(f"LLM API 认证失败 (HTTP {resp.status_code})，请检查 LLM_API_KEY")
            if resp.status_code == 429:
                wait = min(5 * (attempt + 1), 30)
                logger.warning("[llm] rate limited (429), retry %d/%d after %ds", attempt + 1, max_retries, wait)
                await asyncio.sleep(wait)
                continue
            if resp.status_code >= 500:
                if attempt < max_retries:
                    logger.warning("[llm] server error %d, retry %d/%d", resp.status_code, attempt + 1, max_retries)
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                resp.raise_for_status()
            resp.raise_for_status()
            return resp.json()
    raise RuntimeError(f"LLM API 请求失败，已重试 {max_retries} 次") from last_exc


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

        data = await _post_with_retry(url, headers, payload)

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

        data = await _post_with_retry(url, headers, payload)

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
