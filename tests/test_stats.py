import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from itstart_core_api import models
from itstart_core_api.auth import _create_access_token
from itstart_core_api.config import Settings, get_settings
from itstart_core_api.dependencies import get_db_session
from itstart_core_api.main import create_app
from itstart_core_api.security import hash_password
from itstart_domain import PublicationType, TagCategory
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_stats_and_export(monkeypatch):
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
    app.dependency_overrides[get_settings] = lambda: settings

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
        tag = models.Tag(name="python", category=TagCategory.technology)
        session.add(tag)
        user = models.TgUser(tg_id=1, register_at=datetime.datetime.utcnow(), is_active=True)
        session.add(user)
        pub = models.Publication(
            title="t",
            description="d",
            type=PublicationType.job,
            company="c",
            url="u",
            created_at=datetime.datetime.utcnow(),
            vacancy_created_at=datetime.datetime.utcnow(),
            status="sent",
        )
        session.add(pub)
        await session.commit()

    token = _create_access_token(settings, str(admin.id))
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/admin/stats/users", headers=headers)
    assert resp.status_code == 200
    assert "active_users" in resp.json()

    resp = client.get("/admin/stats/tags/top", headers=headers)
    assert resp.status_code == 200

    resp = client.get("/admin/stats/publications", headers=headers)
    assert resp.status_code == 200

    resp = client.get("/admin/stats/parsers", headers=headers)
    assert resp.status_code == 200

    resp = client.get("/admin/export/publications", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("text/csv")
