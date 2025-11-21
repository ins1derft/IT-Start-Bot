import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from itstart_core_api import models
from itstart_core_api.config import Settings
from itstart_core_api.dependencies import get_db_session
from itstart_core_api.main import create_app
from itstart_core_api.security import hash_password


@pytest.mark.asyncio
async def test_login_success(monkeypatch):
    # setup in-memory app overriding env precedence
    monkeypatch.setenv("POSTGRES_DSN", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings(access_token_ttl_sec=3600)
    app = create_app(settings)

    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async def override_get_db_session():
        async with Session() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    # insert admin user
    async with Session() as session:
        user = models.AdminUser(
            id=uuid4(),
            username="admin",
            password_hash=hash_password("password"),
            role=models.AdminRole.admin,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
        )
        session.add(user)
        await session.commit()

    client = TestClient(app)
    resp = client.post("/auth/login", json={"username": "admin", "password": "password"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(monkeypatch):
    monkeypatch.setenv("POSTGRES_DSN", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings(access_token_ttl_sec=3600)
    app = create_app(settings)
    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async def override_get_db_session():
        async with Session() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    async with Session() as session:
        user = models.AdminUser(
            id=uuid4(),
            username="admin",
            password_hash=hash_password("password"),
            role=models.AdminRole.admin,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
        )
        session.add(user)
        await session.commit()

    client = TestClient(app)
    resp = client.post("/auth/login", json={"username": "admin", "password": "bad"})
    assert resp.status_code == 401
