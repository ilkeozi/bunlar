from __future__ import annotations

import os
from functools import lru_cache

try:
    import redis
except Exception:  # pragma: no cover
    redis = None

@lru_cache(maxsize=1)
def _get_redis_client() -> object | None:
    if redis is None:
        return None
    redis_url = str(os.getenv("MATERIAL_INGESTION_REDIS_URL", "redis://localhost:6379/0")).strip()
    if not redis_url:
        return None
    try:
        client = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=0.5,
            socket_connect_timeout=0.5,
        )
        client.ping()
        return client
    except Exception:
        return None


def cache_get(key: str) -> str | None:
    client = _get_redis_client()
    if client is None:
        return None
    try:
        value = client.get(str(key))
    except Exception:
        return None
    if value is None:
        return None
    return str(value)


def cache_setex(key: str, ttl_seconds: int, value: str) -> bool:
    client = _get_redis_client()
    if client is None:
        return False
    try:
        client.setex(str(key), max(1, int(ttl_seconds)), str(value))
        return True
    except Exception:
        return False
