# Research: Retire Stale Material-Ingestion Spec

## Decision 1: Keep stale spec in history, but remove it from active planning

- Decision: Preserve stale spec files for audit/history, but point active workflow metadata to the replacement spec.
- Rationale: Maintains traceability while preventing stale inputs from influencing future planning.
- Alternatives considered:
  - Delete stale spec entirely: rejected because it removes historical context.
  - Keep stale spec active with warnings: rejected because warnings are frequently ignored and do not enforce correctness.

## Decision 2: Enforce no-code-change boundary through path-scoped validation

- Decision: Validate change scope by reviewing diffs and ensuring only spec/process files are touched.
- Rationale: Directly aligns with user requirement to avoid implementation code modifications.
- Alternatives considered:
  - Rely on intent only: rejected due to high risk of accidental edits.
  - Add automated path guard tooling now: rejected for this feature scope; manual validation is sufficient and lower overhead.

## Decision 3: Standardize active baseline resolution via `.specify/feature.json`

- Decision: Use `.specify/feature.json` as the canonical active spec pointer for downstream Spec Kit commands.
- Rationale: Existing scripts already resolve from this metadata, making it the lowest-risk control point.
- Alternatives considered:
  - Branch-name-only resolution: rejected because branch naming can drift from desired active spec.
  - Manual path input for each command: rejected due to operator overhead and inconsistency risk.

## Decision 4: Add explicit status contract for active/retired semantics

- Decision: Define a lightweight contract describing required status fields for active and retired spec baselines.
- Rationale: Creates a shared language for future automation and documentation checks without touching runtime code.
- Alternatives considered:
  - No contract and narrative-only documentation: rejected because status interpretation can drift.
  - Full registry subsystem: rejected as unnecessary complexity for documentation-only scope.
