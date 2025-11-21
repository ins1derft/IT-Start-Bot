from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

from itstart_domain import AdminRole, ParserType, PublicationType, TagCategory

Base = declarative_base()


class Publication(Base):
    __tablename__ = "publication"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    type = Column(Enum(PublicationType, name="publication_type"), nullable=False)
    company = Column(String(255), nullable=False)
    url = Column(Text, unique=True, nullable=False)
    source_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, nullable=False)
    vacancy_created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    editor_id = Column(UUID(as_uuid=True))
    is_edited = Column(Boolean, nullable=False, default=False)
    is_declined = Column(Boolean, nullable=False, default=False)
    deadline_at = Column(DateTime)
    contact_info = Column(Text)
    contact_info_encrypted = Column(LargeBinary)
    deadline_notified = Column(Boolean, nullable=False, default=False)
    status = Column(Enum("new", "declined", "ready", "sent", name="publication_status"), nullable=False, default="new")
    decline_reason = Column(Text)

    tags = relationship("PublicationTag", cascade="all, delete-orphan", back_populates="publication")


class Tag(Base):
    __tablename__ = "tag"
    __table_args__ = (UniqueConstraint("name", "category", name="uq_tag_name_category"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    category = Column(Enum(TagCategory, name="tag_category"), nullable=False)

    publications = relationship("PublicationTag", cascade="all, delete-orphan", back_populates="tag")


class PublicationTag(Base):
    __tablename__ = "publication_tags"

    publication_id = Column(
        UUID(as_uuid=True), ForeignKey("publication.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True)

    publication = relationship("Publication", back_populates="tags")
    tag = relationship("Tag", back_populates="publications")


class TgUser(Base):
    __tablename__ = "tg_user"
    __table_args__ = (UniqueConstraint("tg_id", name="uq_tg_user_tg_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tg_id = Column(Integer, nullable=False)
    register_at = Column(DateTime, nullable=False)
    refused_at = Column(DateTime)
    is_active = Column(Boolean, nullable=False, default=True)

    subscriptions = relationship(
        "TgUserSubscription", cascade="all, delete-orphan", back_populates="user"
    )
    preferences = relationship(
        "UserPreference", cascade="all, delete-orphan", back_populates="user"
    )


class TgUserSubscription(Base):
    __tablename__ = "tg_user_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "publication_type", name="uq_sub_user_type"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("tg_user.id", ondelete="CASCADE"), nullable=False)
    publication_type = Column(Enum(PublicationType, name="publication_type"), nullable=False)
    deadline_reminder = Column(Boolean, nullable=False, default=True)

    user = relationship("TgUser", back_populates="subscriptions")
    tags = relationship(
        "TgUserSubscriptionTag", cascade="all, delete-orphan", back_populates="subscription"
    )


class TgUserSubscriptionTag(Base):
    __tablename__ = "tg_user_subscription_tags"

    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tg_user_subscriptions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True)

    subscription = relationship("TgUserSubscription", back_populates="tags")
    tag = relationship("Tag")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("tg_user.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True)

    user = relationship("TgUser", back_populates="preferences")
    tag = relationship("Tag")


class PublicationSchedule(Base):
    __tablename__ = "publication_schedule"
    __table_args__ = (UniqueConstraint("publication_type", name="uq_publication_schedule_type"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    publication_type = Column(Enum(PublicationType, name="publication_type"), nullable=False)
    interval_minutes = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Parser(Base):
    __tablename__ = "parser"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_name = Column(String(255), nullable=False)
    executable_file_path = Column(Text, nullable=False)
    type = Column(Enum(ParserType, name="parser_type"), nullable=False)
    parsing_interval = Column(Integer, nullable=False)
    parsing_start_time = Column(DateTime, nullable=False)
    last_parsed_at = Column(DateTime)
    is_active = Column(Boolean, nullable=False, default=True)

    results = relationship("ParsingResult", cascade="all, delete-orphan", back_populates="parser")


class ParsingResult(Base):
    __tablename__ = "parsing_result"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    date = Column(DateTime, nullable=False)
    parser_id = Column(UUID(as_uuid=True), ForeignKey("parser.id", ondelete="CASCADE"), nullable=False)
    success = Column(Boolean, nullable=False)
    received_amount = Column(Integer, nullable=False)

    parser = relationship("Parser", back_populates="results")


class AdminUser(Base):
    __tablename__ = "admin_user"
    __table_args__ = (UniqueConstraint("username", name="uq_admin_username"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(255), nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(Enum(AdminRole, name="admin_role"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    otp_secret = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    admin_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(255), nullable=False)
    target_type = Column(String(255), nullable=False)
    target_id = Column(UUID(as_uuid=True))
    details = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# Indices mirroring schema
Index("idx_publication_type_created_at", Publication.type, Publication.created_at.desc())
Index("idx_publication_tags_tag", PublicationTag.tag_id)
Index("idx_parsing_result_parser_date", ParsingResult.parser_id, ParsingResult.date)
Index("idx_tg_user_refused_at", TgUser.refused_at)
Index("idx_tg_user_subscriptions_user_type", TgUserSubscription.user_id, TgUserSubscription.publication_type)
