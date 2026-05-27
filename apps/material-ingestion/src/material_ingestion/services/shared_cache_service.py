from __future__ import annotations

import os
import time
from functools import lru_cache

try:
    import redis
except Exception:  # pragma: no cover
    redis = None

# ---------------------------------------------------------------------------
# In-process TTL cache — lightweight key/value store with per-entry expiry.
# Uses monotonic time so it is not affected by wall-clock adjustments.
# Thread-safe for CPython: dict reads/writes are atomic under the GIL and we
# never do check-then-set on the same key from two threads simultaneously.
# ---------------------------------------------------------------------------

_local_ttl: dict[str, tuple[object, float]] = {}


def local_cache_get(key: str) -> object | None:
    entry = _local_ttl.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if time.monotonic() >= expires_at:
        _local_ttl.pop(key, None)
        return None
    return value


def local_cache_set(key: str, value: object, ttl_seconds: int) -> None:
    _local_ttl[key] = (value, time.monotonic() + max(1, int(ttl_seconds)))


def local_cache_delete(key: str) -> None:
    _local_ttl.pop(key, None)


def local_cache_invalidate_prefix(prefix: str) -> None:
    for k in [k for k in _local_ttl if k.startswith(prefix)]:
        _local_ttl.pop(k, None)

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
