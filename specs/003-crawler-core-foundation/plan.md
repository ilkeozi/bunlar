# Implementation Plan: Crawler Core Foundation

**Branch**: `[003-crawler-core-foundation]` | **Date**: 2026-05-24 | **Spec**: [/Users/ilker/source/bunlar/specs/003-crawler-core-foundation/spec.md](/Users/ilker/source/bunlar/specs/003-crawler-core-foundation/spec.md)

**Input**: Feature specification from `/specs/003-crawler-core-foundation/spec.md`

**Note**: This plan is produced by `/speckit-plan` and covers phases through design artifacts.

## Summary

Add a crawler core foundation around the existing material-ingestion web crawler to standardize URI identity, crawl frontier state, robots/sitemap policy handling, HTTP fetch and representation tracking, and candidate document discovery, while explicitly preserving currently working Playwright fallback, page-quality logic, and extraction behavior.

## Technical Context

**Language/Version**: Python >=3.10

**Primary Dependencies**: SQLAlchemy, Alembic, psycopg, existing crawler stack; add standards-oriented libraries for URI normalization, robots parsing, sitemap parsing, and HTML metadata extraction

**Storage**: PostgreSQL (raw web ingestion tables and new crawler-core raw index tables)

**Testing**: pytest unit + integration suites (`apps/material-ingestion/tests/unit`, `apps/material-ingestion/tests/integration`) and targeted crawl-run validation checks

**Target Platform**: Linux/macOS developer and CI environments running Nx + Python CLI workflows

**Project Type**: Backend data-ingestion service (Nx-managed Python application)

**Performance Goals**: Sustain at least 3 concurrent workers with per-host caps; maintain duplicate-frontier prevention under concurrent enqueue attempts

**Constraints**: Preserve existing working crawler flows, no site-specific crawler modules, no direct writes to final material/product tables, standards-aligned behavior for RFC 3986 / 9110 / 9111 / 9309 and sitemap protocol

**Scale/Scope**: Multi-domain and multi-subdomain crawling with discovery tracking (seed + discovered hosts), index-first phase focused on technical document candidate discovery

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Spec-first check: scope, behavior, constraints, acceptance criteria, and out-of-scope items are explicit and current.
- [x] Simplicity/evolvability check: proposed structure is the simplest viable approach and any abstraction/shared code is justified.
- [x] Verification-first check: each implementation slice has an independent validation path; automated tests or clear manual validation are defined.
- [x] User-centered quality check: UX consistency, accessibility practicality, and empty/loading/error/edge states are intentionally addressed.
- [x] Performance/reliability check: impacted paths include error handling, graceful failure expectations, and a validation approach for performance impact.
- [x] Documentation/automation fidelity check: required guidance updates are identified.

## Project Structure

### Documentation (this feature)

```text
specs/003-crawler-core-foundation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── crawler-core-index.contract.yaml
└── tasks.md
```

### Source Code (repository root)

```text
apps/material-ingestion/
├── src/material_ingestion/
│   ├── db/
│   │   ├── models/
│   │   └── session.py
│   ├── services/
│   ├── sources/web/
│   └── cli.py
├── migrations/versions/
└── tests/
    ├── unit/
    └── integration/

specs/003-crawler-core-foundation/
```

**Structure Decision**: Keep all planning artifacts in `specs/003-crawler-core-foundation/`; implementation will extend existing `apps/material-ingestion` service, DB models, migrations, and tests without replacing current crawler modules.

## Phase 0: Research Output

- Completed: [/Users/ilker/source/bunlar/specs/003-crawler-core-foundation/research.md](/Users/ilker/source/bunlar/specs/003-crawler-core-foundation/research.md)
- Resolved dependency and behavior decisions for URI normalization, robots/sitemaps handling, HTTP caching semantics, retention policy, and concurrency policy.

## Phase 1: Design Output

- Data model: [/Users/ilker/source/bunlar/specs/003-crawler-core-foundation/data-model.md](/Users/ilker/source/bunlar/specs/003-crawler-core-foundation/data-model.md)
- Interface contracts: [/Users/ilker/source/bunlar/specs/003-crawler-core-foundation/contracts/crawler-core-index.contract.yaml](/Users/ilker/source/bunlar/specs/003-crawler-core-foundation/contracts/crawler-core-index.contract.yaml)
- Quickstart: [/Users/ilker/source/bunlar/specs/003-crawler-core-foundation/quickstart.md](/Users/ilker/source/bunlar/specs/003-crawler-core-foundation/quickstart.md)
- Agent context update: `AGENTS.md` SPECKIT marker updated to this feature plan.

## Implementation Strategy (Phase 2 Ready)

1. Introduce crawler-core persistence entities and migrations for host registry, URI identity, frontier, robots/sitemap artifacts, fetch/representation logs, link graph, metadata, structured data, candidate docs, and decision logs.
2. Add an orchestration layer that wraps the current crawler and emits normalized crawler-core events/records without disrupting existing fetch/extract flows.
3. Integrate allowlist-based host auto-crawl policy, per-host concurrency caps, crawl-delay compliance, and conditional fetch freshness policy.
4. Add retention lifecycle processing to transition full representations to metadata-only after 10 days.
5. Add tests for identity dedupe, race-safe frontier enqueue, robots policy behavior, sitemap discovery lineage, retention transitions, and backward compatibility with existing crawler behaviors.

## Risk Register

- **Risk**: Concurrency races create duplicate frontier activity.
  - **Mitigation**: Unique identity constraints + idempotent enqueue semantics + race-focused integration tests.
- **Risk**: New crawler-core layer accidentally changes existing crawler behavior.
  - **Mitigation**: Compatibility tests against current Playwright fallback/page-quality/extraction outcomes.
- **Risk**: Representation retention jobs remove required debugging evidence too early.
  - **Mitigation**: Metadata preservation guarantee + retention job audit logs + configurable grace period controls if needed.

## Post-Design Constitution Re-Check

- [x] Spec-first check remains satisfied after design artifact generation.
- [x] Simplicity/evolvability remains satisfied by wrapping existing crawler functionality rather than replacing it.
- [x] Verification-first remains satisfied via explicit unit/integration validation plan.
- [x] User-centered quality remains satisfied through auditable operator-facing crawl decisions and traceability.
- [x] Performance/reliability remains satisfied through explicit concurrency, caching, and failure-handling constraints.
- [x] Documentation/automation fidelity remains satisfied with updated AGENTS context marker and feature-local artifacts.

## Complexity Tracking

No constitution violations requiring justification.
