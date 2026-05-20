# Quickstart: Material Ingestion Domain Refactor

## Goal
Implement strict folder ownership and unified orchestration for `CLI` + `HTTP API` without manual stage-by-stage execution.

## 1. Confirm Structure Baseline
- Verify `apps/material-ingestion/src/material_ingestion` exists.
- Create/confirm domain folders:
  - `shared/`
  - `material_ingestion/`
  - `uns/`

## 2. Introduce Orchestration Core
- Add a transport-agnostic orchestration service responsible for:
  - deterministic stage order
  - per-context FIFO queueing
  - stop-and-resume failure handling

## 3. Connect Invocation Channels
- Adapt existing CLI entrypoints to call orchestration core (not per-stage manual chain).
- Add HTTP API endpoint handlers that call the same orchestration core.

## 4. Enforce Placement Rules
- Add merge-blocking validation for ambiguous or cross-domain placement.
- Ensure any ambiguous file placement is rejected until a `PlacementRule` resolves target domain.

## 5. Validation
- Unit: stage transition rules, queue behavior, resume behavior.
- Integration: same-context queue FIFO and failure resume.
- Contract: HTTP API accepts and reports runs matching `contracts/ingestion-orchestration.openapi.yaml`.
- Regression: existing UNS flows still pass after refactor.

## 6. Done Criteria
- Contributors place changes using strict ownership directories with no exceptions.
- CLI and HTTP API produce equivalent run behavior and outcomes.
- Failed runs resume from last successful stage.
