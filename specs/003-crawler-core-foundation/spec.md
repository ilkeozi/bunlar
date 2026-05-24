# Feature Specification: Crawler Core Foundation

**Feature Branch**: `003-crawler-core-foundation`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "Add a crawler core foundation around existing material-ingestion crawler behavior while preserving current working functionality."

## Clarifications

### Session 2026-05-24

- Q: How should newly discovered hosts/subdomains be handled for automatic crawling? → A: Register all discovered hosts, auto-crawl only if allowlist-matching; otherwise keep registered but not auto-crawled.
- Q: What should be the default re-crawl freshness policy? → A: Use HTTP cache semantics (ETag/Last-Modified/Cache-Control) by default, with manual force-refresh override.
- Q: What concurrency model should govern parallel crawling? → A: Use a global worker pool with per-host concurrency caps and crawl-delay compliance.
- Q: What retention policy should be used for full HTTP representations? → A: Keep full HTTP representations for all fetched resources for 10 days, then retain metadata-only history.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Track Crawl Index State Reliably (Priority: P1)

As a data ingestion operator, I can start crawl indexing for one or more hosts and see complete lifecycle tracking for URL identity, crawl frontier progress, fetch attempts, and resulting discoveries without breaking existing crawler behavior.

**Why this priority**: Reliable indexing state is the foundation for any later extraction or document selection work.

**Independent Test**: Can be fully tested by launching a crawl run against seed hosts and verifying persistent records for URI identity, frontier states, fetch attempts, stored representations, and decision reason codes.

**Acceptance Scenarios**:

1. **Given** a crawl run is started with seed hosts, **When** indexing executes, **Then** each discovered URL is tracked as a normalized identity with host/domain association and crawl state.
2. **Given** a URL is evaluated for processing, **When** the system makes a decision (queue, skip, defer, reject), **Then** the decision is stored with a reason code and timestamp.
3. **Given** existing crawler logic is already functional, **When** the crawler core foundation is introduced, **Then** previously working Playwright fallback, page quality, and extraction behavior continues to operate.

---

### User Story 2 - Enforce Web Crawling Policies Consistently (Priority: P2)

As a compliance-conscious operator, I can trust that robots policies, sitemap declarations, canonical hints, and robots metadata are recorded and applied consistently during crawl decisioning.

**Why this priority**: Policy compliance and deterministic behavior are required before scaling to many domains.

**Independent Test**: Can be tested by crawling hosts with known robots/sitemap/canonical behaviors and verifying persisted policy records and policy-driven crawl decisions.

**Acceptance Scenarios**:

1. **Given** a host exposes a robots policy, **When** URLs are evaluated, **Then** allow/disallow decisions follow the parsed policy and are recorded.
2. **Given** sitemaps are declared or discovered, **When** sitemap entries are processed, **Then** discovered URLs and host relationships are stored and queued according to policy.
3. **Given** a page provides canonical, robots meta, or hreflang metadata, **When** the page is indexed, **Then** metadata is stored and influences identity and crawl decisions where applicable.

---

### User Story 3 - Discover Candidate Technical Documents at Scale (Priority: P3)

As an ingestion analyst, I can run multiple crawl workers across related domains/subdomains and produce a ranked inventory of candidate documents/downloads (such as technical datasheet PDFs) for downstream review.

**Why this priority**: The immediate business value is finding high-value technical documents while postponing writes to final product/material tables.

**Independent Test**: Can be tested by running parallel crawl workers across sample hosts and verifying candidate-document discovery, cross-host tracking, and parallel-safe run state.

**Acceptance Scenarios**:

1. **Given** multiple hosts/subdomains are in scope, **When** crawl workers run in parallel, **Then** each worker progresses independently while writing to a shared consistent crawl state.
2. **Given** candidate downloadable documents are discovered, **When** they are evaluated, **Then** candidates are stored with source context and decision reason codes without writing into final product/material tables.
3. **Given** robots/sitemaps reveal previously unknown hosts, **When** new hosts are detected, **Then** they are registered and linked to the originating discovery path for auditing.

