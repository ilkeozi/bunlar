---
phase: 02-mesh-quality-baseline
plan: 05
subsystem: infra
tags: [opencascade, occt, glb, mesh, web-worker, nx, vite, vitest]

# Dependency graph
requires:
  - phase: 02-mesh-quality-baseline
    provides: step converter bounded retry-on-explosion + persisted conversionWarnings
  - phase: 02-mesh-quality-baseline
    provides: Phase 2 verification report locating the Explorer worker gap
provides:
  - Explorer worker bounded 3-attempt retry-on-triangle-explosion
  - Structured conversionWarnings for forced absolute tessellation, retries, and unresolved explosions
affects: [phase-02-verification, phase-03-explorer-selection]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Bounded retry-on-explosion using post-write meshStats thresholds
    - JSON-serializable conversionWarnings (code/message/detail) for downstream UI/logging

key-files:
  created:
    - frontend/src/app/features/climate-tech/assembly-viewer/workers/explosionPolicy.ts
    - frontend/src/app/features/climate-tech/assembly-viewer/workers/explosionPolicy.test.ts
  modified:
    - frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts

key-decisions:
  - 'Match explosion thresholds to Step Converter (MAX_TRIANGLES=5_000_000, MAX_PRIMITIVES=50_000) for parity'
  - 'Return the final-attempt GLB even when unresolved; surface via mesh/triangle-explosion-unresolved'

patterns-established:
  - 'Keep retry schedules in pure helpers so they can be unit-tested and reused'

# Metrics
duration: 5 min
completed: 2026-02-07
---

# Phase 2 Plan 05: Explorer Explosion Policy Gap Closure Summary

**Assembly Explorer conversion now enforces absolute tessellation and retries up to 3 attempts when post-write meshStats exceed explosion thresholds, returning structured conversionWarnings.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-07T15:38:18Z
- **Completed:** 2026-02-07T15:42:53Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added MAX_TRIANGLES/MAX_PRIMITIVES thresholds + bounded retry-on-explosion loop to the Explorer conversion worker.
- Ensured `relative=true` requests are forced to absolute tessellation (`relative=false`) and surfaced via structured warnings.
- Extracted and unit-tested the explosion predicate + deterministic 3-attempt coarsening schedule.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add explosion thresholds + bounded retry loop to Explorer worker** - `a313172` (feat)
2. **Task 2: Add a small test for the explosion policy helpers (behavior-level)** - `743175f` (test)

**Plan metadata:** (docs commit)

## Files Created/Modified

- `frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts` - bounded retry-on-explosion + structured conversionWarnings for Explorer conversion.
- `frontend/src/app/features/climate-tech/assembly-viewer/workers/explosionPolicy.ts` - thresholds + explosion predicate + pinned 3-attempt coarsening schedule.
- `frontend/src/app/features/climate-tech/assembly-viewer/workers/explosionPolicy.test.ts` - vitest coverage for predicate + schedule.

## Decisions Made

- Matched Step Converter explosion thresholds (5,000,000 triangles / 50,000 primitives) to keep parity across conversion paths.
- Preserve fidelity-first behavior by returning a GLB even when retries cannot resolve explosions; warn via `mesh/triangle-explosion-unresolved`.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 2 gap closure is complete; re-run `.planning/phases/02-mesh-quality-baseline/02-VERIFICATION.md` to clear the failed truth.
- Phase 2 still requires human performance verification on the target device class per the verification report.

---

_Phase: 02-mesh-quality-baseline_
_Completed: 2026-02-07_
