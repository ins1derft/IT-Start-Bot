import datetime
from uuid import uuid4

import pytest
from itstart_core_api import models
from itstart_core_api.repositories import TagRepository
from itstart_domain import PublicationType, TagCategory
from itstart_tg_bot.service import (
    block_user,
    get_preferences,
    parse_tokens,
    search_publications,
    split_tokens,
    subscribe_tokens,
    unsubscribe_tokens,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def make_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    return engine, Session


@pytest.mark.asyncio
async def test_parse_tokens_and_subscribe():
    engine, Session = make_session()
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    async with Session() as session:
        tag_repo = TagRepository(session)
        tag_repo.create("remote", TagCategory.format)
        tag_repo.create("python", TagCategory.language)
        await session.commit()

        tokens = ["jobs", "remote", "#python", "unknown"]
        tags = await tag_repo.get_all()
        types, tag_ids, unknown = parse_tokens(tokens, tags)
        assert PublicationType.job in types
        assert len(tag_ids) == 2
        assert "unknown" in unknown

        result = await subscribe_tokens(session, tg_id=123, tokens=tokens)
        assert result["types"]
        # preferences saved
        prefs = await get_preferences(session, 123)
        assert TagCategory.format in prefs

        # Unsubscribe tags only
        out = await unsubscribe_tokens(session, 123, ["remote"])
        assert out["removed_tags"]

        # Full unsubscribe
        out = await unsubscribe_tokens(session, 123, [])
        assert "all" in out["removed_types"]


@pytest.mark.asyncio
async def test_search_publications():
    engine, Session = make_session()
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async with Session() as session:
        tag_repo = TagRepository(session)
        t = tag_repo.create("python", TagCategory.language)
        await session.commit()
        pub = models.Publication(
            id=uuid4(),
            title="Py Dev",
            description="",
            type=PublicationType.job,
            company="Co",
            url="u",
            created_at=datetime.datetime.utcnow(),
            vacancy_created_at=datetime.datetime.utcnow(),
            status="new",
        )
        session.add(pub)
        session.add(models.PublicationTag(publication_id=pub.id, tag_id=t.id))
        await session.commit()

        pubs = await search_publications(session, PublicationType.job, ["python"])
        assert len(pubs) == 1


def test_split_tokens():
    txt = "jobs  remote, #python"
    assert split_tokens(txt) == ["jobs", "remote", "#python"]


@pytest.mark.asyncio
async def test_block_user_clears_preferences_and_subscriptions():
    engine, Session = make_session()
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async with Session() as session:
        tag_repo = TagRepository(session)
        tag_repo.create("remote", TagCategory.format)
        await session.commit()

        # create subscriptions
        await subscribe_tokens(session, tg_id=321, tokens=["jobs", "remote"])
        prefs_before = await get_preferences(session, 321)
        assert prefs_before

        await block_user(session, 321)

        # verify user inactive and data removed
        user = (
            await session.execute(select(models.TgUser).where(models.TgUser.tg_id == 321))
        ).scalar_one()
        assert user.is_active is False
        prefs = await get_preferences(session, 321)
        assert prefs == {}
