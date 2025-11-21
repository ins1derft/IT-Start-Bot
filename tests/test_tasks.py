import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from itstart_core_api import models
from itstart_core_api.config import Settings
from itstart_core_api.tasks import (
    cleanup_old_publications,
    send_deadline_reminders,
    send_publications,
)


@pytest.mark.asyncio
async def test_send_publications_marks_sent(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("POSTGRES_DSN", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings()
    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async with Session() as session:
        pub = models.Publication(
            id=uuid4(),
            title="Test",
            description="d",
            type=models.PublicationType.job,
            company="C",
            url="u",
            created_at=datetime.datetime.utcnow(),
            vacancy_created_at=datetime.datetime.utcnow(),
            status="new",
            is_declined=False,
        )
        session.add(pub)
        await session.commit()

    # monkeypatch send telegram to noop
    monkeypatch.setattr(
        "itstart_core_api.tasks._send_telegram_message", lambda *args, **kwargs: None
    )

    # patch settings to use same db url
    monkeypatch.setattr("itstart_core_api.tasks.get_settings", lambda: settings)
    await send_publications()

    async with Session() as session:
        res = await session.execute(select(models.Publication))
        saved = res.scalar_one()
        assert saved.status == "sent"


@pytest.mark.asyncio
async def test_deadline_reminders_flag(monkeypatch, tmp_path):
    db_path = tmp_path / "test2.db"
    monkeypatch.setenv("POSTGRES_DSN", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings()
    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async with Session() as session:
        pub = models.Publication(
            id=uuid4(),
            title="Conf",
            description="d",
            type=models.PublicationType.conference,
            company="C",
            url="u",
            created_at=datetime.datetime.utcnow(),
            vacancy_created_at=datetime.datetime.utcnow(),
            status="new",
            is_declined=False,
            deadline_at=datetime.datetime.utcnow() + datetime.timedelta(days=2),
        )
        session.add(pub)
        await session.commit()

    monkeypatch.setattr(
        "itstart_core_api.tasks._send_telegram_message", lambda *args, **kwargs: None
    )

    monkeypatch.setattr("itstart_core_api.tasks.get_settings", lambda: settings)
    await send_deadline_reminders()

    async with Session() as session:
        res = await session.execute(select(models.Publication))
        saved = res.scalar_one()
        assert saved.deadline_notified is True


@pytest.mark.asyncio
async def test_cleanup_old_publications(monkeypatch, tmp_path):
    db_path = tmp_path / "test3.db"
    monkeypatch.setenv("POSTGRES_DSN", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings()
    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async with Session() as session:
        old_pub = models.Publication(
            id=uuid4(),
            title="Old",
            description="d",
            type=models.PublicationType.job,
            company="C",
            url="u",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=120),
            vacancy_created_at=datetime.datetime.utcnow() - datetime.timedelta(days=120),
            status="sent",
            is_declined=False,
        )
        session.add(old_pub)
        await session.commit()

    monkeypatch.setattr("itstart_core_api.tasks.get_settings", lambda: settings)
    await cleanup_old_publications(days=90)

    async with Session() as session:
        res = await session.execute(select(models.Publication))
        assert res.scalar_one_or_none() is None
