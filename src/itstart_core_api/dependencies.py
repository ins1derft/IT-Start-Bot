from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

# Placeholder for future async session/clients wiring.
@asynccontextmanager
async def lifespan_context() -> AsyncIterator[None]:
    yield
