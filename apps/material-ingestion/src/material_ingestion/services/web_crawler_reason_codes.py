from __future__ import annotations

FRONTIER_STATES = (
    "queued",
    "in_progress",
    "completed",
    "skipped",
    "deferred",
    "failed",
)

DECISION_TYPES = (
    "queue",
    "skip",
    "defer",
    "reject",
    "promote_candidate",
)

REASON_DISCOVERED = "discovered"
REASON_DUPLICATE_ACTIVE = "duplicate_active_frontier"
REASON_HTTP_NOT_MODIFIED = "http_not_modified"
REASON_FORCE_REFRESH = "force_refresh"
REASON_HOST_BLOCKED = "host_not_allowlisted"
REASON_ROBOTS_DISALLOWED = "robots_disallowed"
