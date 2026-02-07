---
phase: 02-mesh-quality-baseline
plan: 01
subsystem: infra
tags: [occt, opencascade, gltf, glb, tessellation, webworker]

# Dependency graph
requires:
  - phase: 01-browser-conversion-outputs
    provides: Browser STEP->GLB conversion + metadata bundling patterns
provides:
  - Face-merged glTF/GLB writer defaults (best-effort)
  - Explorer conversion defaults switched to absolute tessellation
  - Post-write meshStats + bounded retry-on-explosion with conversionWarnings
affects:
  - 02-mesh-quality-baseline
  - 03-explorer-selection-workflow

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Guarded OCCT writer defaults (bindings-safe)
    - Post-write GLB JSON analysis for meshStats and retry decisions
    - Structured conversionWarnings for lightweight UX surfacing

key-files:
  created: []
  modified:
    - packages/opencascade-convert/src/occt/writer-core.ts
    - frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts
    - frontend/src/app/features/climate-tech/assembly-viewer/hooks/useAssemblyFile.ts

key-decisions:
  - 'Enable RWGltf_CafWriter.SetMergeFaces(true) best-effort to reduce render primitives'
  - 'Default Explorer triangulation to absolute deflection (relative=false) to avoid micro-edge explosions'
  - 'Detect triangle/primitive explosions post-write and retry with a bounded, deterministic schedule'

patterns-established:
  - 'Worker returns meshStats + conversionWarnings; hook optionally emits dev-only console summary'

# Metrics
duration: 7 min
completed: 2026-02-07
---

# Phase 02 Plan 01: Mesh Quality Baseline Summary

**Explorer conversion now uses absolute tessellation + face-merged GLB export, with bounded retry and meshStats/warnings when triangle explosions occur.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-07T09:58:20Z
- **Completed:** 2026-02-07T10:06:18Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Enabled best-effort face merging in `RWGltf_CafWriter` to reduce primitive/draw overhead.
- Switched Assembly Hierarchy Explorer defaults to absolute tessellation (`relative: false`) with pinned deflections.
- Added post-write GLB meshStats computation plus bounded retry-on-explosion with structured `conversionWarnings` (dev-only surfaced).

## Task Commits

Each task was committed atomically:

1. **Task 1: Enable face merging in OCCT glTF writer** - `511b0e9` (perf)
2. **Task 2: Switch Explorer conversion defaults to absolute meshing + consistent name format** - `5eeab81` (perf)
3. **Task 3: Add post-write mesh stats + bounded retry-on-explosion in Explorer conversion worker** - `d773b83` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `packages/opencascade-convert/src/occt/writer-core.ts` - Enables guarded `SetMergeFaces(true)` defaults for GLB/GLTF writes.
- `frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts` - Adds meshStats, explosion thresholds, and bounded retry with warnings.
- `frontend/src/app/features/climate-tech/assembly-viewer/hooks/useAssemblyFile.ts` - Pins triangulation defaults and emits a single dev-only `console.warn` when warnings exist.

## Decisions Made

- Guarded `writer.SetMergeFaces(true)` behind a feature-detect + try/catch so binding variance cannot break conversion.
- Forced `relative=false` for Explorer conversions to prevent micro-edge relative-deflection triangle explosions.
- Fixed explosion policy to deterministic thresholds (`MAX_TRIANGLES=5_000_000`, `MAX_PRIMITIVES=50_000`) with a 3-attempt coarsening schedule.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Mesh quality baseline defaults + safeguards are in place.
- Ready for `.planning/phases/02-mesh-quality-baseline/02-02-PLAN.md` (persisted warnings + Step Converter warning UI + overlay work).

---

_Phase: 02-mesh-quality-baseline_
_Completed: 2026-02-07_
