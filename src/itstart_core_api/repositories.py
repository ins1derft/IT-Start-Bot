from __future__ import annotations

import datetime
from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from itstart_domain import AdminRole, ParserType, PublicationType, TagCategory

from .models import (
    AdminAuditLog,
    AdminUser,
    Parser,
    Publication,
    PublicationSchedule,
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
    model = Publication

    async def get(self, pub_id: UUID) -> Publication | None:
        result = await self.session.execute(select(Publication).where(Publication.id == pub_id))
        return result.scalar_one_or_none()

    async def exists_duplicate(
        self,
        *,
        url: str,
        title: str,
        company: str,
        vacancy_created_at: datetime.datetime | None = None,
    ) -> bool:
        q = select(Publication).where(Publication.url == url)
        if vacancy_created_at is not None:
            q = q.union_all(
                select(Publication).where(
                    and_(
                        Publication.title == title,
                        Publication.company == company,
                        Publication.vacancy_created_at == vacancy_created_at,
                    )
                )
            )
        result = await self.session.execute(q.limit(1))
        return result.scalar_one_or_none() is not None

    async def list_recent(self, pub_type: PublicationType, limit: int = 10) -> list[Publication]:
        result = await self.session.execute(
            select(Publication)
            .where(and_(Publication.type == pub_type, Publication.is_declined.is_(False)))
            .order_by(Publication.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars())

    def base_query(self):
        return select(Publication)

    async def add_tags(self, pub_id: UUID, tag_ids: Iterable[UUID]) -> None:
        for tag_id in tag_ids:
            self.session.add(PublicationTag(publication_id=pub_id, tag_id=tag_id))


class TagRepository(BaseRepository):
    model = Tag

    def base_query(self):
        return select(Tag)

    async def get_by_ids(self, ids: Iterable[UUID]) -> list[Tag]:
        result = await self.session.execute(select(Tag).where(Tag.id.in_(list(ids))))
        return list(result.scalars())

    async def get_by_names(self, names: Iterable[str]) -> list[Tag]:
        result = await self.session.execute(select(Tag).where(Tag.name.in_(list(names))))
        return list(result.scalars())

    async def get_by_name_category(self, name: str, category: TagCategory) -> Tag | None:
        result = await self.session.execute(
            select(Tag).where(and_(Tag.name == name, Tag.category == category))
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Tag]:
        res = await self.session.execute(select(Tag))
        return list(res.scalars())

    def create(self, name: str, category: TagCategory | str) -> Tag:
        tag = Tag(name=name, category=category)
        self.session.add(tag)
        return tag


class TgUserRepository(BaseRepository):
    async def get_by_tg_id(self, tg_id: int) -> TgUser | None:
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
    model = TgUserSubscription

    async def upsert_subscription(
        self, user_id: UUID, pub_type: PublicationType, deadline_reminder: bool = True
    ) -> TgUserSubscription:
        result = await self.session.execute(
            select(TgUserSubscription).where(
                and_(
                    TgUserSubscription.user_id == user_id,
                    TgUserSubscription.publication_type == pub_type,
                )
            )
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.deadline_reminder = deadline_reminder
            return sub
        sub = TgUserSubscription(
            user_id=user_id, publication_type=pub_type, deadline_reminder=deadline_reminder
        )
        self.session.add(sub)
        return sub

    async def add_tags(self, subscription_id: UUID, tag_ids: Iterable[UUID]) -> None:
        for tag_id in tag_ids:
            self.session.add(TgUserSubscriptionTag(subscription_id=subscription_id, tag_id=tag_id))


class UserPreferenceRepository(BaseRepository):
    model = UserPreference

    async def add(self, user_id: UUID, tag_ids: Iterable[UUID]) -> None:
        for tag_id in tag_ids:
            self.session.add(UserPreference(user_id=user_id, tag_id=tag_id))


class AdminUserRepository(BaseRepository):
    def base_query(self):
        return select(AdminUser)

    async def get_by_username(self, username: str) -> AdminUser | None:
        result = await self.session.execute(select(AdminUser).where(AdminUser.username == username))
        return result.scalar_one_or_none()

    async def get(self, user_id: UUID) -> AdminUser | None:
        return await self.session.get(AdminUser, user_id)

    def create(
        self, username: str, password_hash: str, role: AdminRole, is_active: bool = True
    ) -> AdminUser:
        user = AdminUser(
            username=username,
            password_hash=password_hash,
            role=role,
            is_active=is_active,
            created_at=datetime.datetime.utcnow(),
        )
        self.session.add(user)
        return user

    async def patch(
        self,
        user: AdminUser,
        *,
        role: AdminRole | None = None,
        is_active: bool | None = None,
        password_hash: str | None = None,
    ) -> AdminUser:
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        if password_hash is not None:
            user.password_hash = password_hash
        return user


class AdminAuditRepository(BaseRepository):
    def log(
        self,
        admin_id: UUID,
        action: str,
        target_type: str,
        target_id: UUID | None,
        details: str | None = None,
    ) -> AdminAuditLog:
        entry = AdminAuditLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
        )
        self.session.add(entry)
        return entry

    def create(
        self, username: str, password_hash: str, role: AdminRole, is_active: bool = True
    ) -> AdminUser:
        user = AdminUser(
            username=username,
            password_hash=password_hash,
            role=role,
            is_active=is_active,
            created_at=datetime.datetime.utcnow(),
        )
        self.session.add(user)
        return user


class ParserRepository(BaseRepository):
    async def list_active(self) -> list[Parser]:
        result = await self.session.execute(select(Parser).where(Parser.is_active.is_(True)))
        return list(result.scalars())

    def base_query(self):
        return select(Parser)

    async def get(self, parser_id: UUID) -> Parser | None:
        return await self.session.get(Parser, parser_id)

    def create(
        self,
        source_name: str,
        executable_file_path: str,
        type: ParserType,
        parsing_interval: int,
        parsing_start_time: datetime.datetime,
        is_active: bool = True,
    ) -> Parser:
        parser = Parser(
            source_name=source_name,
            executable_file_path=executable_file_path,
            type=type,
            parsing_interval=parsing_interval,
            parsing_start_time=parsing_start_time,
            is_active=is_active,
        )
        self.session.add(parser)
        return parser

    async def update(
        self,
        parser: Parser,
        *,
        source_name: str | None = None,
        executable_file_path: str | None = None,
        type: ParserType | None = None,
        parsing_interval: int | None = None,
        parsing_start_time: datetime.datetime | None = None,
        is_active: bool | None = None,
    ) -> Parser:
        if source_name is not None:
            parser.source_name = source_name
        if executable_file_path is not None:
            parser.executable_file_path = executable_file_path
        if type is not None:
            parser.type = type
        if parsing_interval is not None:
            parser.parsing_interval = parsing_interval
        if parsing_start_time is not None:
            parser.parsing_start_time = parsing_start_time
        if is_active is not None:
            parser.is_active = is_active
        return parser


class PublicationScheduleRepository(BaseRepository):
    model = PublicationSchedule

    def base_query(self):
        return select(PublicationSchedule)

    async def get_by_type(
        self, publication_type: PublicationType | str
    ) -> PublicationSchedule | None:
        result = await self.session.execute(
            select(PublicationSchedule).where(
                PublicationSchedule.publication_type == publication_type
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        publication_type: PublicationType | str,
        interval_minutes: int,
        start_time: datetime.datetime | None = None,
        is_active: bool = True,
    ) -> PublicationSchedule:
        existing = await self.get_by_type(publication_type)
        if existing:
            existing.interval_minutes = interval_minutes
            existing.start_time = start_time
            existing.is_active = is_active
            return existing
        schedule = PublicationSchedule(
            publication_type=publication_type,
            interval_minutes=interval_minutes,
            start_time=start_time,
            is_active=is_active,
        )
        self.session.add(schedule)
        return schedule