### Edge Cases

- What happens when the same resource appears under multiple URL variants (scheme, case, trailing slash, query ordering)? It must converge to one URI identity while preserving aliases.
- How does the system handle conflicting canonical signals and redirect chains? It must preserve both observed evidence and final decision reason code.
- How does the system handle unreachable robots/sitemap endpoints? It must record failure attempts and proceed with defined fallback policy.
- What happens when parallel workers race to enqueue the same URL? Only one active frontier item should remain while all attempts are auditable.
- How does the system handle non-HTML content discovered from pages or sitemaps? It must classify and store candidates without forcing extraction into downstream product/material schemas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST introduce a crawler core foundation that wraps existing crawler components without removing or replacing current working behavior.
- **FR-002**: The system MUST maintain URI identity records using normalization behavior aligned with RFC 3986 and retain mappings from observed URL variants to canonical crawl identities.
- **FR-003**: The system MUST track crawl frontier state transitions for each URI identity, including queued, in-progress, completed, skipped, deferred, and failed states.
- **FR-004**: The system MUST persist robots policy artifacts and policy evaluation outcomes aligned with RFC 9309 for each relevant host.
- **FR-005**: The system MUST discover and persist sitemap sources and sitemap URL entries, including host/subdomain discovery lineage.
- **FR-006**: The system MUST persist HTTP fetch attempts and outcomes, including request target, response status, timing, and retry/defer rationale, aligned with RFC 9110 semantics.
- **FR-007**: The system MUST persist stored HTTP representations and representation metadata required for crawl auditability and caching behavior aligned with RFC 9111.
- **FR-007a**: The system MUST use HTTP freshness validators and cache directives as the default re-crawl policy, while allowing explicit force-refresh requests for selected crawl runs or targets.
- **FR-007b**: The system MUST retain full HTTP representations for all fetched resources for 10 days from fetch time, and MUST retain metadata-only history after full representation expiry.
- **FR-008**: The system MUST extract and store outbound links from indexed pages with source-page linkage.
- **FR-009**: The system MUST extract and store page metadata including canonical URL hints, robots meta directives, and hreflang declarations.
- **FR-010**: The system MUST extract and store structured data artifacts found on indexed pages with source provenance.
- **FR-011**: The system MUST identify and store candidate documents/downloads with classification attributes suitable for later technical datasheet selection.
- **FR-012**: The system MUST record crawl decisions and standardized reason codes for queueing, skipping, deferring, rejecting, and candidate promotion actions.
- **FR-013**: The system MUST support domain and subdomain scope tracking, including explicit seed hosts and newly discovered hosts from robots, sitemaps, and links.
- **FR-013a**: The system MUST register all newly discovered hosts/subdomains, but MUST auto-crawl only hosts/subdomains that match configured allowlist rules; non-matching hosts remain tracked as discovered and not auto-crawled.
- **FR-014**: The system MUST support independent worker/event-driven execution so multiple crawl processes can operate concurrently against shared state.
- **FR-014a**: The system MUST enforce per-host concurrency caps and respect declared crawl-delay directives while running a shared global worker pool.
- **FR-015**: The system MUST avoid direct writes into final material/product tables in this phase; outputs are limited to crawl/index discovery datasets.
- **FR-016**: The system MUST prefer established libraries and standards-compliant parsers for URI handling, HTTP policy/caching behavior, robots processing, sitemap parsing, and metadata extraction rather than bespoke implementations where a mature library exists.
- **FR-017**: The system MUST preserve compatibility with currently working Playwright fallback, page-quality logic, and extraction logic.

### Key Entities *(include if feature involves data)*

