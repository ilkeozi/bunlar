# Quickstart: Retire Stale Material-Ingestion Spec

## Goal

Replace stale specification baseline for planning while leaving implementation code untouched.

## Steps

1. Confirm active feature pointer:
   - Read `.specify/feature.json`
   - Verify `feature_directory` points to `specs/002-retire-stale-spec`

2. Confirm stale baseline is not active:
   - Check old spec directory remains available for history
   - Ensure no planning command resolves to the stale directory

3. Validate no-code-change scope:
   - Run `git status --short`
   - Verify changed files are limited to:
     - `.specify/feature.json`
     - `specs/002-retire-stale-spec/*`
     - documentation context updates (e.g., `AGENTS.md` SPECKIT marker)

4. Verify planning continuity:
   - Run `.specify/scripts/bash/setup-plan.sh --json`
   - Confirm `FEATURE_SPEC` resolves to `specs/002-retire-stale-spec/spec.md`

## Expected Outcome

- Active planning baseline is replaced.
- Stale spec remains historical reference only.
- No implementation code edits are introduced.
