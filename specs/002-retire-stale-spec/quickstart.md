# Quickstart: Retire Stale Material-Ingestion Spec

## Goal

Replace stale specification baseline for planning while leaving implementation code untouched.

## Steps

1. Confirm active feature pointer:
   - Read `.specify/feature.json`
   - Verify `feature_directory` points to `specs/002-retire-stale-spec`
   - Run `.specify/scripts/bash/setup-plan.sh --json` and confirm `FEATURE_SPEC` resolves to `specs/002-retire-stale-spec/spec.md`

2. Confirm stale baseline is not active:
   - Check old spec directory remains available for history
   - Ensure no planning command resolves to the stale directory
   - Validate old baseline is treated as retired reference only (`specs/001-material-ingestion-refactor/`)

3. Validate no-code-change scope:
   - Run `git status --short`
   - Verify changed files are limited to:
     - `.specify/feature.json`
     - `specs/002-retire-stale-spec/*`
     - documentation context updates (e.g., `AGENTS.md` SPECKIT marker)
   - Allowed paths:
     - `.specify/`
     - `specs/`
     - `AGENTS.md`
     - `agents.md`
   - Forbidden paths:
     - `apps/`
     - `packages/`
     - runtime service/source files

4. Verify planning continuity:
   - Run `.specify/scripts/bash/setup-plan.sh --json`
   - Confirm `FEATURE_SPEC` resolves to `specs/002-retire-stale-spec/spec.md`
   - Run `/speckit-plan` and verify outputs remain in `specs/002-retire-stale-spec/`
   - Run `/speckit-tasks` and verify tasks reference only the new baseline context

5. Perform scope audit:
   - Run `git diff --name-only`
   - Reject completion if any changed path is outside allowed scope.

## Stale vs Active Baseline Checklist

- [x] Active baseline is `specs/002-retire-stale-spec/`.
- [x] Stale baseline `specs/001-material-ingestion-refactor/` is historical/non-active.
- [x] Pointer metadata `.specify/feature.json` resolves to active baseline.

## Planning Continuity Checklist

- [x] `setup-plan.sh --json` resolves `FEATURE_SPEC` to `specs/002-retire-stale-spec/spec.md`.
- [x] `/speckit-plan` artifacts are generated under `specs/002-retire-stale-spec/`.
- [x] `/speckit-tasks` output references only new-baseline assumptions.

## Final Validation Notes (2026-05-24)

- Active pointer verification completed.
- Allowed/forbidden path checks defined and reviewed.
- Baseline retirement mapping and handoff steps documented.
- No runtime-code-change expectation preserved by process guardrails.

## Operator Handoff

1. Treat `specs/002-retire-stale-spec/` as the only active planning baseline for this scope.
2. Use checklist and scope-audit steps above before any future baseline transitions.
3. If baseline changes again, update:
   - `.specify/feature.json`
   - baseline status mapping in `research.md`
   - this quickstart validation evidence.

## Expected Outcome

- Active planning baseline is replaced.
- Stale spec remains historical reference only.
- No implementation code edits are introduced.
