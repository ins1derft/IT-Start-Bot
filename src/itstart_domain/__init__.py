"""Shared domain models and enums used by both core API and Telegram bot."""

from .models import (
    AdminRole,
    AdminUser,
    Parser,
    ParserType,
    ParsingResult,
    Publication,
    PublicationType,
    Tag,
    TagCategory,
    TgUser,
    TgUserSubscription,
    TgUserSubscriptionTag,
    UserPreference,
)

__all__ = [
    "AdminRole",
    "AdminUser",
    "Parser",
    "ParserType",
    "ParsingResult",
    "Publication",
    "PublicationType",
    "Tag",
    "TagCategory",
    "TgUser",
    "TgUserSubscription",
    "TgUserSubscriptionTag",
    "UserPreference",
]
