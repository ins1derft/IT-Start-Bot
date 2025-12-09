import pytest
from fastapi import HTTPException

from itstart_core_api.rate_limiter import InMemoryRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_within_limits():
    limiter = InMemoryRateLimiter(window_seconds=60, max_hits=2)
    await limiter.check("user")
    await limiter.check("user")  # second should pass


@pytest.mark.asyncio
async def test_rate_limiter_blocks_excess():
    limiter = InMemoryRateLimiter(window_seconds=60, max_hits=1)
    await limiter.check("user")
    with pytest.raises(HTTPException) as exc:
        await limiter.check("user")
    assert exc.value.status_code == 429
