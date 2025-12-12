from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from itstart_domain import AdminRole, ParserType, PublicationType, TagCategory


class Model(BaseModel):
    model_config = {"from_attributes": True}


class TagRead(Model):
    id: UUID
    name: str
    category: TagCategory


class PublicationRead(Model):
    id: UUID
    title: str
    description: str
    type: PublicationType
    company: str
    url: str
    created_at: datetime
    vacancy_created_at: datetime
    updated_at: datetime | None = None
    is_edited: bool
    is_declined: bool
    deadline_at: datetime | None = None
    contact_info: str | None = None
    tags: list[TagRead] = Field(default_factory=list)
    status: str
    decline_reason: str | None = None
    editor_id: UUID | None = None


class PublicationCreate(BaseModel):
    title: str
    description: str
    type: PublicationType
    company: str
    url: str
    vacancy_created_at: datetime
    deadline_at: datetime | None = None
    contact_info: str | None = None
    tag_ids: list[UUID] = Field(default_factory=list)


class TgUserRead(Model):
    id: UUID
    tg_id: int
    register_at: datetime
    refused_at: datetime | None = None
    is_active: bool


class SubscriptionTagRead(Model):
    tag_id: UUID


class SubscriptionRead(Model):
    id: UUID
    user_id: UUID
    publication_type: PublicationType
    deadline_reminder: bool
    tags: list[SubscriptionTagRead] = Field(default_factory=list)


class UserPreferenceRead(Model):
    user_id: UUID
    tag_id: UUID


class ParserRead(Model):
    id: UUID
    source_name: str
    executable_file_path: str
    type: ParserType
    parsing_interval: int
    parsing_start_time: datetime
    last_parsed_at: datetime | None = None
    is_active: bool


class ParsingResultRead(Model):
    id: UUID
    date: datetime
    parser_id: UUID
    success: bool
    received_amount: int


class PublicationScheduleRead(Model):
    id: UUID
    publication_type: PublicationType
    interval_minutes: int
    start_time: datetime | None
    is_active: bool
    updated_at: datetime


class PublicationScheduleUpdate(BaseModel):
    job_interval_minutes: int | None = None
    internship_interval_minutes: int | None = None
    conference_interval_minutes: int | None = None
    contest_interval_minutes: int | None = None


class AdminUserRead(Model):
    id: UUID
    username: str
    role: AdminRole
    is_active: bool
    created_at: datetime


class AdminUserCreateResponse(BaseModel):
    user: AdminUserRead
    temporary_password: str
