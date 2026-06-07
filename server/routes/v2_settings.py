from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from server.deps import error_response, verify_api_key
from server.llm import get_llm_config, update_llm_config

router = APIRouter()


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
