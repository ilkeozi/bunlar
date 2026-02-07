---
phase: 03-explorer-selection-workflow
plan: 01
subsystem: ui
tags: [assembly-viewer, zustand, nodemap, ocaf, three]

# Dependency graph
requires:
  - phase: 02-mesh-quality-baseline
    provides: stable assembly-viewer conversion outputs (GLB mesh naming includes OCAF labelEntry + NodeMap metadata)
provides:
  - Feature-local Zustand store for Assembly Explorer selection/visibility/isolate/fit requests
  - Pure NodeMap/OCAF helpers for deterministic mapping, reveal, and effective-hidden derivation
affects: [phase-03-explorer-selection]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Feature-local Zustand store as single source of truth for tree/canvas sync
    - Immutable Set/Map updates to preserve React subscription correctness
    - Pure NodeMap helpers for ancestor/descendant traversal and effective-hidden derivation

key-files:
  created:
    - frontend/src/app/features/climate-tech/assembly-viewer/state/useAssemblyExplorerStore.ts
    - frontend/src/app/features/climate-tech/assembly-viewer/utils/ocaf.ts
    - frontend/src/app/features/climate-tech/assembly-viewer/utils/nodeMapIndex.ts
  modified: []

key-decisions:
  - 'getAncestorNodeIds() returns root-first order for stable ancestor expansion'

patterns-established:
  - 'Explorer store keeps non-serializable indices internal, except meshesByOcafEntry which is intentionally exposed'

# Metrics
duration: 6 min
completed: 2026-02-07
---

# Phase 3 Plan 1: Explorer Store + Index Utilities Summary

**Assembly Explorer now has a single source of truth for selection/visibility/isolate/fit requests plus pure NodeMap/OCAF indexing helpers to sync tree and 3D deterministically.**

## Performance

- **Duration:** 5m 31s
- **Started:** 2026-02-07T19:14:03Z
- **Completed:** 2026-02-07T19:19:34Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `useAssemblyExplorerStore` with locked Phase 03 semantics (single-select, 3D->tree reveal via ancestor expansion, hide/show/isolate snapshot restore, fit request counters).
- Added `extractOcafEntry()` and NodeMap traversal/indexing helpers to keep mapping/visibility derivations pure and reusable.
- Ensured the frontend builds with the new store/utilities in place.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add feature-local Zustand store for selection + visibility + fit requests** - `e452425` (feat)
2. **Task 2: Add OCAF + NodeMap indexing utilities used by store and UI** - `1a3842e` (feat)

**Plan metadata:** (docs commit)

## Files Created/Modified

- `frontend/src/app/features/climate-tech/assembly-viewer/state/useAssemblyExplorerStore.ts` - Zustand store for selection/visibility/isolate/fit requests + mesh index wiring.
- `frontend/src/app/features/climate-tech/assembly-viewer/utils/ocaf.ts` - `extractOcafEntry(name)` for 3D picking and mesh indexing.
- `frontend/src/app/features/climate-tech/assembly-viewer/utils/nodeMapIndex.ts` - NodeMap helpers (ancestors/descendants, labelEntry<->nodeId mapping, effective-hidden leaf derivation).

## Decisions Made

- `getAncestorNodeIds()` returns root-first order so consumers can expand ancestors deterministically.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Store and helpers are ready to be wired into the tree UI + R3F canvas for selection highlight, mesh visibility application, and fit behavior.

---

_Phase: 03-explorer-selection-workflow_
_Completed: 2026-02-07_
