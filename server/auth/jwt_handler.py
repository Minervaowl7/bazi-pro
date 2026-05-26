import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

_SECRET = os.environ.get("JWT_SECRET", "")
_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "1440"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, _SECRET, algorithm=_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
