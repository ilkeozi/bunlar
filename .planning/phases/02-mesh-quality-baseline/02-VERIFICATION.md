---
phase: 02-mesh-quality-baseline
verified: 2026-02-07T13:09:59Z
status: gaps_found
score: 5/6 must-haves verified
gaps:
  - truth: 'Explorer conversion detects triangle/primitive explosions post-write and performs bounded retry with coarser absolute tessellation'
    status: failed
    reason: 'Explorer worker converts once, never evaluates explosion thresholds, never retries, and always returns empty conversionWarnings.'
    artifacts:
      - path: 'frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts'
        issue: 'No MAX_TRIANGLES/MAX_PRIMITIVES policy, no attempt loop, no forced relative=false, no retry schedule, conversionWarnings is always [].'
    missing:
      - 'Post-write meshStats threshold check (MAX_TRIANGLES=5_000_000, MAX_PRIMITIVES=50_000)'
      - 'Bounded 3-attempt retry loop with deterministic coarsening schedule'
      - 'Structured conversionWarnings for retries/relative-forced-false/unresolved'
      - 'Force absolute tessellation in all attempts (relative=false)'
---

# Phase 2: Mesh Quality Baseline Verification Report

**Phase Goal:** Converted meshes render smoothly without triangle explosions on mid-range desktop Chrome.
**Verified:** 2026-02-07T13:09:59Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                     | Status     | Evidence                                                                                                                                                                                                                                                                             |
| --- | ----------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Explorer conversion uses absolute tessellation defaults (not relative)                    | ✓ VERIFIED | `frontend/src/app/features/climate-tech/assembly-viewer/hooks/useAssemblyFile.ts` sets `BASIC_TRIANGULATION.relative: false` and passes it to the worker. Library default is also `relative: false` (`packages/opencascade-convert/src/occt/triangulation.ts`).                      |
| 2   | Face merging is enabled where supported                                                   | ✓ VERIFIED | Best-effort `writer.SetMergeFaces(true)` in `packages/opencascade-convert/src/occt/writer-core.ts` for both GLB/GLTF. Step converter GLB writer also calls `SetMergeFaces(true)` when available in `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`. |
| 3   | Explorer conversion detects triangle/primitive explosions and retries with bounded policy | ✗ FAILED   | `frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts` does a single `triangulate` + `writeBuffer`, computes `meshStats`, but has no thresholds, no retry loop, and returns `conversionWarnings: []` always.                                   |
| 4   | Step converter has bounded retry-on-explosion policy                                      | ✓ VERIFIED | `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts` defines `TRIANGLE_EXPLOSION_THRESHOLDS` and runs a 3-attempt loop with deterministic coarsening and `relative: false`.                                                                              |
| 5   | Step converter persists `meshStats`/`conversionWarnings` into outputs                     | ✓ VERIFIED | `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts` embeds metadata via `injectAssetExtrasIntoGlb(..., { bunlarStepConverter: metadata })` and writes `${base}.metadata.json` containing `meshStats` + `conversionWarnings` into the zip.               |
| 6   | Dev perf overlay exists in dev builds                                                     | ✓ VERIFIED | `frontend/src/app/features/climate-tech/assembly-viewer/components/DevPerfOverlay.tsx` exists and is mounted dev-only in `frontend/src/app/features/climate-tech/assembly-viewer/visualizer/AssemblyCanvas.tsx` via `import.meta.env.DEV ? <DevPerfOverlay /> : null`.               |

**Score:** 5/6 truths verified

## Required Artifacts

