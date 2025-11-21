from __future__ import annotations

from itstart_common.db import create_engine, create_session_maker
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from .config import Settings


def build_engine(settings: Settings) -> AsyncEngine:
    return create_engine(settings.database_url)


def build_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return create_session_maker(engine)
