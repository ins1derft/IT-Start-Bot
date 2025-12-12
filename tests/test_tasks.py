import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from itstart_core_api import models
from itstart_core_api.config import Settings
from itstart_core_api.tasks import (
    cleanup_old_publications,
    run_parsers,
    send_publication_with_session,
    send_publication_now,
    send_deadline_reminders,
    send_publications,
    _send_telegram_message,
    _eligible_subscriptions,
    _format_publication,
    _parse_publication_type,
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


def test_format_publication_upd_deadline_and_tags():
    pub = models.Publication(
        id=uuid4(),
        title="Title",
        description="Desc",
        type=models.PublicationType.job,
        company="Company",
        url="https://example.com",
        created_at=datetime.datetime.utcnow(),
        vacancy_created_at=datetime.datetime.utcnow(),
        status="new",
        is_declined=False,
        deadline_at=datetime.datetime(2030, 1, 5, 12, 0, 0),
        is_edited=True,
    )
    text = _format_publication(pub, ["python", "remote"], updated=True)
    assert text.startswith("[UPD] ")
    assert "Дедлайн:" in text
    assert "#python" in text
    assert "#remote" in text


def test_parse_publication_type_validation():
    assert _parse_publication_type(None) is None
    assert _parse_publication_type(models.PublicationType.job) == models.PublicationType.job
    assert _parse_publication_type("job") == models.PublicationType.job
    with pytest.raises(ValueError):
        _parse_publication_type("nope")


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


@pytest.mark.asyncio
async def test_send_publications_filters_by_type(monkeypatch, tmp_path):
    db_path = tmp_path / "test4.db"
    monkeypatch.setenv("POSTGRES_DSN", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings()
    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async with Session() as session:
        pub_job = models.Publication(
            id=uuid4(),
            title="Job",
            description="d",
            type=models.PublicationType.job,
            company="C",
            url="u1",
            created_at=datetime.datetime.utcnow(),
            vacancy_created_at=datetime.datetime.utcnow(),
            status="new",
            is_declined=False,
        )
        pub_contest = models.Publication(
            id=uuid4(),
            title="Contest",
            description="d",
            type=models.PublicationType.contest,
            company="C",
            url="u2",
            created_at=datetime.datetime.utcnow(),
            vacancy_created_at=datetime.datetime.utcnow(),
            status="new",
            is_declined=False,
        )
        session.add_all([pub_job, pub_contest])
        await session.commit()

    monkeypatch.setattr("itstart_core_api.tasks.get_settings", lambda: settings)
    await send_publications(publication_type="job")

    async with Session() as session:
        pubs = (await session.execute(select(models.Publication))).scalars().all()
        by_title = {p.title: p for p in pubs}
        assert by_title["Job"].status == "sent"
        assert by_title["Contest"].status == "new"


@pytest.mark.asyncio
async def test_eligible_subscriptions_respects_required_tags(monkeypatch, tmp_path):
    db_path = tmp_path / "test5.db"
    monkeypatch.setenv("POSTGRES_DSN", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings()
    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    tag_python = models.Tag(name="python", category=models.TagCategory.technology)
    tag_java = models.Tag(name="java", category=models.TagCategory.technology)

    async with Session() as session:
        session.add_all([tag_python, tag_java])
        await session.flush()

        pub = models.Publication(
            id=uuid4(),
            title="Job",
            description="d",
            type=models.PublicationType.job,
            company="C",
            url="u3",
            created_at=datetime.datetime.utcnow(),
            vacancy_created_at=datetime.datetime.utcnow(),
            status="ready",
            is_declined=False,
        )
        session.add(pub)
        await session.flush()
        session.add(models.PublicationTag(publication_id=pub.id, tag_id=tag_python.id))

        user_ok = models.TgUser(
            id=uuid4(), tg_id=1, register_at=datetime.datetime.utcnow(), is_active=True
        )
        user_miss = models.TgUser(
            id=uuid4(), tg_id=2, register_at=datetime.datetime.utcnow(), is_active=True
        )
        session.add_all([user_ok, user_miss])
        await session.flush()

        sub_ok = models.TgUserSubscription(
            user_id=user_ok.id, publication_type=models.PublicationType.job
        )
        sub_miss = models.TgUserSubscription(
            user_id=user_miss.id, publication_type=models.PublicationType.job
        )
        session.add_all([sub_ok, sub_miss])
        await session.flush()

        session.add(
            models.TgUserSubscriptionTag(subscription_id=sub_ok.id, tag_id=tag_python.id)
        )
        session.add(
            models.TgUserSubscriptionTag(subscription_id=sub_miss.id, tag_id=tag_java.id)
        )

        await session.commit()

        result = list(await _eligible_subscriptions(session, pub))
        assert len(result) == 1
        _sub, user = result[0]
        assert user.tg_id == 1


@pytest.mark.asyncio
async def test_send_publication_now_returns_false_for_declined(monkeypatch, tmp_path):
    db_path = tmp_path / "test6.db"
    monkeypatch.setenv("POSTGRES_DSN", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings()
    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    pub_id = uuid4()
    async with Session() as session:
        pub = models.Publication(
            id=pub_id,
            title="Declined",
            description="d",
            type=models.PublicationType.job,
            company="C",
            url="u4",
            created_at=datetime.datetime.utcnow(),
            vacancy_created_at=datetime.datetime.utcnow(),
            status="ready",
            is_declined=True,
        )
        session.add(pub)
        await session.commit()

    monkeypatch.setattr("itstart_core_api.tasks.get_settings", lambda: settings)
    ok = await send_publication_now(pub_id)
    assert ok is False


@pytest.mark.asyncio
async def test_send_publications_sends_to_channel_and_subscribers(monkeypatch, tmp_path):
    db_path = tmp_path / "test7.db"
    monkeypatch.setenv("POSTGRES_DSN", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings()
    settings.bot_token = "token"
    settings.bot_channel_id = "@channel"

    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    pub_id = uuid4()
    async with Session() as session:
        tag = models.Tag(name="python", category=models.TagCategory.technology)
        session.add(tag)
        await session.flush()

        pub = models.Publication(
            id=pub_id,
            title="Job",
            description="d",
            type=models.PublicationType.job,
            company="C",
            url="u5",
            created_at=datetime.datetime.utcnow(),
            vacancy_created_at=datetime.datetime.utcnow(),
            status="new",
            is_declined=False,
        )
        session.add(pub)
        await session.flush()
        session.add(models.PublicationTag(publication_id=pub.id, tag_id=tag.id))

        user = models.TgUser(
            id=uuid4(), tg_id=100, register_at=datetime.datetime.utcnow(), is_active=True
        )
        session.add(user)
        await session.flush()

        sub = models.TgUserSubscription(user_id=user.id, publication_type=models.PublicationType.job)
        session.add(sub)
        await session.commit()

    sent: list[tuple[int | str, str]] = []

    async def fake_send(_token: str, chat_id: int | str, text: str) -> None:
        sent.append((chat_id, text))

    monkeypatch.setattr("itstart_core_api.tasks.get_settings", lambda: settings)
    monkeypatch.setattr("itstart_core_api.tasks._send_telegram_message", fake_send)

    await send_publications(publication_type="job")

    # one to channel, one to user
    chat_ids = [c for c, _ in sent]
    assert settings.bot_channel_id in chat_ids
    assert 100 in chat_ids


@pytest.mark.asyncio
async def test_send_publication_now_marks_sent(monkeypatch, tmp_path):
    db_path = tmp_path / "test8.db"
    monkeypatch.setenv("POSTGRES_DSN", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings()
    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    pub_id = uuid4()
    async with Session() as session:
        pub = models.Publication(
            id=pub_id,
            title="Now",
            description="d",
            type=models.PublicationType.job,
            company="C",
            url="u6",
            created_at=datetime.datetime.utcnow(),
            vacancy_created_at=datetime.datetime.utcnow(),
            status="ready",
            is_declined=False,
        )
        session.add(pub)
        await session.commit()

    monkeypatch.setattr("itstart_core_api.tasks.get_settings", lambda: settings)
    ok = await send_publication_now(pub_id)
    assert ok is True

    async with Session() as session:
        saved = (await session.execute(select(models.Publication))).scalar_one()
        assert saved.status == "sent"


@pytest.mark.asyncio
async def test_deadline_reminders_respects_deadline_reminder_flag(monkeypatch, tmp_path):
    db_path = tmp_path / "test9.db"
    monkeypatch.setenv("POSTGRES_DSN", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings()
    settings.bot_token = "token"

    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    now = datetime.datetime.utcnow()
    pub_id = uuid4()
    async with Session() as session:
        pub = models.Publication(
            id=pub_id,
            title="Deadline",
            description="d",
            type=models.PublicationType.job,
            company="C",
            url="u7",
            created_at=now,
            vacancy_created_at=now,
            status="new",
            is_declined=False,
            deadline_at=now + datetime.timedelta(days=2),
            deadline_notified=False,
        )
        session.add(pub)
        await session.flush()

        user_on = models.TgUser(id=uuid4(), tg_id=201, register_at=now, is_active=True)
        user_off = models.TgUser(id=uuid4(), tg_id=202, register_at=now, is_active=True)
        session.add_all([user_on, user_off])
        await session.flush()

        sub_on = models.TgUserSubscription(
            user_id=user_on.id,
            publication_type=models.PublicationType.job,
            deadline_reminder=True,
        )
        sub_off = models.TgUserSubscription(
            user_id=user_off.id,
            publication_type=models.PublicationType.job,
            deadline_reminder=False,
        )
        session.add_all([sub_on, sub_off])
        await session.commit()

    sent_to: list[int | str] = []

    async def fake_send(_token: str, chat_id: int | str, _text: str) -> None:
        sent_to.append(chat_id)

    monkeypatch.setattr("itstart_core_api.tasks.get_settings", lambda: settings)
    monkeypatch.setattr("itstart_core_api.tasks._send_telegram_message", fake_send)

    await send_deadline_reminders()
    assert 201 in sent_to
    assert 202 not in sent_to

    async with Session() as session:
        saved = (await session.execute(select(models.Publication))).scalar_one()
        assert saved.deadline_notified is True


@pytest.mark.asyncio
async def test_send_publication_with_session_sets_sent(monkeypatch, tmp_path):
    db_path = tmp_path / "test10.db"
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
            title="Direct",
            description="d",
            type=models.PublicationType.job,
            company="C",
            url="u8",
            created_at=datetime.datetime.utcnow(),
            vacancy_created_at=datetime.datetime.utcnow(),
            status="new",
            is_declined=False,
        )
        session.add(pub)
        await session.commit()

        await send_publication_with_session(session, settings, pub)
        assert pub.status == "sent"


@pytest.mark.asyncio
async def test_run_parsers_calls_run_due_parsers(monkeypatch, tmp_path):
    db_path = tmp_path / "test11.db"
    monkeypatch.setenv("POSTGRES_DSN", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("SECRET_KEY", "secret")
    settings = Settings()

    called = {"ok": False}

    async def fake_run_due_parsers(_session, _settings, now=None):
        called["ok"] = True
        return []

    monkeypatch.setattr("itstart_core_api.tasks.get_settings", lambda: settings)
    monkeypatch.setattr("itstart_core_api.tasks.run_due_parsers", fake_run_due_parsers)

    await run_parsers()
    assert called["ok"] is True


@pytest.mark.asyncio
async def test_send_telegram_message_uses_httpx_client(monkeypatch):
    calls: list[tuple[str, dict]] = []

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url: str, json: dict):
            calls.append((url, json))

    monkeypatch.setattr("itstart_core_api.tasks.httpx.AsyncClient", DummyClient)
    await _send_telegram_message("token", 123, "hello")
    assert calls
    assert "token" in calls[0][0]
