# Quickstart: Crawler Core Foundation

## Goal

Plan and validate crawler-core foundation delivery without regressing existing crawler behavior.

## Prerequisites

1. Active branch is `003-crawler-core-foundation`.
2. Feature spec and plan exist under `specs/003-crawler-core-foundation/`.
3. Material-ingestion dependencies and DB environment are available.

## Planning Validation Steps

1. Confirm active spec pointer:
   - Read `.specify/feature.json`
   - Verify `feature_directory` is `specs/003-crawler-core-foundation`

2. Confirm plan assets:
   - `specs/003-crawler-core-foundation/plan.md`
   - `specs/003-crawler-core-foundation/research.md`
   - `specs/003-crawler-core-foundation/data-model.md`
   - `specs/003-crawler-core-foundation/contracts/crawler-core-index.contract.yaml`

3. Validate scope boundaries:
   - Existing crawler behavior must remain intact (Playwright fallback, page-quality logic, extraction).
   - No site-specific crawler modules.
   - No writes to final material/product tables in this phase.

4. Validate key clarified policies:
   - Register all discovered hosts; auto-crawl only allowlist matches.
   - Default freshness uses HTTP validators and cache headers.
   - Global worker pool with per-host caps and crawl-delay compliance.
   - Full HTTP representations retained for 10 days, then metadata-only history.

5. Validate implementation readiness:
   - Migration plan covers crawler-core entities in `data-model.md`.
   - Contract schemas cover host, URI identity, frontier transitions, fetches, retention, and decisions.
   - Test strategy includes unit + integration checks for concurrency, policy, and compatibility.

## Execution Preview (post-plan)

1. Run `/speckit-tasks` to generate an ordered implementation backlog.
2. Execute tasks incrementally with validation after each slice.
3. Keep compatibility checks for existing crawler behavior in every integration milestone.

## Completion Checklist

- [x] Plan artifacts created and linked.
- [x] Clarified policies encoded in design artifacts.
- [x] Constitution checks passed pre/post design.
- [x] AGENTS.md SPECKIT context updated to this feature plan.

## Validation Evidence (2026-05-24)

- Phase 3 (US1) validation:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_web_crawl_uri_identity.py tests/integration/test_web_crawler_core_schema.py tests/integration/test_web_crawl_frontier_lifecycle.py tests/integration/test_web_crawl_backward_compatibility.py -q`
  - Result: `5 passed`
- Phase 4 (US2) validation:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_web_crawl_robots_policy.py tests/unit/test_web_crawl_sitemap_discovery.py tests/integration/test_web_crawl_policy_decisions.py tests/integration/test_web_crawl_frontier_lifecycle.py -q`
  - Result: `5 passed`
- Phase 5 (US3) validation:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/integration/test_web_crawl_parallel_workers.py tests/integration/test_web_crawl_host_throttling.py tests/integration/test_web_crawl_candidate_documents.py -q`
  - Result: `5 passed`
- Phase 6 retention validation:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/integration/test_web_crawl_retention_lifecycle.py -q`
  - Result: `1 passed`
