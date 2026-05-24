from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FreshnessRequestDecision:
    conditional: bool
    headers: dict[str, str]
    reason: str


def build_freshness_request(*, etag: str = "", last_modified: str = "", force_refresh: bool = False) -> FreshnessRequestDecision:
    if force_refresh:
        return FreshnessRequestDecision(conditional=False, headers={}, reason="force_refresh")

    headers: dict[str, str] = {}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    if headers:
        return FreshnessRequestDecision(conditional=True, headers=headers, reason="conditional")
    return FreshnessRequestDecision(conditional=False, headers={}, reason="no_validators")
