import logging
import os
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth.jwt_handler import create_access_token, verify_token
from server.auth.password import hash_password, verify_password
from server.database import get_db, is_degraded
from server.models import User

logger = logging.getLogger("bazi-pro.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    display_name: Optional[str] = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class WechatRequest(BaseModel):
    code: str


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def _make_token_response(user: User) -> JSONResponse:
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return JSONResponse({
        "token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "is_active": user.is_active,
        },
    })


@router.post("/register")
async def register(body: RegisterRequest, db: Optional[AsyncSession] = Depends(get_db)):
    if is_degraded() or db is None:
        return _error_response(503, "SERVICE_UNAVAILABLE", "数据库不可用，请稍后重试")

    stmt = select(User).where(User.email == body.email)
    result = await db.execute(stmt)
    if result.scalars().first():
        return _error_response(409, "CONFLICT", "该邮箱已注册")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        display_name=body.display_name,
    )
    db.add(user)
    await db.flush()

    return _make_token_response(user)


@router.post("/login")
async def login(body: LoginRequest, db: Optional[AsyncSession] = Depends(get_db)):
    if is_degraded() or db is None:
        return _error_response(503, "SERVICE_UNAVAILABLE", "数据库不可用，请稍后重试")

    stmt = select(User).where(User.email == body.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(body.password, user.hashed_password):
        return _error_response(401, "UNAUTHORIZED", "邮箱或密码错误")

    if not user.is_active:
        return _error_response(403, "FORBIDDEN", "账户已被禁用")

    return _make_token_response(user)


@router.get("/me")
async def me(request: Request, db: Optional[AsyncSession] = Depends(get_db)):
    if is_degraded() or db is None:
        return _error_response(503, "SERVICE_UNAVAILABLE", "数据库不可用，请稍后重试")

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return _error_response(401, "UNAUTHORIZED", "缺少有效的认证信息")

    token = auth_header[len("Bearer "):]
    payload = verify_token(token)
    if payload is None:
        return _error_response(401, "UNAUTHORIZED", "令牌无效或已过期")

    user_id = payload.get("sub")
    if not user_id:
        return _error_response(401, "UNAUTHORIZED", "令牌无效")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        return _error_response(404, "NOT_FOUND", "用户不存在")

    if not user.is_active:
        return _error_response(403, "FORBIDDEN", "账户已被禁用")

    return JSONResponse({
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "oauth_provider": user.oauth_provider,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    })


@router.post("/wechat")
async def wechat_login(body: WechatRequest, db: Optional[AsyncSession] = Depends(get_db)):
    if is_degraded() or db is None:
        return _error_response(503, "SERVICE_UNAVAILABLE", "数据库不可用，请稍后重试")

    app_id = os.environ.get("WECHAT_APP_ID", "")
    app_secret = os.environ.get("WECHAT_APP_SECRET", "")
    if not app_id or not app_secret:
        return _error_response(503, "SERVICE_UNAVAILABLE", "微信登录未配置")

    async with httpx.AsyncClient(timeout=10) as client:
        token_resp = await client.get(
            "https://api.weixin.qq.com/sns/oauth2/access_token",
            params={
                "appid": app_id,
                "secret": app_secret,
                "code": body.code,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_resp.json()

    if "access_token" not in token_data or "openid" not in token_data:
        return _error_response(401, "UNAUTHORIZED", "微信授权失败")

    wechat_access_token = token_data["access_token"]
    openid = token_data["openid"]

    async with httpx.AsyncClient(timeout=10) as client:
        userinfo_resp = await client.get(
            "https://api.weixin.qq.com/sns/userinfo",
            params={"access_token": wechat_access_token, "openid": openid},
        )
        userinfo = userinfo_resp.json()

    nickname = userinfo.get("nickname", "")
    avatar = userinfo.get("headimgurl", "")

    stmt = select(User).where(User.oauth_provider == "wechat", User.oauth_id == openid)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user:
        if not user.is_active:
            return _error_response(403, "FORBIDDEN", "账户已被禁用")
        return _make_token_response(user)

    user = User(
        email=f"wechat_{openid}@oauth.local",
        hashed_password=hash_password(os.urandom(32).hex()),
        display_name=nickname or None,
        avatar_url=avatar or None,
        oauth_provider="wechat",
        oauth_id=openid,
    )
    db.add(user)
    await db.flush()

    return _make_token_response(user)
