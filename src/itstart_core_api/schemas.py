from __future__ import annotations

from datetime import datetime
from typing import List, Optional
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
    updated_at: Optional[datetime] = None
    is_edited: bool
    is_declined: bool
    deadline_at: Optional[datetime] = None
    contact_info: Optional[str] = None
    tags: List[TagRead] = Field(default_factory=list)


class TgUserRead(Model):
    id: UUID
    tg_id: int
    register_at: datetime
    refused_at: Optional[datetime] = None
    is_active: bool


class SubscriptionTagRead(Model):
    tag_id: UUID


class SubscriptionRead(Model):
    id: UUID
    user_id: UUID
    publication_type: PublicationType
    deadline_reminder: bool
    tags: List[SubscriptionTagRead] = Field(default_factory=list)


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
    last_parsed_at: Optional[datetime] = None
    is_active: bool


class ParsingResultRead(Model):
    id: UUID
    date: datetime
    parser_id: UUID
    success: bool
    received_amount: int


class AdminUserRead(Model):
    id: UUID
    username: str
    role: AdminRole
    is_active: bool
    created_at: datetime
