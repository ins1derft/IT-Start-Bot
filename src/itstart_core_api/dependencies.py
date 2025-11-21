from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import build_engine, build_session_maker


def get_session_maker():
    settings = get_settings()
    engine = build_engine(settings)
    return build_session_maker(engine)


async def get_db_session(session_maker=Depends(get_session_maker)) -> AsyncIterator[AsyncSession]:
    async with session_maker() as session:
        yield session


@asynccontextmanager
async def lifespan_context() -> AsyncIterator[None]:
    yield
