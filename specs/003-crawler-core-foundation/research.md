# Research: Crawler Core Foundation

## Decision 1: Wrap existing crawler behavior, do not replace it

- Decision: Build a crawler-core orchestration and persistence layer that sits around current crawler paths, preserving existing Playwright fallback, page-quality checks, and extraction logic.
- Rationale: User explicitly requires continuity of working behavior; wrapper architecture minimizes regression risk.
- Alternatives considered:
  - Full crawler rewrite: rejected due to high regression and delivery risk.
  - Site-specific crawler modules: rejected due to explicit non-goal and maintenance overhead.

## Decision 2: Standards-first library usage for core protocols

- Decision: Use mature libraries for URI parsing/normalization, robots parsing, sitemap parsing, and HTML metadata extraction; avoid bespoke parser implementations unless no robust library exists.
- Rationale: Reduces correctness risk for RFC and protocol edge cases while accelerating delivery.
- Alternatives considered:
  - Custom parser implementations for all standards: rejected due to quality and maintenance burden.
  - Minimal parsing with ad hoc regex rules: rejected due to poor standards compliance.

## Decision 3: Host discovery policy with allowlist-controlled auto-crawl

- Decision: Register all newly discovered hosts/subdomains but auto-crawl only those that match allowlist rules.
- Rationale: Captures discovery intelligence while preventing uncontrolled scope expansion.
- Alternatives considered:
  - Auto-crawl every discovered host: rejected due to compliance and operational risk.
  - Manual approval for all new hosts: rejected as too slow for initial index coverage.

## Decision 4: HTTP freshness and fetch policy

- Decision: Use HTTP cache semantics (ETag/Last-Modified/Cache-Control) as default re-crawl policy with explicit force-refresh override capability.
- Rationale: Balances crawl efficiency and correctness while preserving deterministic operator control.
- Alternatives considered:
  - Always full re-fetch: rejected due to unnecessary load and cost.
  - Fixed-interval-only polling: rejected as less adaptive than validator-based freshness.

## Decision 5: Concurrency model

- Decision: Use a shared global worker pool with per-host concurrency caps and crawl-delay compliance.
- Rationale: Enables multi-domain parallelism without overwhelming specific hosts.
- Alternatives considered:
  - Global-only concurrency without host caps: rejected for fairness/compliance risks.
  - Strict single worker per host: rejected due to reduced throughput.

## Decision 6: Representation retention lifecycle

- Decision: Keep full HTTP representations for all fetched resources for 10 days, then retain metadata-only history.
- Rationale: Preserves short-term debug/audit utility while controlling long-term storage growth.
- Alternatives considered:
  - Infinite full payload retention: rejected due to storage cost and governance burden.
  - Metadata-only from day one: rejected because it weakens troubleshooting and audit depth.

## Decision 7: Phase boundary for downstream material tables

- Decision: Restrict this phase to crawl/index discovery datasets and prohibit direct writes to final material/product tables.
- Rationale: Keeps scope aligned with index-first foundation and avoids coupling with downstream normalization/matching concerns.
- Alternatives considered:
  - Immediate end-to-end ingestion into final tables: rejected as premature and scope-expanding.

## Traceability Mapping

- Active feature spec: `specs/003-crawler-core-foundation/spec.md`
- Active implementation plan: `specs/003-crawler-core-foundation/plan.md`
- Persistence scope: raw crawler/index entities under `apps/material-ingestion/src/material_ingestion/db/models/` with migrations under `apps/material-ingestion/migrations/versions/`
- Validation scope: `apps/material-ingestion/tests/unit/` and `apps/material-ingestion/tests/integration/`
