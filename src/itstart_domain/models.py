from __future__ import annotations

from datetime import datetime

try:  # Python 3.11+
    from enum import StrEnum
except ImportError:  # Python 3.10 fallback
    from enum import Enum

    class StrEnum(str, Enum):  # type: ignore
        pass


from collections.abc import Sequence
from uuid import UUID

from pydantic import BaseModel, Field


class PublicationType(StrEnum):
    job = "job"
    internship = "internship"
    conference = "conference"


class TagCategory(StrEnum):
    format = "format"
    occupation = "occupation"
    platform = "platform"
    language = "language"
    location = "location"
    technology = "technology"
    duration = "duration"


class Tag(BaseModel):
    id: UUID
    name: str
    category: TagCategory

    model_config = {"frozen": True}


class Publication(BaseModel):
    id: UUID
    title: str
    description: str
    type: PublicationType
    company: str
    url: str
    source_id: UUID | None = None
    created_at: datetime
    vacancy_created_at: datetime
    updated_at: datetime | None = None
    editor_id: UUID | None = None
    is_edited: bool = False
    is_declined: bool = False
    deadline_at: datetime | None = None
    contact_info: str | None = None
    contact_info_encrypted: bytes | None = None
    tags: Sequence[Tag] = Field(default_factory=tuple)
    status: str = "new"
    decline_reason: str | None = None


class TgUser(BaseModel):
    id: UUID
    tg_id: int
    register_at: datetime
    refused_at: datetime | None = None
    is_active: bool = True


class TgUserSubscription(BaseModel):
    id: UUID
    user_id: UUID
    publication_type: PublicationType
    deadline_reminder: bool = True


class TgUserSubscriptionTag(BaseModel):
    subscription_id: UUID
    tag_id: UUID


class Parser(BaseModel):
    id: UUID
    source_name: str
    executable_file_path: str
    type: ParserType
    parsing_interval: int
    parsing_start_time: datetime
    last_parsed_at: datetime | None = None
    is_active: bool = True


class ParsingResult(BaseModel):
    id: UUID
    date: datetime
    parser_id: UUID
    success: bool
    received_amount: int


class AdminRole(StrEnum):
    admin = "admin"
    moderator = "moderator"


class AdminUser(BaseModel):
    id: UUID
    username: str
    password_hash: str
    role: AdminRole
    is_active: bool = True
    otp_secret: str | None = None
    created_at: datetime | None = None


class UserPreference(BaseModel):
    user_id: UUID
    tag_id: UUID


class ParserType(StrEnum):
    api_client = "api_client"
    website_parser = "website_parser"
    tg_channel_parser = "tg_channel_parser"
