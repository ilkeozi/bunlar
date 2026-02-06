---
phase: 01-browser-conversion-outputs
verified: 2026-02-06T17:12:05Z
status: passed
score: 6/6 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - 'Invalid/unsupported STEP inputs show actionable errors with stable error codes'
  gaps_remaining: []
  regressions: []
---

# Phase 1: Browser Conversion + Outputs Verification Report

**Phase Goal:** Users can convert STEP in the browser and get GLB plus assembly metadata reliably.
**Verified:** 2026-02-06T17:12:05Z
**Status:** passed
**Re-verification:** Yes — after gap-closure plan 01-04

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                                    | Status     | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| --- | -------------------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | User can select a STEP file (<= 15MB) and start conversion                                               | ✓ VERIFIED | `frontend/src/app/features/tools/step-converter/components/StepConverterForm.tsx` accepts `.step,.stp`; `frontend/src/app/features/tools/step-converter/utils.ts` sets `MAX_BROWSER_STEP_BYTES = 15 * 1024 * 1024`; `frontend/src/app/features/tools/step-converter/hooks/useStepConverterBrowser.ts` validates extension + size on selection and submit.                                                                                                                                                                                                                                                                                                                                                                                                 |
| 2   | Conversion runs off the main thread with stage progress and cancel                                       | ✓ VERIFIED | `frontend/src/app/features/tools/step-converter/hooks/useStepConverterBrowser.ts` starts a module `Worker(new URL('../workers/stepConverter.worker.ts', import.meta.url))`, updates UI from `PROGRESS` stage messages, and `onCancel()` terminates worker + clears outputs (keeping selected file).                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 3   | On success, user downloads a single bundle containing GLB + metadata JSON                                | ✓ VERIFIED | `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts` builds a zip with `${base}.glb` and `${base}.metadata.json` via `zipSync(...)` and posts `DONE` with `{ bundleName: `${base}.zip`, bundleBytes }`; UI creates a single `application/zip` download link in `frontend/src/app/features/tools/step-converter/hooks/useStepConverterBrowser.ts` and renders it in `frontend/src/app/features/tools/step-converter/components/StepConverterOutputs.tsx`.                                                                                                                                                                                                                                                                      |
| 4   | Produced GLB embeds metadata under `asset.extras` and remains valid after injection                      | ✓ VERIFIED | Worker calls `injectAssetExtrasIntoGlb(glb, { bunlarStepConverter: metadata })` in `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`; injection implementation is in `packages/opencascade-convert/src/occt/glb-metadata.ts` and preserves existing `asset.extras` while rebuilding GLB chunks/length correctly.                                                                                                                                                                                                                                                                                                                                                                                                           |
| 5   | Metadata includes `assemblyTree`/`nodeMap`/`bom`/`units`/`bounds` and preserves names when available     | ✓ VERIFIED | Worker constructs `metadata = { schemaVersion, assemblyTree, nodeMap, bom, units, boundsMeters }` in `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`; it requests `preserveNames: true` on STEP read and overrides node/BOM names from GLB node names (OCAF entry mapping + `cleanGltfNodeName(...)`) when present.                                                                                                                                                                                                                                                                                                                                                                                                      |
| 6   | Invalid/unsupported inputs show actionable errors with stable codes including `UNSUPPORTED_STEP_CONTENT` | ✓ VERIFIED | Pre-worker validation emits `UNSUPPORTED_EXTENSION` / `FILE_TOO_LARGE` in `frontend/src/app/features/tools/step-converter/hooks/useStepConverterBrowser.ts`; worker explicitly emits `UNSUPPORTED_STEP_CONTENT` for supported-but-empty STEP containers via `throw { __code: 'UNSUPPORTED_STEP_CONTENT', detail }` when node map is empty (pre-export) or GLB has no usable geometry (post-export) in `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`. UI surfaces stable code via `data-error-code` in `frontend/src/app/features/tools/step-converter/components/StepConverterForm.tsx`. Regression coverage exists in `frontend-e2e/src/step-converter-browser.spec.ts` using `frontend-e2e/src/fixtures/empty.step`. |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact                                                                             | Expected                                                                             | Status     | Details                                                                                                                                                 |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`     | Web-worker conversion, progress protocol, zip bundle, stable error codes             | ✓ VERIFIED | Emits `PROGRESS`/`DONE`/`ERROR`; builds bundle; injects `asset.extras`; detects unsupported content and emits `UNSUPPORTED_STEP_CONTENT` with `detail`. |
| `frontend/src/app/features/tools/step-converter/hooks/useStepConverterBrowser.ts`    | Browser controller: STEP-only validation, 15MB cap, progress/cancel, download wiring | ✓ VERIFIED | Validates `.step/.stp` + size cap; uses worker; updates stage; cancel terminates worker; errors surface as `{ code, message }`.                         |
| `frontend/src/app/features/tools/step-converter/components/StepConverterForm.tsx`    | STEP-only file input, conversion controls, stable error-code surface                 | ✓ VERIFIED | File input `accept=".step,.stp"`; status container uses `data-testid` + `data-error-code={status.error.code}`.                                          |
| `frontend/src/app/features/tools/step-converter/components/StepConverterOutputs.tsx` | Single bundle download CTA                                                           | ✓ VERIFIED | Renders download only when `download` exists (no partial outputs on error).                                                                             |
| `packages/opencascade-convert/src/occt/glb-metadata.ts`                              | GLB `asset.extras` injection without corrupting GLB                                  | ✓ VERIFIED | Parses GLB header/chunks, rewrites JSON chunk with 4-byte padding, preserves other chunks, updates length.                                              |
| `frontend/src/app/pages/tools/StepConverterBrowserPage.tsx`                          | Route-level page wiring hook + UI                                                    | ✓ VERIFIED | Calls `useStepConverterBrowser(t)` and renders form + outputs.                                                                                          |
| `frontend/src/app/app.tsx`                                                           | Router link for browser converter                                                    | ✓ VERIFIED | Route exists at `/tools/step-converter-browser`.                                                                                                        |
| `frontend-e2e/src/fixtures/empty.step`                                               | Syntactically valid empty STEP fixture                                               | ✓ VERIFIED | Minimal AP203 STEP with product definition but no geometry.                                                                                             |
| `frontend-e2e/src/step-converter-browser.spec.ts`                                    | Regression for `UNSUPPORTED_STEP_CONTENT` + no bundle                                | ✓ VERIFIED | Asserts `data-error-code="UNSUPPORTED_STEP_CONTENT"` and no “Download bundle” CTA.                                                                      |

### Key Link Verification

| From                                                                              | To                                                                               | Via                                                      | Status | Details                                                                                                                                                   |
| --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `frontend/src/app/features/tools/step-converter/hooks/useStepConverterBrowser.ts` | `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts` | `new Worker(...)` + `postMessage({ type: 'START' })`     | WIRED  | Worker lifecycle is owned by hook; `PROGRESS` stages update UI; `DONE` yields bundle bytes; `ERROR` rejects with structured error.                        |
| `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`  | `WorkerError.error.code = 'UNSUPPORTED_STEP_CONTENT'`                            | `throw Error + __code + detail` then forced-code mapping | WIRED  | Unsupported content is detected both pre-export (empty node map) and post-export (meshless/positionless GLB), and forced-code mapping preserves `detail`. |
| `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`  | `packages/opencascade-convert/src/occt/glb-metadata.ts`                          | `injectAssetExtrasIntoGlb(...)`                          | WIRED  | Worker embeds `bunlarStepConverter` metadata under `asset.extras`.                                                                                        |
| `frontend/src/app/features/tools/step-converter/components/StepConverterForm.tsx` | `frontend-e2e/src/step-converter-browser.spec.ts`                                | `data-testid` + `data-error-code`                        | WIRED  | E2E assertions target stable error code (not translated copy).                                                                                            |

### Requirements Coverage

| Requirement | Status      | Blocking Issue |
| ----------- | ----------- | -------------- |
| CONV-01     | ✓ SATISFIED | -              |
| CONV-02     | ✓ SATISFIED | -              |
| CONV-03     | ✓ SATISFIED | -              |
| CONV-04     | ✓ SATISFIED | -              |
| CONV-05     | ✓ SATISFIED | -              |
| OUT-01      | ✓ SATISFIED | -              |
| OUT-02      | ✓ SATISFIED | -              |

### Anti-Patterns Found

No blocker stub patterns found in the Phase 01 browser converter artifacts (no TODO/placeholder flows; outputs are only produced on `DONE`).

### Human Verification Required

1. STEP conversion end-to-end

**Test:** Open `/tools/step-converter-browser`, upload a real `.step/.stp` under 15MB, click “Convert now”.
**Expected:** Stage labels advance (`parsing`→`meshing`→`writing`→`metadata`→`packaging`), then a single “Download bundle” link appears.
**Why human:** Requires running WASM worker and validating UX timing.

2. Bundle contents + GLB embedded extras

**Test:** Download the zip; confirm it contains `<name>.glb` and `<name>.metadata.json`. Inspect the GLB JSON chunk and confirm `asset.extras.bunlarStepConverter` exists and matches the downloaded metadata JSON (schemaVersion + assemblyTree/nodeMap/bom/units/boundsMeters).
**Expected:** Both files exist; GLB remains loadable; `asset.extras` includes embedded metadata.
**Why human:** Requires unzipping and optionally inspecting/loading GLB.

3. Error surfaces are stable/actionable

**Test:** Upload a non-STEP file and a >15MB STEP; confirm the UI shows stable error codes (`UNSUPPORTED_EXTENSION`, `FILE_TOO_LARGE`). Upload `frontend-e2e/src/fixtures/empty.step` and confirm `data-error-code="UNSUPPORTED_STEP_CONTENT"` and no download CTA.
**Expected:** Correct code surfaced; no partial bundle outputs on error.
**Why human:** Confirms UI behavior and messaging in an actual browser session.

---

_Verified: 2026-02-06T17:12:05Z_
_Verifier: Claude (gsd-verifier)_
