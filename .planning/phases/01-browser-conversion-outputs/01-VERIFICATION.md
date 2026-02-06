---
phase: 01-browser-conversion-outputs
verified: 2026-02-06T14:11:37Z
status: gaps_found
score: 5/6 must-haves verified
gaps:
  - truth: 'Invalid/unsupported STEP inputs show actionable errors with stable error codes'
    status: failed
    reason: '`UNSUPPORTED_STEP_CONTENT` is defined and translated but is never emitted by the worker; empty/unsupported STEP content will fall back to `CONVERSION_FAILED`.'
    artifacts:
      - path: 'frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts'
        issue: "No code path produces `UNSUPPORTED_STEP_CONTENT`; `normalizeWorkerError()` maps `ValidationError` to `CONVERSION_FAILED` and there is no explicit 'no solids/assembly' detection."
    missing:
      - "Detect 'supported STEP container but no supported solids/assemblies' (e.g., empty roots/nodes or GLB has no meshes)"
      - "Emit structured worker error `{ code: 'UNSUPPORTED_STEP_CONTENT', message, detail? }` for that condition"
      - "(Optional) Tighten `normalizeWorkerError()` to map known 'no shapes' ValidationError/ConversionError messages to `UNSUPPORTED_STEP_CONTENT`"
---

# Phase 1: Browser Conversion + Outputs Verification Report

**Phase Goal:** Users can convert STEP in the browser and get GLB plus assembly metadata reliably.
**Verified:** 2026-02-06T14:11:37Z
**Status:** gaps_found
**Re-verification:** No (initial verification)

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                                      | Status   | Evidence                                                                                                                                                                                                                                                                                                                                                                        |
| --- | ---------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | User can select a STEP file (<= 15MB) and start conversion                                                 | VERIFIED | `frontend/src/app/features/tools/step-converter/components/StepConverterForm.tsx` restricts to `.step,.stp`; `frontend/src/app/features/tools/step-converter/hooks/useStepConverterBrowser.ts` validates extension + `MAX_BROWSER_STEP_BYTES = 15 * 1024 * 1024` from `frontend/src/app/features/tools/step-converter/utils.ts`.                                                |
| 2   | Conversion runs off the main thread with stage progress and cancel                                         | VERIFIED | `frontend/src/app/features/tools/step-converter/hooks/useStepConverterBrowser.ts` creates a `Worker(new URL('../workers/stepConverter.worker.ts', import.meta.url))`, listens for `PROGRESS` stages, and `onCancel()` terminates the worker and clears outputs while keeping the selected file.                                                                                 |
| 3   | On success, user downloads a single bundle containing GLB + metadata JSON                                  | VERIFIED | `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts` returns `{ bundleName: \`${base}.zip\`, bundleBytes }`; UI builds a single `application/zip`download in`frontend/src/app/features/tools/step-converter/hooks/useStepConverterBrowser.ts`and renders it in`frontend/src/app/features/tools/step-converter/components/StepConverterOutputs.tsx`. |
| 4   | Produced GLB embeds metadata under `asset.extras` and remains valid after injection                        | VERIFIED | `packages/opencascade-convert/src/occt/glb-metadata.ts` implements `injectAssetExtrasIntoGlb()`; unit tests in `packages/opencascade-convert/src/__tests__/glb-metadata.test.ts` assert GLB validity + chunk preservation; worker injects `{ bunlarStepConverter: metadata }` via `injectAssetExtrasIntoGlb` imported from `opencascade-convert/browser`.                       |
| 5   | Metadata includes `assemblyTree`/`nodeMap`/`bom`/`units`/`boundsMeters` and preserves names when available | VERIFIED | Worker constructs `metadata = { schemaVersion, assemblyTree, nodeMap, bom, units, boundsMeters }` and applies pretty-name overrides from GLB node names (`cleanGltfNodeName()` + OCAF entry mapping) in `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`.                                                                                       |
| 6   | Invalid/unsupported inputs show actionable errors with stable codes                                        | FAILED   | Pre-worker validation provides `FILE_TOO_LARGE`/`UNSUPPORTED_EXTENSION` codes (`frontend/src/app/features/tools/step-converter/hooks/useStepConverterBrowser.ts`). Worker emits `INVALID_STEP`, `OUT_OF_MEMORY`, `WASM_LOAD_FAILED`, `UNITS_SCALE_MISMATCH`, etc. but never emits `UNSUPPORTED_STEP_CONTENT` (defined + translated, but unused).                                |

