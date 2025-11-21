import pytest
from fastapi import HTTPException
from itstart_core_api.rate_limiter import InMemoryRateLimiter


def test_rate_limiter_allows_within_limits():
    limiter = InMemoryRateLimiter(window_seconds=60, max_hits=2)
    limiter.check("user")
    limiter.check("user")  # second should pass


def test_rate_limiter_blocks_excess():
    limiter = InMemoryRateLimiter(window_seconds=60, max_hits=1)
    limiter.check("user")
    with pytest.raises(HTTPException) as exc:
        limiter.check("user")
    assert exc.value.status_code == 429
