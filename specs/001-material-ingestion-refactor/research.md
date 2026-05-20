# Research: Material Ingestion Domain Refactor

## Decision 1: Keep Python package architecture; separate by domain folders inside `src/material_ingestion`
- Decision: Retain the current Python/Nx project and enforce strict domain folders for `shared`, `material_ingestion`, and `uns` behaviors.
- Rationale: This satisfies strict ownership without unnecessary cross-project migration risk and preserves existing working tests and package setup.
- Alternatives considered:
  - Split into multiple Nx apps immediately: rejected due to migration overhead and higher breakage risk.
  - Keep mixed structure with naming conventions only: rejected because it does not enforce ownership boundaries.

## Decision 2: Add orchestration service layer callable from CLI and HTTP API
- Decision: Introduce an orchestration entry service that is transport-agnostic and callable by both CLI and HTTP adapters.
- Rationale: Enables one canonical pipeline execution path and avoids duplicate stage logic.
- Alternatives considered:
  - Keep separate CLI scripts for each flow: rejected because it requires manual step execution.
  - Build HTTP-only first: rejected because CLI is existing operational path and must remain supported.

## Decision 3: Concurrency policy is FIFO queue per ingestion context
- Decision: If a run is active for a context, queue subsequent runs for that context and process FIFO.
- Rationale: Prevents conflicting writes while preserving request acceptance.
- Alternatives considered:
  - Reject concurrent requests: simpler but degrades operator workflow.
  - Allow parallel same-context runs: rejected due to conflict risk.

## Decision 4: Failure policy is stop-and-resume
- Decision: On stage failure, stop run, mark failed, and allow resume from last successful stage.
- Rationale: Minimizes rework and preserves deterministic recovery semantics.
- Alternatives considered:
  - Always full restart: rejected for operational inefficiency.
  - Continue after failure: rejected due to data integrity risk.

## Decision 5: Contract-first for HTTP orchestration
- Decision: Define HTTP orchestration contract in spec artifacts before implementation.
- Rationale: Keeps API behavior testable and aligned with CLI parity from the start.
- Alternatives considered:
  - Define endpoints during coding: rejected due to higher rework risk across adapters/tests.
