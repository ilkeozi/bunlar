---
phase: 01-browser-conversion-outputs
plan: 03
subsystem: testing
tags: [nx, vite, react, step, glb, gltf, zip, opencascade, occt]

# Dependency graph
requires:
  - phase: 01-browser-conversion-outputs
    provides: 01-02 browser conversion worker + bundle outputs
provides:
  - End-to-end browser verification for STEP conversion + zip bundle contents
  - Meaningful name preservation across metadata assemblyTree/nodeMap/BOM
affects: [mesh-quality-baseline, explorer-hierarchy, metadata-schema]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - 'Prefer STEP labels for part names; fall back to glTF node names'
    - 'Normalize names (prettyName) consistently across assemblyTree/nodeMap/BOM'

key-files:
  created: []
  modified:
    - .planning/phases/01-browser-conversion-outputs/01-03-PLAN.md
    - packages/opencascade-convert/src/occt/document.ts
    - packages/opencascade-convert/src/occt/assembly.ts
    - packages/opencascade-convert/src/occt/__tests__/document-reader-settings.test.ts
    - frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts

key-decisions:
  - 'Treat end-user part names as a first-class output: STEP label -> glTF node name fallback'
  - 'Keep BOM minimal (name + quantity) while preserving assembly structure elsewhere'

patterns-established:
  - 'Output metadata naming should be stable and human-readable, not instance IDs'

# Metrics
duration: 17h 25m
completed: 2026-02-06
---

# Phase 01 Plan 03: Browser Conversion E2E Verification Summary

**End-to-end browser STEP conversion verified with downloadable zip bundle outputs and meaningful metadata names across assemblyTree/nodeMap/BOM.**

## Performance

- **Duration:** 17h 25m
- **Started:** 2026-02-05T20:41:14Z
- **Completed:** 2026-02-06T14:06:21Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Verified the browser UX flow (convert progress, cancel/retry, download bundle) against real inputs.
- Fixed metadata naming so assemblyTree/nodeMap/BOM preserve meaningful names (not generic IDs).
- Made the checkpoint repeatable by clarifying the 15 MB sample constraint and keeping negative fixtures ephemeral.

## Task Commits

Each task was committed atomically (when it changed repo state):

1. **Task 1: Start the frontend dev server (background) and prep a test STEP file** - _no repo changes (runtime-only)_
2. **Task 2: Browser STEP conversion + bundled outputs (human verify)**
   - `8306787` (fix) Adjust checkpoint instructions for the 15 MB cap
   - `ddbe8b7` (fix) Preserve STEP part names in metadata
   - `c3de26d` (fix) Improve STEP label name extraction
   - `726d274` (fix) Derive metadata names from glTF node names
   - `47ed8f4` (fix) Apply pretty names to assemblyTree/nodeMap/BOM
3. **Task 3: Stop the dev server and clean up runtime artifacts** - _no repo changes (runtime-only)_

**Plan metadata:** _committed as docs(01-03) after SUMMARY/STATE updates_

## Files Created/Modified

- `.planning/phases/01-browser-conversion-outputs/01-03-PLAN.md` - Human verification instructions (15 MB cap guidance)
- `packages/opencascade-convert/src/occt/document.ts` - Document reader settings / name preservation plumbing
- `packages/opencascade-convert/src/occt/assembly.ts` - Better STEP label name extraction
- `packages/opencascade-convert/src/occt/__tests__/document-reader-settings.test.ts` - Regression coverage for name preservation
- `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts` - Name derivation + normalization during bundle metadata build

## Decisions Made

- Prefer STEP labels for part names and fall back to glTF node names to keep metadata human-meaningful across sources.
- Keep BOM output minimal (name + quantity) while relying on assemblyTree/nodeMap for structure.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected checkpoint instructions to avoid >15 MB repo samples**

- **Found during:** Task 2 (human verification)
- **Issue:** Repo sample paths referenced in Task 1 were expected to be blocked by the 15 MB cap.
- **Fix:** Updated `.planning/phases/01-browser-conversion-outputs/01-03-PLAN.md` guidance.
- **Verification:** Checkpoint steps now match app constraints.
- **Committed in:** `8306787`

**2. [Rule 1 - Bug] Metadata names were not preserved consistently across assemblyTree/nodeMap/BOM**

- **Found during:** Task 2 (human verification)
- **Issue:** Output metadata did not reliably carry meaningful part names, violating Phase 1 must-haves.
- **Fix:** Preserved STEP part names, improved STEP label extraction, added glTF-node fallback, and applied normalization across outputs.
- **Files modified:** `packages/opencascade-convert/src/occt/document.ts`, `packages/opencascade-convert/src/occt/assembly.ts`, `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`
- **Verification:** User-confirmed metadata JSON contains meaningful names for assemblyTree/nodeMap/BOM.
- **Committed in:** `ddbe8b7`, `c3de26d`, `726d274`, `47ed8f4`

---

**Total deviations:** 2 auto-fixed (2 bug fixes)
**Impact on plan:** Both fixes were required for correctness of the Phase 1 observable outputs; no scope creep.

## Issues Encountered

- Metadata naming required iterative refinement to match the checkpoint expectations; resolved via the fixes listed above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 1 observable truths are now verified end-to-end.
- Ready to begin Phase 2 (mesh quality baseline) planning/execution.

---

_Phase: 01-browser-conversion-outputs_
_Completed: 2026-02-06_
