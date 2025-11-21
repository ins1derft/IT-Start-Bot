import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from itstart_core_api.main import create_app
from itstart_core_api.config import Settings, get_settings
from itstart_core_api import models
from itstart_core_api.dependencies import get_db_session
from itstart_core_api.security import hash_password
from itstart_core_api.auth import _create_access_token
from itstart_domain import ParserType


@pytest.mark.asyncio
async def test_parsers_crud(monkeypatch):
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
        await session.commit()

    token = _create_access_token(settings, str(admin.id))
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}

    start_time = datetime.datetime.utcnow()
    resp = client.post(
        "/admin/parsers",
        headers=headers,
        params={
            "source_name": "parser1",
            "executable_file_path": "/bin/parser",
            "type": "api_client",
            "parsing_interval": 10,
            "parsing_start_time": start_time.isoformat(),
            "is_active": True,
        },
    )
    assert resp.status_code == 201, resp.text
    parser_id = resp.json()["id"]

    resp = client.get("/admin/parsers", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.patch(
        f"/admin/parsers/{parser_id}",
        headers=headers,
        params={"parsing_interval": 20, "is_active": False},
    )
    assert resp.status_code == 200
    assert resp.json()["parsing_interval"] == 20
    assert resp.json()["is_active"] is False

    resp = client.post(f"/admin/parsers/{parser_id}/enable", headers=headers)
    assert resp.status_code == 204

    resp = client.get("/admin/parsers", headers=headers)
    assert resp.json()[0]["is_active"] is True

    resp = client.post(f"/admin/parsers/{parser_id}/disable", headers=headers)
    assert resp.status_code == 204