**Score:** 5/6 truths verified

### Required Artifacts

| Artifact                                                                             | Expected                                                 | Status   | Details                                                                                                    |
| ------------------------------------------------------------------------------------ | -------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------- |
| `packages/opencascade-convert/src/occt/glb-metadata.ts`                              | GLB JSON-chunk editing + `asset.extras` injection        | VERIFIED | Substantive implementation; merges existing extras; validates magic/length; 4-byte padding.                |
| `packages/opencascade-convert/src/__tests__/glb-metadata.test.ts`                    | Unit coverage for inject + error handling                | VERIFIED | Builds/validates GLBs; asserts merge + chunk preservation + invalid inputs throw.                          |
| `packages/opencascade-convert/src/browser/index.ts`                                  | Browser entry export for helper                          | VERIFIED | Re-exports `injectAssetExtrasIntoGlb` for `opencascade-convert/browser`.                                   |
| `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`     | Worker conversion + progress + bundle assembly           | VERIFIED | Implements `START` protocol, stage messages, metadata generation, GLB patch, ZIP via `fflate`.             |
| `frontend/src/app/features/tools/step-converter/hooks/useStepConverterBrowser.ts`    | UI controller: size cap + progress wiring + cancel/retry | VERIFIED | Extension/size checks, worker wiring, stage status, cancel terminates worker, creates zip download link.   |
| `frontend/src/app/features/tools/step-converter/components/StepConverterForm.tsx`    | STEP-only file input + cancel button behavior            | VERIFIED | File accept `.step,.stp`; cancel uses controller `onCancel` while loading.                                 |
| `frontend/src/app/features/tools/step-converter/components/StepConverterOutputs.tsx` | Bundle download CTA                                      | VERIFIED | Renders only a single download CTA for the bundle.                                                         |
| `frontend/src/app/pages/tools/StepConverterBrowserPage.tsx`                          | Route-level entry wired into app router                  | VERIFIED | Uses `useStepConverterBrowser()`; routed at `/tools/step-converter-browser` in `frontend/src/app/app.tsx`. |

### Key Link Verification

| From                                                                              | To                                                                                | Via                                                | Status | Details                                                                                             |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------- |
| `frontend/src/app/features/tools/step-converter/hooks/useStepConverterBrowser.ts` | `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`  | `new Worker(new URL(...))` + `postMessage`         | WIRED  | `START` messages drive worker conversion; `PROGRESS` updates stage UI; `DONE` returns bundle bytes. |
| `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`  | `opencascade-convert/browser`                                                     | `createConverter()` + `injectAssetExtrasIntoGlb()` | WIRED  | Worker imports both converter and GLB extras injector from browser entry.                           |
| `/tools/step-converter-browser`                                                   | `frontend/src/app/features/tools/step-converter/hooks/useStepConverterBrowser.ts` | Route renders page + hooks                         | WIRED  | Route exists in `frontend/src/app/app.tsx`; page calls the hook.                                    |

### Requirements Coverage

| Requirement | Status    | Blocking Issue                                                                                   |
| ----------- | --------- | ------------------------------------------------------------------------------------------------ |
| CONV-01     | SATISFIED | -                                                                                                |
| CONV-02     | SATISFIED | -                                                                                                |
| CONV-03     | SATISFIED | -                                                                                                |
| CONV-04     | SATISFIED | -                                                                                                |
| CONV-05     | BLOCKED   | Missing emission of `UNSUPPORTED_STEP_CONTENT` for supported-but-empty/unsupported STEP content. |
| OUT-01      | SATISFIED | -                                                                                                |
| OUT-02      | SATISFIED | -                                                                                                |

### Anti-Patterns Found

No obvious stub patterns (TODO/placeholder/empty handlers) found in the Phase 1 artifacts.

### Gaps Summary

The browser conversion flow is present and wired (STEP-only + 15MB cap, worker progress/cancel, zip bundle containing `{base}.glb` and `{base}.metadata.json`, and GLB metadata embedded under `asset.extras`). The remaining blocker for Phase 1's "actionable errors" success criteria is that the error code `UNSUPPORTED_STEP_CONTENT` is never produced by the worker, so a valid-but-empty STEP container will likely surface as a generic `CONVERSION_FAILED` instead of a stable, specific code.

---

_Verified: 2026-02-06T14:11:37Z_
_Verifier: Claude (gsd-verifier)_
