from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(slots=True)
class HostThrottleDecision:
    allowed: bool
    reason: str


class HostThrottleScheduler:
    def __init__(self, per_host_limit: int | None = None) -> None:
        self.per_host_limit = per_host_limit or int(os.getenv("MATERIAL_INGESTION_CRAWL_HOST_CONCURRENCY", "2"))
        self._active_by_host: dict[str, int] = defaultdict(int)

    def try_acquire(self, url: str) -> HostThrottleDecision:
        host = urlsplit(url).netloc
        if self._active_by_host[host] >= self.per_host_limit:
            return HostThrottleDecision(allowed=False, reason="host_concurrency_limit")
        self._active_by_host[host] += 1
        return HostThrottleDecision(allowed=True, reason="acquired")

    def release(self, url: str) -> None:
        host = urlsplit(url).netloc
        if self._active_by_host[host] <= 0:
            return
        self._active_by_host[host] -= 1
