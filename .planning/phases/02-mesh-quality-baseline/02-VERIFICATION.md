---
phase: 02-mesh-quality-baseline
verified: 2026-02-07T15:47:13Z
status: human_needed
score: 6/6 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - 'Explorer conversion detects triangle/primitive explosions post-write and performs bounded retry with coarser absolute tessellation'
  gaps_remaining: []
  regressions: []
human_verification:
  - test: 'Assembly Explorer renders smoothly on mid-range desktop Chrome'
    expected: 'No visible triangle explosions; interaction remains responsive while orbiting/panning/zooming.'
    why_human: 'Performance feel and GPU/driver behavior cannot be proven by static inspection.'
  - test: 'Explosion mitigation triggers and warnings surface (debug)'
    expected: 'When a file exceeds thresholds, conversion retries up to 3 attempts and logs/returns structured conversionWarnings with meshStats.'
    why_human: "Requires a representative 'exploding' assembly to exercise retry paths."
---

# Phase 2: Mesh Quality Baseline Verification Report

**Phase Goal:** Converted meshes render smoothly without triangle explosions on mid-range desktop Chrome.
**Verified:** 2026-02-07T15:47:13Z
**Status:** human_needed
**Re-verification:** Yes — after gap closure

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                     | Status     | Evidence                                                                                                                                                                                                                                                                                 |
| --- | ----------------------------------------------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Explorer conversion uses absolute tessellation defaults (not relative)                    | ✓ VERIFIED | `frontend/src/app/features/climate-tech/assembly-viewer/hooks/useAssemblyFile.ts` sets `BASIC_TRIANGULATION.relative: false` and passes it to the worker. Library default is also `relative: false` (`packages/opencascade-convert/src/occt/triangulation.ts`).                          |
| 2   | Face merging is enabled where supported                                                   | ✓ VERIFIED | Best-effort `writer.SetMergeFaces(true)` in `packages/opencascade-convert/src/occt/writer-core.ts` for both GLB/GLTF. Step converter GLB writer also calls `SetMergeFaces(true)` when available in `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`.     |
| 3   | Explorer conversion detects triangle/primitive explosions and retries with bounded policy | ✓ VERIFIED | `frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts` computes `meshStats` post-write, checks `TRIANGLE_EXPLOSION_THRESHOLDS`, and retries up to 3 attempts with `relative: false`, returning structured `conversionWarnings` (retry/unresolved). |
| 4   | Step converter has bounded retry-on-explosion policy                                      | ✓ VERIFIED | `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts` defines `TRIANGLE_EXPLOSION_THRESHOLDS` and runs a 3-attempt loop with deterministic coarsening and `relative: false`.                                                                                  |
| 5   | Step converter persists `meshStats`/`conversionWarnings` into outputs                     | ✓ VERIFIED | `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts` embeds metadata via `injectAssetExtrasIntoGlb(..., { bunlarStepConverter: metadata })` and writes `${base}.metadata.json` containing `meshStats` + `conversionWarnings` into the zip.                   |
| 6   | Dev perf overlay exists in dev builds                                                     | ✓ VERIFIED | `frontend/src/app/features/climate-tech/assembly-viewer/components/DevPerfOverlay.tsx` exists and is mounted dev-only in `frontend/src/app/features/climate-tech/assembly-viewer/visualizer/AssemblyCanvas.tsx` via `import.meta.env.DEV ? <DevPerfOverlay /> : null`.                   |

**Score:** 6/6 truths verified

## Required Artifacts

| Artifact                                                                                     | Expected                                                  | Status     | Details                                                                                                                           |
| -------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `packages/opencascade-convert/src/occt/writer-core.ts`                                       | Face merging defaults                                     | ✓ VERIFIED | Guarded `SetMergeFaces(true)` for GLB/GLTF.                                                                                       |
| `frontend/src/app/features/climate-tech/assembly-viewer/hooks/useAssemblyFile.ts`            | Explorer absolute tessellation defaults + warning surface | ✓ VERIFIED | Posts `BASIC_TRIANGULATION` and resolves `meshStats` + `conversionWarnings` from the worker metadata response; dev-only warn log. |
| `frontend/src/app/features/climate-tech/assembly-viewer/workers/explosionPolicy.ts`          | Thresholds + schedule + predicate                         | ✓ VERIFIED | Exports `TRIANGLE_EXPLOSION_THRESHOLDS`, `isTriangleExplosion`, `getTriangulationForAttempt` (relative always `false`).           |
| `frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts` | Explorer bounded retry + warnings                         | ✓ VERIFIED | 3-attempt retry loop, post-write `meshStats`, structured warning codes, returns final GLB even if unresolved.                     |
| `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`             | Retry + persistence for step converter                    | ✓ VERIFIED | Still implements 3-attempt explosion mitigation and persists `meshStats`/`conversionWarnings` into GLB extras + `metadata.json`.  |
| `frontend/src/app/features/climate-tech/assembly-viewer/components/DevPerfOverlay.tsx`       | Dev overlay component                                     | ✓ VERIFIED | R3F `useFrame` sampling (~250ms) and `gl.info.render` stats.                                                                      |
| `frontend/src/app/features/climate-tech/assembly-viewer/visualizer/AssemblyCanvas.tsx`       | Dev overlay mounted in dev only                           | ✓ VERIFIED | `import.meta.env.DEV` guard around `<DevPerfOverlay />`.                                                                          |

