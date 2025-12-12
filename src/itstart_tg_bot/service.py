from __future__ import annotations

import datetime
import json
from collections.abc import Iterable
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy import delete, func

from itstart_core_api import models
from itstart_core_api.repositories import (
    PublicationRepository,
    SubscriptionRepository,
    TagRepository,
    TgUserRepository,
    UserPreferenceRepository,
)
from itstart_domain import PublicationType

from .config import get_settings


def split_tokens(text: str) -> list[str]:
    return [t.strip().lower() for t in text.replace(",", " ").split() if t.strip()]


def parse_tokens(
    tokens: Iterable[str], tags: list
) -> tuple[list[PublicationType], list[UUID], list[str]]:
    pub_types: list[PublicationType] = []
    tag_ids: list[UUID] = []
    unknown: list[str] = []
    tag_lookup = {t.name.lower(): t.id for t in tags}
    for token in tokens:
        if token in ("jobs", "job"):
            pub_types.append(PublicationType.job)
        elif token in ("internships", "internship"):
            pub_types.append(PublicationType.internship)
        elif token in ("conferences", "conference"):
            pub_types.append(PublicationType.conference)
        elif token in ("contests", "contest", "hackathon", "hackathons", "хакатон", "хакатоны"):
            pub_types.append(PublicationType.contest)
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

    if not pub_types:
        raise ValueError("Укажите тип публикаций: jobs, internships или conferences.")

    target_types = pub_types

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
        await session.execute(
            delete(SubscriptionRepository(session).model).where(
                SubscriptionRepository(session).model.user_id == user.id,
                SubscriptionRepository(session).model.publication_type.in_(pub_types),
            )
        )
        removed_types = pub_types

    if tag_ids:
        # delete from user_preferences
        await session.execute(
            delete(UserPreferenceRepository(session).model).where(
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
        .join(
            UserPreferenceRepository(session).model,
            UserPreferenceRepository(session).model.tag_id == TagRepository(session).model.id,
        )
        .where(UserPreferenceRepository(session).model.user_id == user.id)
    )
    rows = (await session.execute(q)).scalars().all()
    grouped: dict[models.TagCategory, list[str]] = {}
    for t in rows:
        grouped.setdefault(t.category, []).append(t.name)
    return grouped


async def search_publications(session, pub_type: PublicationType, tokens: Iterable[str]):
    tag_repo = TagRepository(session)
    tags = await tag_repo.get_all()
    _, tag_ids, _ = parse_tokens(tokens, tags)

    cache_key = None
    cache_client = None
    try:
        cache_client = redis.from_url(get_settings().redis_url, decode_responses=True)
        cache_key = f"search:{pub_type}:{'-'.join(sorted([str(t) for t in tag_ids]))}"
        if cache_client:
            cached = await cache_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                # Return lightweight dicts to avoid ORM session issues
                return data
    except Exception:
        cache_client = None

    repo = PublicationRepository(session)
    base_filters = [repo.model.type == pub_type, repo.model.is_declined.is_(False)]

    q = repo.base_query().where(*base_filters)

    if tag_ids:
        # Require all specified tags to be present on the publication
        q = (
            q.join(models.PublicationTag, models.PublicationTag.publication_id == repo.model.id)
            .where(models.PublicationTag.tag_id.in_(tag_ids))
            .group_by(repo.model.id)
            .having(func.count(func.distinct(models.PublicationTag.tag_id)) == len(tag_ids))
        )

    result = await session.execute(q.order_by(repo.model.created_at.desc()).limit(10))
    pubs = list(result.scalars())

    if cache_client and cache_key:
        try:
            await cache_client.set(
                cache_key,
                json.dumps([{"title": p.title, "company": p.company, "url": p.url} for p in pubs]),
                ex=300,
            )
        except Exception:
            pass
    return pubs


async def block_user(session, tg_id: int) -> bool:
    """Mark user as refused and clear preferences/subscriptions"""
    user_repo = TgUserRepository(session)
    user = await user_repo.get_by_tg_id(tg_id)
    if not user:
        return False

    user.is_active = False
    user.refused_at = datetime.datetime.utcnow()

    await session.execute(
        delete(UserPreferenceRepository(session).model).where(
            UserPreferenceRepository(session).model.user_id == user.id
        )
    )
    await session.execute(
        delete(SubscriptionRepository(session).model).where(
            SubscriptionRepository(session).model.user_id == user.id
        )
    )
    await session.commit()
    return True
