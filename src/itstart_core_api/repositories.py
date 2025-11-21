from __future__ import annotations

from collections.abc import Iterable
from typing import Optional
import datetime
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    AdminUser,
    Parser,
    ParsingResult,
    Publication,
    PublicationTag,
    Tag,
    TgUser,
    TgUserSubscription,
    TgUserSubscriptionTag,
    UserPreference,
)


class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


class PublicationRepository(BaseRepository):
    async def get(self, pub_id: UUID) -> Optional[Publication]:
        result = await self.session.execute(select(Publication).where(Publication.id == pub_id))
        return result.scalar_one_or_none()

    async def list_recent(self, pub_type: str, limit: int = 10) -> list[Publication]:
        result = await self.session.execute(
            select(Publication).where(Publication.type == pub_type, Publication.is_declined == False)  # noqa: E712
            .order_by(Publication.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars())

    async def add_tags(self, pub_id: UUID, tag_ids: Iterable[UUID]) -> None:
        for tag_id in tag_ids:
            self.session.add(PublicationTag(publication_id=pub_id, tag_id=tag_id))


class TagRepository(BaseRepository):
    async def get_by_names(self, names: Iterable[str]) -> list[Tag]:
        result = await self.session.execute(select(Tag).where(Tag.name.in_(list(names))))
        return list(result.scalars())


class TgUserRepository(BaseRepository):
    async def get_by_tg_id(self, tg_id: int) -> Optional[TgUser]:
        result = await self.session.execute(select(TgUser).where(TgUser.tg_id == tg_id))
        return result.scalar_one_or_none()

    async def create_or_activate(self, tg_id: int, now) -> TgUser:
        user = await self.get_by_tg_id(tg_id)
        if user:
            user.is_active = True
            user.register_at = now
            user.refused_at = None
        else:
            user = TgUser(tg_id=tg_id, register_at=now, is_active=True)
            self.session.add(user)
        return user


class SubscriptionRepository(BaseRepository):
    async def upsert_subscription(self, user_id: UUID, pub_type: str, deadline_reminder: bool = True) -> TgUserSubscription:
        result = await self.session.execute(
            select(TgUserSubscription).where(
                TgUserSubscription.user_id == user_id,
                TgUserSubscription.publication_type == pub_type,
            )
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.deadline_reminder = deadline_reminder
            return sub
        sub = TgUserSubscription(user_id=user_id, publication_type=pub_type, deadline_reminder=deadline_reminder)
        self.session.add(sub)
        return sub

    async def add_tags(self, subscription_id: UUID, tag_ids: Iterable[UUID]) -> None:
        for tag_id in tag_ids:
            self.session.add(TgUserSubscriptionTag(subscription_id=subscription_id, tag_id=tag_id))


class UserPreferenceRepository(BaseRepository):
    async def add(self, user_id: UUID, tag_ids: Iterable[UUID]) -> None:
        for tag_id in tag_ids:
            self.session.add(UserPreference(user_id=user_id, tag_id=tag_id))


class AdminUserRepository(BaseRepository):
    def base_query(self):
        return select(AdminUser)

    async def get_by_username(self, username: str) -> Optional[AdminUser]:
        result = await self.session.execute(select(AdminUser).where(AdminUser.username == username))
        return result.scalar_one_or_none()

    async def get(self, user_id: UUID) -> Optional[AdminUser]:
        return await self.session.get(AdminUser, user_id)

    def create(self, username: str, password_hash: str, role: AdminRole, is_active: bool = True) -> AdminUser:
        user = AdminUser(username=username, password_hash=password_hash, role=role, is_active=is_active, created_at=datetime.datetime.utcnow())
        self.session.add(user)
        return user


class ParserRepository(BaseRepository):
    async def list_active(self) -> list[Parser]:
        result = await self.session.execute(select(Parser).where(Parser.is_active == True))  # noqa: E712
        return list(result.scalars())
