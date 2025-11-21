from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(url: str) -> AsyncEngine:
    return create_async_engine(url, future=True, echo=False)


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def session_dependency(
    session_factory: async_sessionmaker[AsyncSession],
) -> Callable[[], AbstractAsyncContextManager[AsyncSession]]:
    @asynccontextmanager
    async def _get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    return _get_session
