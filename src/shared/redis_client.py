from __future__ import annotations

from typing import Optional

from redis import Redis

from .config import settings


_client: Optional[Redis] = None


def get_redis() -> Redis:
    global _client
    if _client is None:
        _client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