- **Crawl Host**: A tracked domain or subdomain target, including seed/discovered status and discovery lineage.
- **URI Identity**: Normalized crawl identity for a resource plus observed URL aliases.
- **Frontier Item**: Queueable crawl work unit tied to URI identity and current crawl state.
- **Robots Policy Record**: Retrieved and parsed host policy plus evaluation results.
- **Sitemap Source**: A discovered sitemap endpoint and retrieval status.
- **Sitemap Entry**: A URL discovered from sitemap data with source linkage.
- **Fetch Attempt**: A single network retrieval attempt with status/outcome metadata.
- **Stored Representation**: Retained response representation and associated metadata for audit/caching behavior.
- **Extracted Link**: Source-to-target relationship discovered from indexed content.
- **Page Metadata Record**: Canonical, robots meta, hreflang, and related metadata extracted from a page.
- **Structured Data Record**: Structured page data artifact with extraction context.
- **Candidate Document**: Discovered downloadable asset candidate with classification and provenance.
- **Crawl Decision**: Decision event with reason code, actor (worker/system), and timestamp.
- **Crawl Run**: Logical crawl execution context spanning one or more workers.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of processed URLs in a crawl run are represented by a persisted URI identity and frontier state history.
- **SC-002**: At least 95% of crawl decisions are accompanied by an explicit standardized reason code and source context.
- **SC-003**: For approved in-scope hosts, 100% of robots policy retrieval outcomes are recorded with corresponding allow/deny evaluation traces.
- **SC-004**: For hosts exposing sitemap references, at least 95% of sitemap-declared URLs are either queued, skipped with reason, or rejected with reason within the same crawl run.
- **SC-005**: Parallel crawl execution can run at least 3 concurrent workers with no duplicate active frontier entries for the same URI identity.
- **SC-006**: Candidate technical document discovery produces an auditable inventory where each candidate includes source page, discovery path, and current decision state.
- **SC-007**: Existing crawler behavior currently relied upon in production-like workflows continues functioning with no critical regression in end-to-end crawl completion.
- **SC-008**: During this phase, zero records are written directly into final material/product destination tables.
- **SC-009**: For previously fetched resources with validators present, at least 90% of repeat checks use conditional retrieval behavior rather than unconditional full re-fetch.
- **SC-010**: During parallel operation, 100% of requests must comply with configured per-host concurrency caps and applicable crawl-delay constraints.
- **SC-011**: 100% of stored full HTTP representations older than 10 days are transitioned to metadata-only history according to retention policy.

## Assumptions

- Existing crawler behavior remains the operational baseline; this feature adds foundational orchestration and indexing records around it.
- Initial business focus is discovery/indexing for valuable technical document candidates, not downstream product/material ingestion.
- A shared database is available for durable crawl/index state across workers.
- Retention lifecycle processing is available to enforce 10-day full-representation TTL and metadata-only continuation.
- Seed hosts may include multiple related domains/subdomains (for example LG Chem and BASF host families), and additional hosts can be added through controlled discovery.
- Standards-compliant third-party libraries are acceptable dependencies when they reduce custom parsing/logic risk.

## Constitution Alignment *(mandatory)*

- **CA-001 Spec Quality**: The spec defines explicit scope boundaries: preserve existing crawler behavior, add crawl-core indexing foundation, and exclude downstream product/material writes.
- **CA-002 Simplicity and Evolvability**: The feature adds a minimal foundational layer focused on state, policy, and discovery records so current working crawler paths remain intact while enabling later evolution.
- **CA-003 Validation Path**: Each user story includes independent acceptance scenarios and can be validated through controlled crawl runs and state/audit verification.
- **CA-004 User-Centered Quality**: Operator-facing outcomes prioritize traceability, predictable policy behavior, and transparent reason codes for decision review.
- **CA-005 Performance and Reliability**: Requirements include parallel worker safety, duplicate-frontier prevention, retry/defer auditability, and graceful handling of unavailable robots/sitemap endpoints.
- **CA-006 Documentation Fidelity**: Crawl runbooks and ingestion architecture docs must be updated to describe new crawl-core entities, decision reason codes, and discovery workflow boundaries.
