from __future__ import annotations

import logging
import time

from fastapi import HTTPException, status
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """Simple per-key sliding window limiter (seconds, max hits)."""

    def __init__(self, window_seconds: int, max_hits: int):
        self.window = window_seconds
        self.max_hits = max_hits
        self.storage: dict[str, list[float]] = {}

    async def check(self, key: str) -> None:
        now = time.time()
        window_start = now - self.window
        hits = self.storage.get(key, [])
        hits = [h for h in hits if h >= window_start]
        if len(hits) >= self.max_hits:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
            )
        hits.append(now)
        self.storage[key] = hits


class RedisRateLimiter:
    """Distributed rate limiter using Redis sorted sets."""

    def __init__(
        self,
        redis_url: str,
        window_seconds: int,
        max_hits: int,
        prefix: str = "rate",
    ):
        self.redis_url = redis_url
        self.window = window_seconds
        self.max_hits = max_hits
        self.prefix = prefix
        self._redis: aioredis.Redis | None = None

    def _client(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=False
            )
        return self._redis

    async def check(self, key: str) -> None:
        now_ms = int(time.time() * 1000)
        window_start = now_ms - self.window * 1000
        redis_key = f"{self.prefix}:{key}"
        try:
            client = self._client()
            pipe = client.pipeline()
            pipe.zremrangebyscore(redis_key, 0, window_start)
            pipe.zadd(redis_key, {str(now_ms): now_ms})
            pipe.zcard(redis_key)
            pipe.expire(redis_key, self.window)
            _, _, count, _ = await pipe.execute()
        except Exception:
            logger.exception("Redis rate limiter failed; allowing request", extra={"key": key})
            return

        if count > self.max_hits:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
            )
