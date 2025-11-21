from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, Index, LargeBinary, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from itstart_domain import AdminRole, ParserType, PublicationType, TagCategory


class Base(DeclarativeBase):
    pass


def uuid_pk() -> Mapped[UUID]:
    return mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)


class Publication(Base):
    __tablename__ = "publication"

    id: Mapped[UUID] = uuid_pk()
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[PublicationType] = mapped_column(
        Enum(PublicationType, name="publication_type"), nullable=False
    )
    company: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    source_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    vacancy_created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime | None]
    editor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    is_edited: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_declined: Mapped[bool] = mapped_column(default=False, nullable=False)
    deadline_at: Mapped[datetime | None]
    contact_info: Mapped[str | None]
    contact_info_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    deadline_notified: Mapped[bool] = mapped_column(default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("new", "declined", "ready", "sent", name="publication_status"),
        nullable=False,
        default="new",
    )
    decline_reason: Mapped[str | None]

    tags: Mapped[list[PublicationTag]] = relationship(
        cascade="all, delete-orphan", back_populates="publication"
    )


class Tag(Base):
    __tablename__ = "tag"
    __table_args__ = (UniqueConstraint("name", "category", name="uq_tag_name_category"),)

    id: Mapped[UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[TagCategory] = mapped_column(Enum(TagCategory, name="tag_category"))

    publications: Mapped[list[PublicationTag]] = relationship(
        cascade="all, delete-orphan", back_populates="tag"
    )


class PublicationTag(Base):
    __tablename__ = "publication_tags"

    publication_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("publication.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True
    )

    publication: Mapped[Publication] = relationship(back_populates="tags")
    tag: Mapped[Tag] = relationship(back_populates="publications")


class TgUser(Base):
    __tablename__ = "tg_user"
    __table_args__ = (UniqueConstraint("tg_id", name="uq_tg_user_tg_id"),)

    id: Mapped[UUID] = uuid_pk()
    tg_id: Mapped[int] = mapped_column(nullable=False)
    register_at: Mapped[datetime] = mapped_column(nullable=False)
    refused_at: Mapped[datetime | None]
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    subscriptions: Mapped[list[TgUserSubscription]] = relationship(
        cascade="all, delete-orphan", back_populates="user"
    )
    preferences: Mapped[list[UserPreference]] = relationship(
        cascade="all, delete-orphan", back_populates="user"
    )


class TgUserSubscription(Base):
    __tablename__ = "tg_user_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "publication_type", name="uq_sub_user_type"),)

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tg_user.id", ondelete="CASCADE"), nullable=False
    )
    publication_type: Mapped[PublicationType] = mapped_column(
        Enum(PublicationType, name="publication_type"), nullable=False
    )
    deadline_reminder: Mapped[bool] = mapped_column(default=True, nullable=False)

    user: Mapped[TgUser] = relationship(back_populates="subscriptions")
    tags: Mapped[list[TgUserSubscriptionTag]] = relationship(
        cascade="all, delete-orphan", back_populates="subscription"
    )


class TgUserSubscriptionTag(Base):
    __tablename__ = "tg_user_subscription_tags"

    subscription_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tg_user_subscriptions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True
    )

    subscription: Mapped[TgUserSubscription] = relationship(back_populates="tags")
    tag: Mapped[Tag] = relationship()


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tg_user.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True
    )

    user: Mapped[TgUser] = relationship(back_populates="preferences")
    tag: Mapped[Tag] = relationship()


class PublicationSchedule(Base):
    __tablename__ = "publication_schedule"
    __table_args__ = (UniqueConstraint("publication_type", name="uq_publication_schedule_type"),)

    id: Mapped[UUID] = uuid_pk()
    publication_type: Mapped[PublicationType] = mapped_column(
        Enum(PublicationType, name="publication_type"), nullable=False
    )
    interval_minutes: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[datetime | None]
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Parser(Base):
    __tablename__ = "parser"

    id: Mapped[UUID] = uuid_pk()
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    executable_file_path: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[ParserType] = mapped_column(Enum(ParserType, name="parser_type"), nullable=False)
    parsing_interval: Mapped[int] = mapped_column(nullable=False)
    parsing_start_time: Mapped[datetime] = mapped_column(nullable=False)
    last_parsed_at: Mapped[datetime | None]
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    results: Mapped[list[ParsingResult]] = relationship(
        cascade="all, delete-orphan", back_populates="parser"
    )


class ParsingResult(Base):
    __tablename__ = "parsing_result"

    id: Mapped[UUID] = uuid_pk()
    date: Mapped[datetime] = mapped_column(nullable=False)
    parser_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("parser.id", ondelete="CASCADE"), nullable=False
    )
    success: Mapped[bool] = mapped_column(nullable=False)
    received_amount: Mapped[int] = mapped_column(nullable=False)

    parser: Mapped[Parser] = relationship(back_populates="results")


class AdminUser(Base):
    __tablename__ = "admin_user"
    __table_args__ = (UniqueConstraint("username", name="uq_admin_username"),)

    id: Mapped[UUID] = uuid_pk()
    username: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[AdminRole] = mapped_column(Enum(AdminRole, name="admin_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    otp_secret: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[UUID] = uuid_pk()
    admin_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)


Index("idx_publication_type_created_at", Publication.type, Publication.created_at.desc())
Index("idx_publication_tags_tag", PublicationTag.tag_id)
Index("idx_parsing_result_parser_date", ParsingResult.parser_id, ParsingResult.date)
Index("idx_tg_user_refused_at", TgUser.refused_at)
Index(
    "idx_tg_user_subscriptions_user_type",
    TgUserSubscription.user_id,
    TgUserSubscription.publication_type,
)
