---
phase: 02-mesh-quality-baseline
plan: 03
subsystem: ui
tags: [react, threejs, r3f, drei, nx, vite, perf]

# Dependency graph
requires:
  - phase: 01-browser-conversion-outputs
    provides: Assembly Explorer viewer baseline (R3F Canvas + model loading)
provides:
  - Dev-only on-screen performance overlay (FPS + triangles + draw calls) for Assembly Explorer canvas
affects: [mesh-quality, perf-baseline, assembly-explorer, conversion-tuning]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - 'Dev-only instrumentation guarded by `import.meta.env.DEV`'
    - 'Throttled `useFrame` sampling (<=4Hz) for overlay UI updates'

key-files:
  created:
    - frontend/src/app/features/climate-tech/assembly-viewer/components/DevPerfOverlay.tsx
  modified:
    - frontend/src/app/features/climate-tech/assembly-viewer/visualizer/AssemblyCanvas.tsx

key-decisions:
  - 'Use `@react-three/drei` Html overlay inside Canvas to keep stats colocated with renderer context'
  - 'Throttle overlay state updates to ~250ms to avoid UI churn during orbit'

patterns-established:
  - 'Overlay components should be pointer-event transparent (`pointer-events: none`)'

# Metrics
duration: 2 min
completed: 2026-02-07
---

# Phase 02 Plan 03: Dev Perf Overlay Summary

**Dev-only R3F overlay shows FPS plus renderer triangles/draw calls while orbiting in the Assembly Hierarchy Explorer canvas.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-07T09:58:26Z
- **Completed:** 2026-02-07T10:01:05Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added a compact, pointer-event transparent overlay that samples FPS and `gl.info.render` stats
- Throttled overlay updates to <=4Hz so instrumentation doesn't add noticeable UI overhead
- Wired the overlay into the Assembly Explorer Canvas for dev builds only

## Task Commits

Each task was committed atomically:

1. **Task 1: Create DevPerfOverlay (FPS + renderer.info) with throttled updates** - `97234e7` (feat)
2. **Task 2: Mount overlay in AssemblyCanvas for dev builds only** - `6473b24` (feat)

## Files Created/Modified

- `frontend/src/app/features/climate-tech/assembly-viewer/components/DevPerfOverlay.tsx` - Dev-only overlay sampling FPS + renderer triangles/calls with throttled React updates
- `frontend/src/app/features/climate-tech/assembly-viewer/visualizer/AssemblyCanvas.tsx` - Mounts overlay behind `import.meta.env.DEV` inside the Canvas tree

## Decisions Made

- Use `@react-three/drei` `Html` for the overlay so it can read renderer state via R3F hooks without external wiring.
- Update overlay state at ~250ms intervals to keep instrumentation low-overhead during orbit/select.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Dev perf instrumentation is in place; ready to baseline orbit/select performance while tuning mesh quality.

---

_Phase: 02-mesh-quality-baseline_
_Completed: 2026-02-07_
