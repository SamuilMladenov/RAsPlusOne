"""JWT auth dependencies."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET_KEY
from app.auth_accounts import Account

security = HTTPBearer()

Role = Literal["admin", "hospital", "triager"]


class TokenUser(BaseModel):
    email: str
    role: Role
    hospital_id: str | None = None


def create_access_token(account: Account) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": account.email,
        "role": account.role,
        "hospital_id": account.hospital_id,
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def parse_access_token(token: str) -> TokenUser | None:
    """Decode a bearer token; return None if invalid or expired."""
    try:
        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return TokenUser(
            email=data["sub"],
            role=data["role"],
            hospital_id=data.get("hospital_id"),
        )
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenUser:
    token = credentials.credentials
    user = parse_access_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


CurrentUser = Annotated[TokenUser, Depends(get_current_user)]


async def require_admin(user: TokenUser = Depends(get_current_user)) -> TokenUser:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


AdminUser = Annotated[TokenUser, Depends(require_admin)]


async def require_triager(user: TokenUser = Depends(get_current_user)) -> TokenUser:
    if user.role != "triager":
        raise HTTPException(status_code=403, detail="Triager access required")
    return user


TriagerUser = Annotated[TokenUser, Depends(require_triager)]


def ensure_hospital_access(user: TokenUser, hospital_id: str) -> None:
    if user.role == "admin":
        return
    if user.role == "hospital" and user.hospital_id == hospital_id:
        return
    raise HTTPException(status_code=403, detail="Not allowed to access this hospital")


__all__ = [
    "TokenUser",
    "CurrentUser",
    "AdminUser",
    "TriagerUser",
    "get_current_user",
    "parse_access_token",
    "require_admin",
    "require_triager",
    "create_access_token",
    "ensure_hospital_access",
]
