# Tasks: Crawler Core Foundation

**Input**: Design documents from `/specs/003-crawler-core-foundation/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Every change MUST define a validation path. Automated tests SHOULD be added when practical; this plan includes unit and integration coverage for regression-prone crawler behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare dependencies, constants, and scaffolding for crawler-core work.

- [ ] T001 Add crawler-core standards libraries and lock dependency versions in /Users/ilker/source/bunlar/apps/material-ingestion/pyproject.toml
- [ ] T002 Add crawler-core config defaults (allowlist, host concurrency caps, representation retention days) in /Users/ilker/source/bunlar/apps/material-ingestion/.env.example
- [ ] T003 [P] Add reason-code and frontier-state constant module in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawler_reason_codes.py
- [ ] T004 [P] Add crawler-core type definitions for host policy, URI identity, and decision payloads in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/types.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core persistence and orchestration infrastructure required before user stories.

**⚠️ CRITICAL**: No user story work should begin before this phase completes.

- [ ] T005 Create migration for crawler-core tables (host, URI identity, alias, frontier, run, decision, policy, sitemap, fetch, representation, metadata) in /Users/ilker/source/bunlar/apps/material-ingestion/migrations/versions/20260524_08_create_crawler_core_foundation_tables.py
- [ ] T006 [P] Implement SQLAlchemy models for CrawlHost, UriIdentity, UriAlias in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/db/models/raw_web_crawl_identity.py
- [ ] T007 [P] Implement SQLAlchemy models for CrawlRun, FrontierItem, CrawlDecision in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/db/models/raw_web_crawl_frontier.py
- [ ] T008 [P] Implement SQLAlchemy models for RobotsPolicy, SitemapSource, SitemapEntry in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/db/models/raw_web_crawl_policy.py
- [ ] T009 [P] Implement SQLAlchemy models for HttpFetchAttempt, HttpRepresentation, PageMetadata, StructuredDataRecord, CandidateDocument in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/db/models/raw_web_crawl_observation.py
- [ ] T010 Register crawler-core models in model exports and metadata wiring in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/db/models/__init__.py
- [ ] T011 Implement repository/service layer for idempotent URI identity upsert and alias mapping in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_identity_service.py
- [ ] T012 Implement repository/service layer for frontier state transitions and duplicate-active prevention in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_frontier_service.py
- [ ] T013 Implement repository/service layer for crawl decision recording and standardized reason codes in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_decision_service.py
- [ ] T014 Add foundational migration/model integration tests in /Users/ilker/source/bunlar/apps/material-ingestion/tests/integration/test_web_crawler_core_schema.py

**Checkpoint**: Foundation ready; user story implementation may proceed.

---

## Phase 3: User Story 1 - Track Crawl Index State Reliably (Priority: P1) 🎯 MVP

**Goal**: Persist URI identity, frontier lifecycle, fetch attempts, representations, links, and decisions while preserving existing crawler behavior.

**Independent Test**: Launch a crawl run with seed hosts and verify end-to-end index state, decision logs, and compatibility with current Playwright/page-quality/extraction flow.

### Validation for User Story 1

- [ ] T015 [P] [US1] Add unit tests for RFC-3986-oriented URI normalization and alias mapping in /Users/ilker/source/bunlar/apps/material-ingestion/tests/unit/test_web_crawl_uri_identity.py
- [ ] T016 [P] [US1] Add integration test for frontier state lifecycle and decision persistence in /Users/ilker/source/bunlar/apps/material-ingestion/tests/integration/test_web_crawl_frontier_lifecycle.py
- [ ] T017 [P] [US1] Add regression integration test ensuring existing Playwright fallback/page-quality/extraction still works in /Users/ilker/source/bunlar/apps/material-ingestion/tests/integration/test_web_crawl_backward_compatibility.py

### Implementation for User Story 1

- [ ] T018 [US1] Implement crawler-core orchestration wrapper around existing web pipeline in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_orchestrator.py
- [ ] T019 [US1] Integrate URI identity + frontier + decision services into crawl start flow in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_pipeline.py
- [ ] T020 [US1] Persist HTTP fetch attempts and representation metadata in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_download_service.py
- [ ] T021 [US1] Persist extracted links and page-level crawl observations in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_discovery_service.py
- [ ] T022 [US1] Add crawl-run level entrypoints/options (run key, force refresh) in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/cli.py

**Checkpoint**: User Story 1 is independently functional and testable (MVP).

---

## Phase 4: User Story 2 - Enforce Web Crawling Policies Consistently (Priority: P2)

**Goal**: Apply and persist robots policy, sitemap discovery, canonical/robots/hreflang metadata, and policy-driven decisions.

**Independent Test**: Crawl policy-rich hosts and verify robots/sitemap/metadata records plus decision outcomes.

### Validation for User Story 2

- [ ] T023 [P] [US2] Add unit tests for robots policy evaluation and allow/disallow resolution in /Users/ilker/source/bunlar/apps/material-ingestion/tests/unit/test_web_crawl_robots_policy.py
- [ ] T024 [P] [US2] Add unit tests for sitemap parsing and lineage tracking in /Users/ilker/source/bunlar/apps/material-ingestion/tests/unit/test_web_crawl_sitemap_discovery.py
- [ ] T025 [P] [US2] Add integration test for policy-driven queue/skip/defer decisions in /Users/ilker/source/bunlar/apps/material-ingestion/tests/integration/test_web_crawl_policy_decisions.py

### Implementation for User Story 2

- [ ] T026 [US2] Implement robots retrieval, parse persistence, and evaluation outcomes in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_robots_service.py
- [ ] T027 [US2] Implement sitemap discovery and sitemap-entry ingestion with host lineage in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_sitemap_service.py
- [ ] T028 [US2] Integrate allowlist-based host auto-crawl gate for newly discovered hosts in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_host_scope_service.py
- [ ] T029 [US2] Persist canonical, robots meta, and hreflang metadata extraction in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_metadata_service.py
- [ ] T030 [US2] Wire policy services into orchestration decision points in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_orchestrator.py

**Checkpoint**: User Stories 1 and 2 both work independently with consistent policy behavior.

---

## Phase 5: User Story 3 - Discover Candidate Technical Documents at Scale (Priority: P3)

**Goal**: Support parallel crawling with per-host controls and produce auditable candidate document inventory.

**Independent Test**: Run at least 3 concurrent workers across multi-host scope and verify candidate-doc discovery, no duplicate active frontier entries, and host-level constraints.

### Validation for User Story 3

- [ ] T031 [P] [US3] Add integration test for multi-worker crawl execution and duplicate-frontier prevention in /Users/ilker/source/bunlar/apps/material-ingestion/tests/integration/test_web_crawl_parallel_workers.py
- [ ] T032 [P] [US3] Add integration test for per-host concurrency cap and crawl-delay compliance in /Users/ilker/source/bunlar/apps/material-ingestion/tests/integration/test_web_crawl_host_throttling.py
- [ ] T033 [P] [US3] Add integration test for candidate document discovery and reason-code lifecycle in /Users/ilker/source/bunlar/apps/material-ingestion/tests/integration/test_web_crawl_candidate_documents.py

### Implementation for User Story 3

- [ ] T034 [US3] Implement worker coordination and global queue consumption logic in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_worker_service.py
- [ ] T035 [US3] Implement per-host concurrency and crawl-delay scheduler controls in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_scheduler_service.py
- [ ] T036 [US3] Implement conditional request freshness handling (ETag/Last-Modified/Cache-Control + force refresh override) in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_freshness_service.py
- [ ] T037 [US3] Implement candidate document classification and audit trail persistence in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_candidate_service.py
- [ ] T038 [US3] Add CLI controls for worker count and host-scope execution in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/cli.py

**Checkpoint**: All user stories are independently functional, with scalable discovery behavior.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, retention lifecycle, docs, and validation.

- [ ] T039 [P] Implement 10-day full-representation retention transition to metadata-only history in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/services/web_crawl_retention_service.py
- [ ] T040 Add scheduled retention lifecycle invocation path in /Users/ilker/source/bunlar/apps/material-ingestion/src/material_ingestion/raw_ingestion_pipeline.py
- [ ] T041 [P] Add integration test for retention lifecycle transitions in /Users/ilker/source/bunlar/apps/material-ingestion/tests/integration/test_web_crawl_retention_lifecycle.py
- [ ] T042 Update material-ingestion operational documentation for crawler-core entities and reason codes in /Users/ilker/source/bunlar/apps/material-ingestion/README.md
- [ ] T043 Run end-to-end quickstart validation and record evidence in /Users/ilker/source/bunlar/specs/003-crawler-core-foundation/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no dependencies.
- **Phase 2 (Foundational)**: depends on Phase 1 and blocks all user stories.
- **Phase 3 (US1)**: depends on Phase 2; MVP slice.
- **Phase 4 (US2)**: depends on Phase 2 and integrates with US1 orchestration hooks.
- **Phase 5 (US3)**: depends on Phase 2 and uses US1/US2 persistence/policy services.
- **Phase 6 (Polish)**: depends on completion of desired user stories.

### User Story Dependencies

- **US1 (P1)**: starts after foundational phase; no dependency on US2/US3.
- **US2 (P2)**: starts after foundational phase; integrates with orchestration introduced in US1.
- **US3 (P3)**: starts after foundational phase; requires host/policy/fetch primitives from US1/US2 for full value.

### Parallel Opportunities

- Setup tasks `T003`, `T004` parallelizable after `T001`/`T002` planning decisions.
- Foundational model tasks `T006`-`T009` parallelizable.
- Per-story tests are parallelizable (`T015`-`T017`, `T023`-`T025`, `T031`-`T033`).
- Within US3, scheduler and candidate services (`T035`, `T037`) can proceed in parallel after worker service boundaries are defined.
- Polish tasks `T039` and `T041` can run in parallel.

---

## Parallel Example: User Story 1

```bash
Task: "T015 [US1] URI normalization unit tests in tests/unit/test_web_crawl_uri_identity.py"
Task: "T016 [US1] frontier lifecycle integration test in tests/integration/test_web_crawl_frontier_lifecycle.py"
Task: "T017 [US1] backward compatibility integration test in tests/integration/test_web_crawl_backward_compatibility.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete US1 tasks (Phase 3).
3. Validate crawl-index state tracking + compatibility with existing crawler behavior.
4. Demo/deploy MVP indexing foundation.

### Incremental Delivery

1. Foundation (Phases 1-2).
2. US1 (index-state core).
3. US2 (policy consistency).
4. US3 (parallel scale + candidate discovery).
5. Polish (retention + docs + end-to-end validation).

### Parallel Team Strategy

1. Team A: persistence/migrations/model tracks (Phase 2).
2. Team B: orchestration and policy services (US1/US2).
3. Team C: worker scheduling and candidate discovery (US3) after foundational APIs stabilize.

---

## Notes

- [P] tasks target disjoint files or separable concerns.
- Every task maps to explicit file paths for direct execution.
- No task writes to final material/product tables in this phase.
- Validate existing crawler behavior after each story phase to prevent regressions.