| Artifact                                                                                     | Expected                                                  | Status                | Details                                                                                               |
| -------------------------------------------------------------------------------------------- | --------------------------------------------------------- | --------------------- | ----------------------------------------------------------------------------------------------------- |
| `packages/opencascade-convert/src/occt/writer-core.ts`                                       | Face merging defaults                                     | ✓ VERIFIED            | Guarded `SetMergeFaces(true)` for GLB/GLTF.                                                           |
| `frontend/src/app/features/climate-tech/assembly-viewer/hooks/useAssemblyFile.ts`            | Explorer absolute tessellation defaults + warning surface | ✓ VERIFIED            | `BASIC_TRIANGULATION` pins `relative: false`, deflections; dev-only `console.warn` if warnings exist. |
| `frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts` | Explorer bounded retry + warnings                         | ✗ STUB (behaviorally) | Substantive file, but missing the required explosion policy + retry + warnings generation.            |
| `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`             | Retry + persistence for step converter                    | ✓ VERIFIED            | Implements thresholds, attempt loop, persisted metadata and zip outputs.                              |
| `frontend/src/app/features/tools/step-converter/components/StepConverterOutputs.tsx`         | Post-success warning UI                                   | ✓ VERIFIED            | Warnings shown only when `download` exists and `status.state === 'success'`.                          |
| `frontend/src/app/features/climate-tech/assembly-viewer/components/DevPerfOverlay.tsx`       | Dev overlay component                                     | ✓ VERIFIED            | R3F `useFrame` sampling; throttled (~250ms); reads `gl.info.render`.                                  |
| `frontend/src/app/features/climate-tech/assembly-viewer/visualizer/AssemblyCanvas.tsx`       | Dev overlay mounted in dev only                           | ✓ VERIFIED            | `import.meta.env.DEV` guard around `<DevPerfOverlay />`.                                              |

## Key Link Verification

| From                                                                                         | To                                                                                           | Via                                                                              | Status  | Details                                                      |
| -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ------- | ------------------------------------------------------------ |
| `frontend/src/app/features/climate-tech/assembly-viewer/hooks/useAssemblyFile.ts`            | `frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts` | `new Worker(new URL(...))` + `postMessage({ triangulate: BASIC_TRIANGULATION })` | ✓ WIRED | Worker invoked with pinned triangulation defaults.           |
| `frontend/src/app/features/climate-tech/assembly-viewer/workers/assemblyConverter.worker.ts` | `opencascade-convert/browser`                                                                | `createConverter()` + `writeBuffer(..., 'glb', { nameFormat })`                  | ✓ WIRED | Conversion path is wired, but missing explosion policy.      |
| `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`             | persisted output metadata                                                                    | `injectAssetExtrasIntoGlb` + zip `${base}.metadata.json`                         | ✓ WIRED | `meshStats`/`conversionWarnings` are written to both places. |
| `frontend/src/app/features/tools/step-converter/components/StepConverterOutputs.tsx`         | warning state                                                                                | `conversionWarnings` + `meshStats` from controller                               | ✓ WIRED | Render guarded to post-success state.                        |
| `frontend/src/app/features/climate-tech/assembly-viewer/visualizer/AssemblyCanvas.tsx`       | `frontend/src/app/features/climate-tech/assembly-viewer/components/DevPerfOverlay.tsx`       | React import + `import.meta.env.DEV` guard                                       | ✓ WIRED | Dev-only overlay present.                                    |

## Requirements Coverage

| Requirement                                                                  | Status    | Blocking Issue                                                                                                                          |
| ---------------------------------------------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| MESH-01: Meshes suitable for real-time rendering on mid-range desktop Chrome | ✗ BLOCKED | Explorer conversion path lacks the bounded retry-on-explosion safeguard; smoothness requires human validation even after wiring exists. |
| MESH-02: Avoid triangle/mesh explosions while maintaining visual fidelity    | ✗ BLOCKED | No explosion detection/retry on the Explorer conversion path (only Step Converter path has it).                                         |

## Anti-Patterns Found

None detected in the inspected Phase 02 implementation files (no TODO/placeholder/empty-handler patterns found).

## Human Verification Required

Even with code safeguards, the phase goal includes real interaction smoothness on a target device/browser class. This cannot be proven by static inspection alone.

### 1. Explorer Orbit Smoothness (Mid-range Desktop Chrome)

**Test:** `npx nx serve @bunlar/frontend`, open `/subjects/climate-tech/assembly-hierarchy-explorer`, load a representative assembly, orbit/pan/zoom for ~10s.
**Expected:** No visible triangle explosions; orbit stays responsive; overlay shows stable FPS and renderer load.
**Why human:** Performance feel + GPU/driver variability cannot be verified structurally.

## Gaps Summary

The Step Converter path has a deterministic explosion policy with bounded retries and persisted post-success warnings, and the Explorer has dev instrumentation plus absolute tessellation defaults. However, the Explorer conversion worker currently lacks the required explosion detection and retry loop, so the phase goal (avoid triangle explosions in the explorer on the target device class) is not structurally guaranteed.

---

_Verified: 2026-02-07T13:09:59Z_
_Verifier: Claude (gsd-verifier)_
