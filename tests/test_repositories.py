import datetime

import pytest

from itstart_core_api import models
from itstart_core_api.repositories import (
    PublicationRepository,
    SubscriptionRepository,
    TgUserRepository,
    UserPreferenceRepository,
)
from itstart_domain import PublicationType, TagCategory


@pytest.mark.asyncio
async def test_user_create_or_activate(session):
    repo = TgUserRepository(session)
    now = datetime.datetime.utcnow()
    await repo.create_or_activate(123, now)
    await session.commit()

    fetched = await repo.get_by_tg_id(123)
    assert fetched is not None
    assert fetched.is_active
    assert fetched.register_at == now


@pytest.mark.asyncio
async def test_subscription_upsert_and_tags(session):
    user_repo = TgUserRepository(session)
    sub_repo = SubscriptionRepository(session)
    now = datetime.datetime.utcnow()
    user = await user_repo.create_or_activate(1, now)
    await session.commit()

    # create tags
    tag1 = models.Tag(name="python", category=TagCategory.language)
    tag2 = models.Tag(name="remote", category=TagCategory.format)
    session.add_all([tag1, tag2])
    await session.commit()

    sub = await sub_repo.upsert_subscription(user.id, PublicationType.job)
    await session.commit()

    await sub_repo.add_tags(sub.id, [tag1.id, tag2.id])
    await session.commit()

    result = await session.execute(
        models.TgUserSubscriptionTag.__table__.select().where(
            models.TgUserSubscriptionTag.subscription_id == sub.id
        )
    )
    rows = result.fetchall()
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_publication_recent(session):
    pub_repo = PublicationRepository(session)

    tag = models.Tag(name="ml", category=TagCategory.technology)
    session.add(tag)
    await session.commit()

    now = datetime.datetime.utcnow()
    pub = models.Publication(
        title="Test",
        description="Desc",
        type=PublicationType.job,
        company="Co",
        url="https://example.com",
        created_at=now,
        vacancy_created_at=now,
    )
    session.add(pub)
    await session.commit()

    latest = await pub_repo.list_recent(PublicationType.job, limit=5)
    assert latest
    assert latest[0].title == "Test"


@pytest.mark.asyncio
async def test_user_preferences(session):
    user_repo = TgUserRepository(session)
    pref_repo = UserPreferenceRepository(session)

    now = datetime.datetime.utcnow()
    user = await user_repo.create_or_activate(42, now)

    tag = models.Tag(name="data", category=TagCategory.technology)
    session.add(tag)
    await session.commit()

    await pref_repo.add(user.id, [tag.id])
    await session.commit()

    prefs = await session.execute(
        models.UserPreference.__table__.select().where(models.UserPreference.user_id == user.id)
    )
    rows = prefs.fetchall()
    assert len(rows) == 1
    assert rows[0].tag_id == tag.id
