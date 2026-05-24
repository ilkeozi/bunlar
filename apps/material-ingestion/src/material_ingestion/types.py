from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MaterialRecord:
    source: str
    material_id: str
    name: str
    aliases: list[str] = field(default_factory=list)
    composition: dict[str, Any] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)
    standards: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WebCrawlHostPolicy:
    hostname: str
    allowlist_match: bool
    auto_crawl_enabled: bool
    source_type: str = "discovered"


@dataclass(slots=True)
class WebUriIdentityPayload:
    observed_uri: str
    canonical_uri: str
    normalized_hash: str
    host_id: int


@dataclass(slots=True)
class WebCrawlDecisionPayload:
    crawl_run_id: int
    decision_type: str
    reason_code: str
    uri_identity_id: int | None = None
    detail: dict[str, Any] = field(default_factory=dict)
