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
async def test_publications_crud_flow(monkeypatch):
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
        tag = models.Tag(id=uuid4(), name="python", category=TagCategory.language)
        session.add(tag)
        pub = models.Publication(
            id=uuid4(),
            title="Py Dev",
            description="desc",
            type=PublicationType.job,
            company="Co",
            url="u",
            created_at=datetime.datetime.utcnow(),
            vacancy_created_at=datetime.datetime.utcnow(),
            status="new",
            is_declined=False,
        )
        session.add(pub)
        session.add(models.PublicationTag(publication_id=pub.id, tag_id=tag.id))
        await session.commit()

    token = _create_access_token(settings, str(admin.id))
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/admin/publications", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    deadline = datetime.datetime.utcnow().isoformat()
    resp = client.patch(
        f"/admin/publications/{pub.id}",
        headers=headers,
        params={"title": "New title", "contact_info": "mail", "deadline_at": deadline, "status": "ready"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["title"] == "New title"
    assert data["editor_id"] is None or isinstance(data.get("editor_id"), str)

    resp = client.post(f"/admin/publications/{pub.id}/decline", headers=headers, params={"reason": "bad"})
    assert resp.status_code == 204

    resp = client.post(f"/admin/publications/{pub.id}/approve-and-send", headers=headers)
    assert resp.status_code == 204
