import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from itstart_core_api import models
from itstart_core_api.auth import _create_access_token
from itstart_core_api.config import Settings, get_settings
from itstart_core_api.dependencies import get_db_session
from itstart_core_api.main import create_app
from itstart_core_api.security import hash_password


def setup_app(monkeypatch):
    monkeypatch.setenv("POSTGRES_DSN", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings(access_token_ttl_sec=3600)
    app = create_app(settings)
    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    @pytest.fixture
    async def override_session():
        async with Session() as session:
            yield session

    async def override_get_db_session():
        async with Session() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[Settings] = lambda: settings
    app.dependency_overrides[get_settings] = lambda: settings
    return app, settings, Session, engine


@pytest.mark.asyncio
async def test_admin_user_creation_and_list(monkeypatch):
    app, settings, Session, engine = setup_app(monkeypatch)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    # seed admin
    async with Session() as session:
        admin = models.AdminUser(
            id=uuid4(),
            username="root",
            password_hash=hash_password("root"),
            role=models.AdminRole.admin,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
        )
        session.add(admin)
        await session.commit()

    token = _create_access_token(settings, str(admin.id))
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/admin/users",
        headers=headers,
        params={"username": "newuser", "role": "moderator"},
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["user"]["username"] == "newuser"
    assert created["user"]["role"] == "moderator"
    assert isinstance(created["temporary_password"], str)
    assert len(created["temporary_password"]) >= 8

    resp = client.get("/admin/users", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert any(u["username"] == "newuser" for u in data)
