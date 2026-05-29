from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


# ---------------------------------------------------------------------------
# Per-table export rows (plain dataclasses — NOT ORM models).
# Field names and types mirror the existing raw_web_* columns exactly.
# Optional / nullable columns default to None or ""; required FKs do not.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class UriIdentityRow:
    id: int
    canonical_uri: str
    normalized_hash: str
    host_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class CrawlHostRow:
    id: int
    hostname: str
    source_type: str = ""
    discovery_source: str = ""
    allowlist_match: bool = False
    auto_crawl_enabled: bool = False
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


@dataclass(slots=True)
class FrontierItemRow:
    id: int
    uri_identity_id: int
    crawl_run_id: int
    state: str
    priority: int = 0
    state_reason_code: str = ""
    scheduled_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class HttpFetchAttemptRow:
    id: int
    uri_identity_id: int
    crawl_run_id: int
    status_code: int = 200
    outcome: str = "success"
    reason_code: str = ""
    requested_url: str = ""
    final_url: str = ""
    redirect_count: int = 0
    ttfb_ms: int = 0
    read_ms: int = 0
    total_ms: int = 0
    requested_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass(slots=True)
class HttpRepresentationRow:
    id: int
    fetch_attempt_id: int
    content_type: str = ""
    content_length: int = 0
    content_language: str = ""
    content_encoding: str = ""


@dataclass(slots=True)
class PageTextRow:
    id: int
    fetch_attempt_id: int
    title: str = ""
    meta_description: str = ""
    h1: str = ""
    lang: str = ""
    raw_html_length: int = 0
    text_length: int = 0
    text_ratio: float = 0.0
    render_needed: bool = False
    extracted_at: datetime | None = None


@dataclass(slots=True)
class ExtractedLinkRow:
    id: int
    source_uri_identity_id: int
    target_uri_identity_id: int
    rel: str = ""
    anchor_text: str = ""
    discovered_at: datetime | None = None


@dataclass(slots=True)
class CandidateDocumentRow:
    id: int
    uri_identity_id: int
    source_uri_identity_id: int
    mime_type: str = ""
    classification: str = "new"
    decision_state: str = "new"
    decision_reason_code: str = ""
    score: int = 0
    distinct_source_count: int = 0
    score_reason_json: str = "{}"


@dataclass(slots=True)
class CrawlDecisionRow:
    id: int
    crawl_run_id: int
    uri_identity_id: int | None
    decision_type: str = ""
    reason_code: str = ""
    detail_json: str = "{}"
    recorded_at: datetime | None = None


@dataclass(slots=True)
class SitemapEntryRow:
    id: int
    sitemap_source_id: int
    uri_identity_id: int
    lastmod_at: datetime | None = None
    changefreq: str | None = None
    priority: float | None = None


@dataclass(slots=True)
class SitemapAlternateRow:
    id: int
    sitemap_entry_id: int
    hreflang: str = ""
    href: str = ""


@dataclass(slots=True)
class RobotsPolicyRow:
    id: int
    host_id: int
    fetch_status: str = ""
    policy_blob: str = ""
    evaluation_summary_json: str = "{}"
    fetched_at: datetime | None = None


# ---------------------------------------------------------------------------
# Container for a complete exported slice of the database.
# Callers populate only the tables relevant to their analysis; everything else
# defaults to an empty list.
# ---------------------------------------------------------------------------


@dataclass
class AnalysisDataset:
    uri_identities: list[UriIdentityRow]
    hosts: list[CrawlHostRow]
    frontier_items: list[FrontierItemRow]
    fetch_attempts: list[HttpFetchAttemptRow]
    representations: list[HttpRepresentationRow]
    page_texts: list[PageTextRow]
    extracted_links: list[ExtractedLinkRow]
    candidate_documents: list[CandidateDocumentRow]
    crawl_decisions: list[CrawlDecisionRow] = field(default_factory=list)
    sitemap_entries: list[SitemapEntryRow] = field(default_factory=list)
    sitemap_alternates: list[SitemapAlternateRow] = field(default_factory=list)
    robots_policies: list[RobotsPolicyRow] = field(default_factory=list)
