# Data Model: Crawler Core Foundation

## Entity: CrawlHost

- Purpose: Tracks seed and discovered hosts/subdomains with crawl-eligibility status.
- Key fields:
  - `id` (uuid)
  - `hostname` (string, unique)
  - `source_type` (enum: seed, discovered)
  - `discovery_source` (string, nullable; robots/sitemap/link lineage)
  - `allowlist_match` (boolean)
  - `auto_crawl_enabled` (boolean)
  - `first_seen_at`, `last_seen_at`

## Entity: UriIdentity

- Purpose: Canonical crawl identity for a resource with alias tracking.
- Key fields:
  - `id` (uuid)
  - `canonical_uri` (string, unique)
  - `host_id` (fk -> CrawlHost)
  - `normalized_hash` (string, unique)
  - `created_at`, `updated_at`

## Entity: UriAlias

- Purpose: Records observed URL variants mapped to a URI identity.
- Key fields:
  - `id` (uuid)
  - `uri_identity_id` (fk -> UriIdentity)
  - `observed_uri` (string)
  - `observed_at`

## Entity: FrontierItem

- Purpose: Represents crawl work-state lifecycle per URI identity.
- Key fields:
  - `id` (uuid)
  - `uri_identity_id` (fk -> UriIdentity)
  - `crawl_run_id` (fk -> CrawlRun)
  - `state` (enum: queued, in_progress, completed, skipped, deferred, failed)
  - `priority` (integer)
  - `state_reason_code` (string)
  - `scheduled_at`, `updated_at`
- Constraint: only one active (`queued`/`in_progress`) item per URI identity per run.

## Entity: CrawlRun

- Purpose: Logical execution context across one or more workers.
- Key fields:
  - `id` (uuid)
  - `run_key` (string, unique)
  - `started_at`, `ended_at`
  - `initiator` (string)
  - `force_refresh` (boolean)

## Entity: RobotsPolicy

- Purpose: Stores host robots retrieval and parsed policy outcomes.
- Key fields:
  - `id` (uuid)
  - `host_id` (fk -> CrawlHost)
  - `fetched_at`
  - `fetch_status` (enum: success, failed, unavailable)
  - `policy_blob_ref` (string, nullable)
  - `evaluation_summary` (json)

## Entity: SitemapSource

- Purpose: Tracks sitemap endpoints per host and fetch status.
- Key fields:
  - `id` (uuid)
  - `host_id` (fk -> CrawlHost)
  - `sitemap_url` (string)
  - `discovered_via` (enum: robots, manual, nested)
  - `last_fetch_status` (string)
  - `last_fetched_at`

## Entity: SitemapEntry

- Purpose: Captures URLs discovered from sitemaps with lineage.
- Key fields:
  - `id` (uuid)
  - `sitemap_source_id` (fk -> SitemapSource)
  - `uri_identity_id` (fk -> UriIdentity)
  - `lastmod` (datetime, nullable)
  - `discovered_at`

## Entity: HttpFetchAttempt

- Purpose: Audit record of a single fetch attempt.
- Key fields:
  - `id` (uuid)
  - `uri_identity_id` (fk -> UriIdentity)
  - `crawl_run_id` (fk -> CrawlRun)
  - `requested_at`, `completed_at`
  - `status_code` (integer)
  - `outcome` (enum: success, retryable_failure, terminal_failure, skipped_not_modified)
  - `reason_code` (string)

## Entity: HttpRepresentation

- Purpose: Stored HTTP representation and retention lifecycle.
- Key fields:
  - `id` (uuid)
  - `fetch_attempt_id` (fk -> HttpFetchAttempt)
  - `storage_ref` (string, nullable after expiry)
  - `content_type` (string)
  - `etag` (string, nullable)
  - `last_modified` (string, nullable)
  - `cache_control` (string, nullable)
  - `expires_full_at` (datetime)
  - `metadata_only_since` (datetime, nullable)

## Entity: ExtractedLink

- Purpose: Directed relationship between source and discovered target URIs.
- Key fields:
  - `id` (uuid)
  - `source_uri_identity_id` (fk -> UriIdentity)
  - `target_uri_identity_id` (fk -> UriIdentity)
  - `rel` (string, nullable)
  - `anchor_text` (string, nullable)
  - `discovered_at`

## Entity: PageMetadata

- Purpose: Captures canonical, robots meta, and hreflang metadata.
- Key fields:
  - `id` (uuid)
  - `uri_identity_id` (fk -> UriIdentity)
  - `canonical_hint` (string, nullable)
  - `robots_meta` (json, nullable)
  - `hreflang_map` (json, nullable)
  - `observed_at`

## Entity: StructuredDataRecord

- Purpose: Stores extracted structured data artifacts with provenance.
- Key fields:
  - `id` (uuid)
  - `uri_identity_id` (fk -> UriIdentity)
  - `format` (enum: jsonld, microdata, rdfa, other)
  - `payload` (json)
  - `observed_at`

## Entity: CandidateDocument

- Purpose: Candidate downloadable artifact for technical datasheet selection.
- Key fields:
  - `id` (uuid)
  - `uri_identity_id` (fk -> UriIdentity)
  - `source_uri_identity_id` (fk -> UriIdentity)
  - `mime_type` (string)
  - `classification` (string)
  - `decision_state` (enum: new, shortlisted, deferred, rejected)
  - `decision_reason_code` (string)
  - `created_at`, `updated_at`

## Entity: CrawlDecision

- Purpose: Captures decision events for traceability and analytics.
- Key fields:
  - `id` (uuid)
  - `crawl_run_id` (fk -> CrawlRun)
  - `uri_identity_id` (fk -> UriIdentity, nullable for host-level decisions)
  - `decision_type` (enum: queue, skip, defer, reject, promote_candidate)
  - `reason_code` (string)
  - `detail` (json, nullable)
  - `recorded_at`

## Relationship Summary

- `CrawlHost` 1..* `UriIdentity`
- `UriIdentity` 1..* `UriAlias`, `FrontierItem`, `HttpFetchAttempt`, `PageMetadata`, `StructuredDataRecord`, `CandidateDocument`, `CrawlDecision`
- `SitemapSource` 1..* `SitemapEntry`
- `CrawlRun` 1..* `FrontierItem`, `HttpFetchAttempt`, `CrawlDecision`

## Validation Rules

- `hostname` must be unique per `CrawlHost`.
- `canonical_uri` and `normalized_hash` must be unique per `UriIdentity`.
- Auto-crawl only permitted when `allowlist_match=true`.
- Full representation retention expires at `fetched_at + 10 days`; metadata must remain after expiry.
- Frontier uniqueness constraint prevents duplicate active items for same URI identity in a crawl run.
