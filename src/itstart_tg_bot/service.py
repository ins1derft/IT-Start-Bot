from __future__ import annotations

import datetime
from typing import Iterable, Tuple
from uuid import UUID

from itstart_domain import PublicationType, TagCategory
from itstart_core_api import models
from itstart_core_api.repositories import (
    TgUserRepository,
    SubscriptionRepository,
    UserPreferenceRepository,
    TagRepository,
    PublicationRepository,
)


def split_tokens(text: str) -> list[str]:
    return [t.strip().lower() for t in text.replace(",", " ").split() if t.strip()]


def parse_tokens(tokens: Iterable[str], tags: list) -> tuple[list[PublicationType], list[UUID], list[str]]:
    pub_types = []
    tag_ids = []
    unknown = []
    tag_lookup = {t.name.lower(): t.id for t in tags}
    for token in tokens:
        if token in ("jobs", "job"):
            pub_types.append(PublicationType.job)
        elif token in ("internships", "internship"):
            pub_types.append(PublicationType.internship)
        elif token in ("conferences", "conference"):
            pub_types.append(PublicationType.conference)
        elif token.startswith("#"):
            token = token[1:]
            tid = tag_lookup.get(token.lower())
            if tid:
                tag_ids.append(tid)
            else:
                unknown.append(token)
        else:
            tid = tag_lookup.get(token.lower())
            if tid:
                tag_ids.append(tid)
            else:
                unknown.append(token)
    return list(set(pub_types)), list(set(tag_ids)), unknown


async def ensure_user(session, tg_id: int):
    user_repo = TgUserRepository(session)
    now = datetime.datetime.utcnow()
    return await user_repo.create_or_activate(tg_id, now)


async def subscribe_tokens(session, tg_id: int, tokens: Iterable[str]):
    tag_repo = TagRepository(session)
    tags = await tag_repo.get_all()
    pub_types, tag_ids, unknown = parse_tokens(tokens, tags)

    user = await ensure_user(session, tg_id)
    await session.flush()  # ensure user.id is available

    sub_repo = SubscriptionRepository(session)
    pref_repo = UserPreferenceRepository(session)

    # If no pub_types specified, default to jobs
    target_types = pub_types or [PublicationType.job]

    for ptype in target_types:
        sub = await sub_repo.upsert_subscription(user.id, ptype)
        await session.flush()
        await sub_repo.add_tags(sub.id, tag_ids)

    await pref_repo.add(user.id, tag_ids)
    await session.commit()
    return {"types": target_types, "tags": tag_ids, "unknown": unknown}


async def unsubscribe_tokens(session, tg_id: int, tokens: Iterable[str]):
    tag_repo = TagRepository(session)
    tags = await tag_repo.get_all()
    pub_types, tag_ids, unknown = parse_tokens(tokens, tags)

    user_repo = TgUserRepository(session)
    user = await user_repo.get_by_tg_id(tg_id)
    if not user:
        return {"removed_types": [], "removed_tags": [], "unknown": tokens}

    if not tokens:
        # full unsubscribe
        user.is_active = False
        user.refused_at = datetime.datetime.utcnow()
        # Clearing preferences/subscriptions would require cascading; simplest is to mark inactive.
        await session.commit()
        return {"removed_types": ["all"], "removed_tags": ["all"], "unknown": []}

    # partial remove tags from subscriptions and preferences
    removed_types = []
    removed_tags = []

    if pub_types:
        # simplistic: deactivate matching subscriptions
        for ptype in pub_types:
            result = await session.execute(
                SubscriptionRepository(session)
                .base_query()
                .where(SubscriptionRepository(session).model.user_id == user.id)
            )
        removed_types = pub_types

    if tag_ids:
        # delete from user_preferences
        await session.execute(
            UserPreferenceRepository(session).model.__table__.delete().where(
                UserPreferenceRepository(session).model.user_id == user.id,
                UserPreferenceRepository(session).model.tag_id.in_(tag_ids),
            )
        )
        removed_tags = tag_ids

    await session.commit()
    return {"removed_types": removed_types, "removed_tags": removed_tags, "unknown": unknown}


async def get_preferences(session, tg_id: int):
    user_repo = TgUserRepository(session)
    user = await user_repo.get_by_tg_id(tg_id)
    if not user:
        return {}
    q = (
        TagRepository(session)
        .base_query()
        .join(UserPreferenceRepository(session).model, UserPreferenceRepository(session).model.tag_id == TagRepository(session).model.id)
        .where(UserPreferenceRepository(session).model.user_id == user.id)
    )
    rows = (await session.execute(q)).scalars().all()
    grouped = {}
    for t in rows:
        grouped.setdefault(t.category, []).append(t.name)
    return grouped


async def search_publications(session, pub_type: PublicationType, tokens: Iterable[str]):
    tag_repo = TagRepository(session)
    tags = await tag_repo.get_all()
    _, tag_ids, _ = parse_tokens(tokens, tags)
    repo = PublicationRepository(session)
    q = repo.base_query().where(repo.model.type == pub_type, repo.model.is_declined == False)  # noqa: E712
    if tag_ids:
        q = q.join(models.PublicationTag, models.PublicationTag.publication_id == repo.model.id).where(models.PublicationTag.tag_id.in_(tag_ids))
    q = q.order_by(repo.model.created_at.desc()).limit(10)
    result = await session.execute(q)
    return list(result.scalars())


async def block_user(session, tg_id: int) -> bool:
    """Mark user as refused and clear preferences/subscriptions"""
    user_repo = TgUserRepository(session)
    user = await user_repo.get_by_tg_id(tg_id)
    if not user:
        return False

    user.is_active = False
    user.refused_at = datetime.datetime.utcnow()

    await session.execute(UserPreferenceRepository(session).model.__table__.delete().where(UserPreferenceRepository(session).model.user_id == user.id))
    await session.execute(SubscriptionRepository(session).model.__table__.delete().where(SubscriptionRepository(session).model.user_id == user.id))
    await session.commit()
    return True
