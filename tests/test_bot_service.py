import datetime
import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from itstart_tg_bot.service import parse_tokens, subscribe_tokens, unsubscribe_tokens, get_preferences, search_publications, split_tokens
from itstart_core_api import models
from itstart_core_api.repositories import TagRepository
from itstart_domain import TagCategory, PublicationType


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
