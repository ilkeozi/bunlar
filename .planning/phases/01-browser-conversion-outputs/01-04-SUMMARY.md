---
phase: 01-browser-conversion-outputs
plan: 04
subsystem: testing
tags: [playwright, web-worker, opencascade, step, glb, nx, vite]

# Dependency graph
requires:
  - phase: 01-browser-conversion-outputs
    provides: Browser STEP converter worker + UI + stable error taxonomy (01-01..01-03)
provides:
  - Worker emits `UNSUPPORTED_STEP_CONTENT` for supported-but-empty STEP inputs
  - Playwright regression coverage using a minimal empty STEP fixture
  - Stable UI surface (`data-error-code`) for e2e assertions
affects: [conv-05, conversion-errors, browser-step-converter]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - 'Forced worker errors use `__code` + preserved `detail`'
    - 'Unsupported content detection uses node map emptiness + GLB geometry sanity checks'

key-files:
  created:
    - frontend-e2e/src/fixtures/empty.step
    - frontend-e2e/src/step-converter-browser.spec.ts
  modified:
    - frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts
    - frontend/src/app/features/tools/step-converter/components/StepConverterForm.tsx

key-decisions:
  - 'Treat empty node maps and meshless/positionless GLBs as `UNSUPPORTED_STEP_CONTENT` (not `CONVERSION_FAILED`)'
  - 'Preserve structured `detail` on forced-code worker errors for actionable diagnostics'

patterns-established:
  - 'E2E error assertions target `data-error-code` instead of translated copy'

# Metrics
duration: 5 min
completed: 2026-02-06
---

# Phase 01 Plan 04: Unsupported STEP Content Error Summary

**Browser STEP converter emits `UNSUPPORTED_STEP_CONTENT` for empty/unsupported models (no partial outputs) and is covered by a Playwright regression fixture/test.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-06T17:01:53Z
- **Completed:** 2026-02-06T17:07:27Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added explicit worker detection for supported-but-empty STEP content (pre-export node map check + post-export GLB geometry check)
- Preserved `detail` payloads on forced-code worker errors so logs stay actionable
- Added an empty STEP fixture + Playwright regression test asserting `data-error-code="UNSUPPORTED_STEP_CONTENT"` and no download CTA

## Task Commits

Each task was committed atomically:

1. **Task 1: Detect empty/unsupported STEP outputs and emit UNSUPPORTED_STEP_CONTENT** - `8114a8a` (feat)
2. **Task 2: Add Playwright regression test for unsupported STEP content (with fixture adjustment loop)** - `2d0f1cb` (test)

## Files Created/Modified

- `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts` - Emits `UNSUPPORTED_STEP_CONTENT` with structured `detail` for empty/unsupported outputs
- `frontend/src/app/features/tools/step-converter/components/StepConverterForm.tsx` - Renders `data-error-code` for stable e2e assertions
- `frontend-e2e/src/fixtures/empty.step` - Minimal syntactically valid empty STEP fixture
- `frontend-e2e/src/step-converter-browser.spec.ts` - Regression spec for `/tools/step-converter-browser`

## Decisions Made

- Treat empty node maps and meshless/positionless GLBs as `UNSUPPORTED_STEP_CONTENT` so unsupported content is actionable and stable.
- Preserve `detail` on forced-code worker errors so diagnostics survive the worker error mapping.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 01 gap closure complete: valid-but-empty STEP inputs surface `UNSUPPORTED_STEP_CONTENT` and no bundle is produced.
- CONV-05 is unblocked via implementation + automated regression coverage.

---

_Phase: 01-browser-conversion-outputs_
_Completed: 2026-02-06_
