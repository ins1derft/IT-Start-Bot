from __future__ import annotations

import asyncio
import datetime
import logging
import json
from typing import Iterable

import httpx
from sqlalchemy import select

from itstart_domain import PublicationType
from .config import get_settings
from .db import build_engine, build_session_maker
from .models import Publication, PublicationTag, Tag, TgUser, TgUserSubscription, TgUserSubscriptionTag
from .repositories import PublicationRepository

logger = logging.getLogger(__name__)


def _format_publication(pub: Publication, tags: list[str], updated: bool = False) -> str:
    prefix = "[UPD] " if updated else ""
    tag_str = " " + " ".join(f"#{t}" for t in tags) if tags else ""
    deadline = f"\nДедлайн: {pub.deadline_at.date()}" if getattr(pub, "deadline_at", None) else ""
    return f"{prefix}{pub.title} — {pub.company}\n{pub.url}{deadline}{tag_str}"


async def _send_telegram_message(token: str, chat_id: int | str, text: str) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            await client.post(url, json={"chat_id": chat_id, "text": text})
        except Exception:  # pragma: no cover - network failures are logged
            logger.exception("Failed to send Telegram message", extra={"chat_id": chat_id})


async def _collect_pub_tags(session, pub_id) -> list[str]:
    rows = await session.execute(
        select(Tag.name)
        .join(PublicationTag, PublicationTag.tag_id == Tag.id)
        .where(PublicationTag.publication_id == pub_id)
    )
    return [r[0] for r in rows.all()]


async def _eligible_subscriptions(session, pub: Publication) -> Iterable[tuple[TgUserSubscription, TgUser]]:
    # fetch publication tags once
    pub_tag_rows = await session.execute(
        PublicationTag.__table__.select().where(PublicationTag.publication_id == pub.id)
    )
    pub_tag_ids = {r.tag_id for r in pub_tag_rows}

    subs_result = await session.execute(
        select(TgUserSubscription, TgUser)
        .join(TgUser, TgUserSubscription.user_id == TgUser.id)
        .where(
            TgUserSubscription.publication_type == pub.type,
            TgUser.is_active == True,  # noqa: E712
        )
    )
    subs: list[tuple[TgUserSubscription, TgUser]] = []
    for sub, user in subs_result:
        # get tags for subscription
        tags_rows = await session.execute(
            TgUserSubscriptionTag.__table__.select().where(TgUserSubscriptionTag.subscription_id == sub.id)
        )
        required = {t.tag_id for t in tags_rows}
        if required and not required.issubset(pub_tag_ids):
            continue
        subs.append((sub, user))
    return subs


async def send_publications() -> None:
    """Send new/ready publications to channel and subscribers, mark as sent."""
    settings = get_settings()
    engine = build_engine(settings)
    Session = build_session_maker(engine)

    async with Session() as session:
        repo = PublicationRepository(session)
        res = await session.execute(
            repo.base_query().where(
                Publication.status.in_(["new", "ready"]),
                Publication.is_declined == False,  # noqa: E712
            )
        )
        pubs = list(res.scalars())

        for pub in pubs:
            tags = await _collect_pub_tags(session, pub.id)
            text = _format_publication(pub, tags, updated=getattr(pub, "is_edited", False))

            # send to channel if configured
            if settings.bot_token and getattr(settings, "bot_channel_id", None):
                await _send_telegram_message(settings.bot_token, settings.bot_channel_id, text)

            # send to subscribers
            subs = await _eligible_subscriptions(session, pub)
            for sub, user in subs:
                await _send_telegram_message(settings.bot_token, user.tg_id, text)

            pub.status = "sent"
            pub.updated_at = datetime.datetime.utcnow()
        await session.commit()


async def send_deadline_reminders() -> None:
    settings = get_settings()
    engine = build_engine(settings)
    Session = build_session_maker(engine)
    now = datetime.datetime.utcnow()
    target_from = now
    target_to = now + datetime.timedelta(days=3)

    async with Session() as session:
        res = await session.execute(
            select(Publication).where(
                Publication.deadline_at != None,  # noqa: E711
                Publication.deadline_at >= target_from,
                Publication.deadline_at <= target_to,
                Publication.is_declined == False,  # noqa: E712
                Publication.deadline_notified == False,  # noqa: E712
            )
        )
        pubs = list(res.scalars())
        for pub in pubs:
            subs = await _eligible_subscriptions(session, pub)
            tags = await _collect_pub_tags(session, pub.id)
            text = _format_publication(pub, tags, updated=False) + "\nНапоминание о дедлайне через 3 дня."
            for sub, user in subs:
                if getattr(sub, "deadline_reminder", True):
                    await _send_telegram_message(settings.bot_token, user.tg_id, text)
            pub.deadline_notified = True
        await session.commit()


async def cleanup_old_publications(days: int = 90) -> None:
    settings = get_settings()
    engine = build_engine(settings)
    Session = build_session_maker(engine)
    threshold = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    async with Session() as session:
        await session.execute(Publication.__table__.delete().where(Publication.created_at < threshold))
        await session.commit()
