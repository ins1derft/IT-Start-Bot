from __future__ import annotations

import time
from typing import Dict, Tuple

from fastapi import HTTPException, status


class InMemoryRateLimiter:
    """Simple per-key sliding window limiter (seconds, max hits)."""

    def __init__(self, window_seconds: int, max_hits: int):
        self.window = window_seconds
        self.max_hits = max_hits
        self.storage: Dict[str, list[float]] = {}

    def check(self, key: str) -> None:
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
