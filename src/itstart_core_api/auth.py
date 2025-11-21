from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Settings, get_settings
from .dependencies import get_db_session
from .repositories import AdminUserRepository
from .rate_limiter import InMemoryRateLimiter
from .security import hash_password
from uuid import UUID

http_bearer = HTTPBearer(auto_error=False)
login_limiter = InMemoryRateLimiter(window_seconds=60, max_hits=5)
from .security import verify_password


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


router = APIRouter(prefix="/auth", tags=["auth"])


def _create_access_token(settings: Settings, subject: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": subject, "iat": datetime.utcnow(), "typ": "access"}
    expire = datetime.utcnow() + (expires_delta or timedelta(seconds=settings.access_token_ttl_sec))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def _create_refresh_token(settings: Settings, subject: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": subject, "iat": datetime.utcnow(), "typ": "refresh"}
    expire = datetime.utcnow() + (expires_delta or timedelta(seconds=settings.refresh_token_ttl_sec))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


async def get_current_admin(
    creds: HTTPAuthorizationCredentials = Depends(http_bearer),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
):
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    repo = AdminUserRepository(session)
    try:
        payload = jwt.decode(creds.credentials, settings.secret_key, algorithms=["HS256"])
        subject: str = payload.get("sub")
        if subject is None:
            raise ValueError
        user = await repo.get(UUID(subject))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
):
    login_limiter.check(payload.username)
    repo = AdminUserRepository(session)
    user = await repo.get_by_username(payload.username)
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access = _create_access_token(settings, subject=str(user.id))
    refresh = _create_refresh_token(settings, subject=str(user.id))
    return TokenResponse(access_token=access, refresh_token=refresh, expires_in=settings.access_token_ttl_sec)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    creds: HTTPAuthorizationCredentials = Depends(http_bearer),
    settings: Settings = Depends(get_settings),
):
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, settings.secret_key, algorithms=["HS256"])
        if payload.get("typ") != "refresh":
            raise ValueError
        subject: str = payload.get("sub")
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access = _create_access_token(settings, subject=subject)
    refresh = _create_refresh_token(settings, subject=subject)
    return TokenResponse(access_token=access, refresh_token=refresh, expires_in=settings.access_token_ttl_sec)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/change-password", status_code=204)
async def change_password(
    payload: ChangePasswordRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    current=Depends(get_current_admin),
):
    repo = AdminUserRepository(session)
    user = await repo.get(current.id)
    assert user
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid old password")
    user.password_hash = hash_password(payload.new_password)
    await session.commit()
    return None
