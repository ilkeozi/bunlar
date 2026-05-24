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
