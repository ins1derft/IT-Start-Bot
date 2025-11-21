from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from itstart_domain import AdminRole

from .config import Settings, get_settings
from .dependencies import get_db_session
from .rate_limiter import InMemoryRateLimiter
from .repositories import AdminUserRepository
from .security import hash_password, verify_password

http_bearer = HTTPBearer(auto_error=False)
login_limiter = InMemoryRateLimiter(window_seconds=60, max_hits=5)


class LoginRequest(BaseModel):
    username: str
    password: str
    otp_code: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


router = APIRouter(prefix="/auth", tags=["auth"])


def _create_access_token(settings: Settings, subject: str, expires_delta: timedelta | None = None) -> str:
    to_encode = {"sub": subject, "iat": datetime.utcnow(), "typ": "access"}
    expire = datetime.utcnow() + (expires_delta or timedelta(seconds=settings.access_token_ttl_sec))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def _create_refresh_token(settings: Settings, subject: str, expires_delta: timedelta | None = None) -> str:
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
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
):
    login_limiter.check(payload.username)

    if settings.allowed_login_ips:
        client_ip = request.client.host
        if client_ip not in settings.allowed_login_ips:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="IP not allowed")

    repo = AdminUserRepository(session)
    user = await repo.get_by_username(payload.username)
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # If TOTP is set, require correct code
    if user.otp_secret:
        if not payload.otp_code:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP required")
        totp = pyotp.TOTP(user.otp_secret)
        if not totp.verify(payload.otp_code, valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

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


class TOTPSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class OTPCode(BaseModel):
    code: str


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


@router.post("/setup-2fa", response_model=TOTPSetupResponse)
async def setup_2fa(
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    secret = pyotp.random_base32()
    current.otp_secret = secret
    await session.commit()
    await session.refresh(current)
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=current.username, issuer_name="ITStart Admin")
    return TOTPSetupResponse(secret=secret, provisioning_uri=provisioning_uri)


@router.post("/confirm-2fa", status_code=204)
async def confirm_2fa(
    payload: OTPCode,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if not current.otp_secret:
        raise HTTPException(status_code=400, detail="2FA not set")
    totp = pyotp.TOTP(current.otp_secret)
    if not totp.verify(payload.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    return None


@router.delete("/disable-2fa", status_code=204)
async def disable_2fa(
    payload: OTPCode,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role == AdminRole.admin:
        raise HTTPException(status_code=400, detail="Admin must keep 2FA enabled")
    if not current.otp_secret:
        return None
    totp = pyotp.TOTP(current.otp_secret)
    if not totp.verify(payload.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    current.otp_secret = None
    await session.commit()
    return None
