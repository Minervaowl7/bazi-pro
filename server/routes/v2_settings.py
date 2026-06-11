from __future__ import annotations

import ipaddress
import logging
import socket
from urllib.parse import urlparse

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from server.deps import error_response, verify_api_key
from server.llm import get_llm_config, update_llm_config

logger = logging.getLogger("bazi-pro")

router = APIRouter()

# 私有/保留 IP 段黑名单，防止 SSRF
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


# 域名黑名单，防止 SSRF
_BLOCKED_DOMAINS = {"localhost", "metadata.google.internal"}

# 域名后缀黑名单，防止通配符 DNS 解析绕过
_BLOCKED_DOMAIN_SUFFIXES = (".nip.io", ".localtest.me")


def _is_private_ip(hostname: str) -> bool:
    """检查主机名是否解析到私有/保留 IP 段。

    1. 先检查域名黑名单
    2. 尝试直接解析为 IP 地址
    3. 域名 → DNS 解析，检查所有结果
    4. DNS 解析失败 → fail-closed（返回 True）
    """
    hostname_lower = hostname.lower().rstrip(".")

    # 域名黑名单检查
    if hostname_lower in _BLOCKED_DOMAINS:
        return True

    # 域名后缀黑名单检查
    for suffix in _BLOCKED_DOMAIN_SUFFIXES:
        if hostname_lower.endswith(suffix):
            return True

    # 尝试直接解析为 IP 地址
    try:
        addr = ipaddress.ip_address(hostname)
        return any(addr in net for net in _PRIVATE_NETWORKS)
    except ValueError:
        pass

    # 域名 → DNS 解析，检查所有解析结果
    try:
        addrinfos = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addrinfos:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
                if any(ip in net for net in _PRIVATE_NETWORKS):
                    return True
            except ValueError:
                continue
        return False
    except (socket.gaierror, OSError):
        # DNS 解析失败 → fail-closed
        return True


class LLMSettingsRequest(BaseModel):
    api_key: str = Field(default="", description="LLM API Key")
    api_base: str = Field(default="https://api.openai.com/v1", description="API Base URL")
    model: str = Field(default="gpt-4o-mini", description="模型名称")


@router.get("/api/v2/settings/llm")
async def api_v2_get_llm_settings(_auth=Depends(verify_api_key)):
    cfg = get_llm_config()
    return JSONResponse({
        "api_base": cfg["api_base"],
        "api_key_set": cfg["api_key_set"],
        "model": cfg["model"],
    })


@router.post("/api/v2/settings/llm")
async def api_v2_update_llm_settings(req: LLMSettingsRequest, _auth=Depends(verify_api_key)):
    # SSRF 防护：校验 api_base 不指向私有 IP
    if req.api_base:
        try:
            parsed = urlparse(req.api_base)
            hostname = parsed.hostname or ""
            if _is_private_ip(hostname):
                return error_response(400, "INVALID_INPUT", "api_base 不允许指向私有/保留 IP 地址")
        except Exception:
            return error_response(400, "INVALID_INPUT", "api_base URL 格式不合法")

    try:
        update_llm_config(
            api_key=req.api_key or None,
            api_base=req.api_base or None,
            model=req.model or None,
        )
    except ValueError as e:
        return error_response(400, "INVALID_INPUT", str(e))
    cfg = get_llm_config()
    return JSONResponse({
        "ok": True,
        "api_base": cfg["api_base"],
        "api_key_set": cfg["api_key_set"],
        "model": cfg["model"],
    })


@router.post("/api/v2/settings/llm/test")
async def api_v2_test_llm_settings(_auth=Depends(verify_api_key)):
    from server.llm import chat_completion, is_llm_configured
    if not is_llm_configured():
        return error_response(400, "NOT_CONFIGURED", "API Key 未配置")
    try:
        reply = await chat_completion(
            [{"role": "user", "content": "请回复\"连接成功\"两个字"}],
            max_tokens=100,
        )
        return JSONResponse({"ok": True, "reply": reply[:100]})
    except Exception as e:
        return error_response(502, "CONNECTION_FAILED", f"连接测试失败: {str(e) or type(e).__name__}")