## Key Link Verification

| From                                                                                         | To                                                                                           | Via                                                                              | Status  | Details                                                                                  |
| -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------------------- |
| `frontend/src/app/features/climate-tech/assembly-viewer/hooks/useAssemblyFile.ts`            | `frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts` | `new Worker(new URL(...))` + `postMessage({ triangulate: BASIC_TRIANGULATION })` | ✓ WIRED | Worker invoked with pinned triangulation defaults.                                       |
| `frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts` | `opencascade-convert/browser`                                                                | `createConverter()` + `writeBuffer(..., 'glb', { nameFormat })`                  | ✓ WIRED | Conversion path is wired; retry-on-explosion runs post-write via `meshStats` thresholds. |
| `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`             | persisted output metadata                                                                    | `injectAssetExtrasIntoGlb` + zip `${base}.metadata.json`                         | ✓ WIRED | `meshStats`/`conversionWarnings` are written to both places.                             |
| `frontend/src/app/features/tools/step-converter/components/StepConverterOutputs.tsx`         | warning state                                                                                | `conversionWarnings` + `meshStats` from controller                               | ✓ WIRED | Render guarded to post-success state.                                                    |
| `frontend/src/app/features/climate-tech/assembly-viewer/visualizer/AssemblyCanvas.tsx`       | `frontend/src/app/features/climate-tech/assembly-viewer/components/DevPerfOverlay.tsx`       | React import + `import.meta.env.DEV` guard                                       | ✓ WIRED | Dev-only overlay present.                                                                |

Notes:

- Explorer retry policy is implemented in `frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts` using `frontend/src/app/features/climate-tech/assembly-viewer/workers/explosionPolicy.ts`.

## Requirements Coverage

| Requirement                                                                  | Status        | Blocking Issue                                                                                                                             |
| ---------------------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| MESH-01: Meshes suitable for real-time rendering on mid-range desktop Chrome | ? NEEDS HUMAN | Requires runtime perf validation on representative assemblies and target hardware/browser.                                                 |
| MESH-02: Avoid triangle/mesh explosions while maintaining visual fidelity    | ? NEEDS HUMAN | Retry-on-explosion exists; need real models to confirm it eliminates visible explosions (or produces acceptable warnings when unresolved). |

## Anti-Patterns Found

None detected in the inspected Phase 02 implementation files (no TODO/placeholder/empty-handler patterns found).

## Human Verification Required

The structural safeguards for explosion mitigation now exist in both the Step Converter and Explorer conversion paths, but the phase goal is explicitly about smooth runtime behavior on a target device class.

### 1. Explorer Orbit Smoothness (Mid-range Desktop Chrome)

**Test:** `npx nx serve @bunlar/frontend`, open `/subjects/climate-tech/assembly-hierarchy-explorer`, load a representative assembly, orbit/pan/zoom for ~10s.
**Expected:** No visible triangle explosions; orbit stays responsive; dev perf overlay shows stable FPS and non-pathological draw calls/triangles.
**Why human:** Performance feel + GPU/driver variability cannot be verified structurally.

### 2. Explorer Explosion Mitigation (Force Retry Path)

**Test:** Load a known-heavy assembly that previously triggered explosions; watch dev console for `[assembly-viewer] conversionWarnings` and inspect warning `code` + `detail.meshStats`.
**Expected:** If thresholds are exceeded, warnings include `mesh/triangle-explosion-retry` (attempts 0/1) and possibly `mesh/triangle-explosion-unresolved` after attempt 2; final GLB still loads.
**Why human:** Needs an input that exceeds thresholds to exercise the retry/unresolved branches.

---

_Verified: 2026-02-07T15:47:13Z_
_Verifier: Claude (gsd-verifier)_
