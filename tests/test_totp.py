import datetime
from uuid import uuid4

import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from itstart_core_api.main import create_app
from itstart_core_api.config import Settings, get_settings
from itstart_core_api import models
from itstart_core_api.dependencies import get_db_session
from itstart_core_api.security import hash_password
from itstart_core_api.auth import _create_access_token


def make_app(monkeypatch):
    monkeypatch.setenv("POSTGRES_DSN", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings(access_token_ttl_sec=3600)
    app = create_app(settings)
    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db_session():
        async with Session() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_settings] = lambda: settings
    return app, settings, Session, engine


@pytest.mark.asyncio
async def test_setup_confirm_login_with_totp(monkeypatch):
    app, settings, Session, engine = make_app(monkeypatch)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async with Session() as session:
        user = models.AdminUser(
            id=uuid4(),
            username="root",
            password_hash=hash_password("pass"),
            role=models.AdminRole.admin,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
        )
        session.add(user)
        await session.commit()

    token = _create_access_token(settings, str(user.id))
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}

    # setup
    resp = client.post("/auth/setup-2fa", headers=headers)
    assert resp.status_code == 200
    secret = resp.json()["secret"]

    # confirm
    code = pyotp.TOTP(secret).now()
    resp = client.post("/auth/confirm-2fa", headers=headers, json={"code": code})
    assert resp.status_code == 204

    # login requires otp
    resp = client.post("/auth/login", json={"username": "root", "password": "pass"})
    assert resp.status_code == 401
    code = pyotp.TOTP(secret).now()
    resp = client.post("/auth/login", json={"username": "root", "password": "pass", "otp_code": code})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_disable_2fa_for_moderator(monkeypatch):
    app, settings, Session, engine = make_app(monkeypatch)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async with Session() as session:
        user = models.AdminUser(
            id=uuid4(),
            username="mod",
            password_hash=hash_password("pass"),
            role=models.AdminRole.moderator,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
            otp_secret=pyotp.random_base32(),
        )
        session.add(user)
        await session.commit()

    token = _create_access_token(settings, str(user.id))
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}
    code = pyotp.TOTP(user.otp_secret).now()
    resp = client.request("DELETE", "/auth/disable-2fa", headers=headers, json={"code": code})
    assert resp.status_code == 204
