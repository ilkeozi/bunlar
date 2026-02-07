---
phase: 03-explorer-selection-workflow
plan: 02
subsystem: ui
tags: [react, three, r3f, zustand, orbitcontrols]

# Dependency graph
requires:
  - phase: 03-explorer-selection-workflow/03-01
    provides: Zustand store + NodeMap selection/visibility semantics
provides:
  - Mesh index (OCAF entry -> meshes[]) for selection/visibility
  - 3D frontmost picking -> store selection
  - Gearbox-style selection outline across all meshes in selected part
  - Hidden parts enforced as invisible + non-pickable
  - Fit-to-selection/visible camera animation without retargeting OrbitControls
affects: [03-03, 03-04, explorer-selection]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Override mesh.raycast while hidden to enforce non-pickable parts
    - Fit camera by moving camera.position only (keep OrbitControls.target)

key-files:
  created:
    - frontend/src/app/features/climate-tech/assembly-viewer/utils/sceneIndex.ts
    - frontend/src/app/features/climate-tech/assembly-viewer/visualizer/SelectionOutline.tsx
    - frontend/src/app/features/climate-tech/assembly-viewer/utils/fitCamera.ts
    - frontend/src/app/features/climate-tech/assembly-viewer/visualizer/FitController.tsx
  modified:
    - frontend/src/app/features/climate-tech/assembly-viewer/visualizer/AssemblyModel.tsx
    - frontend/src/app/features/climate-tech/assembly-viewer/visualizer/AssemblyCanvas.tsx

key-decisions:
  - 'None - followed plan as specified'

patterns-established:
  - 'Scene index computed once per model load and stored in feature state'
  - 'Selection outline attached as a child object and made non-pickable'

# Metrics
duration: 6m
completed: 2026-02-07
---

# Phase 03 Plan 02: 3D Canvas Wiring Summary

**3D selection now picks the frontmost mesh, outlines the selected part with the gearbox edge style, enforces hidden parts as non-pickable, and supports fit-to-selection/visible without retargeting orbit controls.**

## Performance

- **Duration:** 6m 13s
- **Started:** 2026-02-07T19:22:44Z
- **Completed:** 2026-02-07T19:28:57Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Indexed GLB meshes by OCAF entry to drive selection + visibility updates without scene traversal
- Wired R3F pointer selection to the explorer store and applied the gearbox-style outline highlight
- Enforced hidden parts as invisible and non-pickable (raycast disabled), and added fit camera animation driven by store requests

## Task Commits

Each task was committed atomically:

1. **Task 1: Add mesh indexing + 3D picking + gearbox outline highlight** - `760758d` (feat)
2. **Task 2: Enforce hidden-not-pickable + add fit-to-selection/visible** - `7d1e43e` (feat)

Plan metadata: committed as `docs(03-02): complete 03-02 plan` (SUMMARY + STATE)

## Files Created/Modified

- `frontend/src/app/features/climate-tech/assembly-viewer/utils/sceneIndex.ts` - Build mesh index by OCAF entry for fast lookup
- `frontend/src/app/features/climate-tech/assembly-viewer/visualizer/SelectionOutline.tsx` - Gearbox-style outline attached to all meshes for selected part
- `frontend/src/app/features/climate-tech/assembly-viewer/utils/fitCamera.ts` - Fit position math using bounding sphere + FOV while keeping orbit target
- `frontend/src/app/features/climate-tech/assembly-viewer/visualizer/FitController.tsx` - Animates camera.position on store fit requests (selection/visible)
- `frontend/src/app/features/climate-tech/assembly-viewer/visualizer/AssemblyModel.tsx` - Model picking + mesh indexing + hidden visibility application
- `frontend/src/app/features/climate-tech/assembly-viewer/visualizer/AssemblyCanvas.tsx` - Canvas wiring: pointer-missed clear + fit controller + outline mount

## Decisions Made

None - followed plan as specified.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 03-03 to wire tree/toolbar UI into store selection, hide/isolate, and `requestFit(...)`.

---

_Phase: 03-explorer-selection-workflow_
_Completed: 2026-02-07_
