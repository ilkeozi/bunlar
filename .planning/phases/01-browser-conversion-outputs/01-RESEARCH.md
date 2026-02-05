# Phase 01: Browser Conversion + Outputs - Research

**Researched:** 2026-02-05
**Domain:** Browser CAD conversion (OpenCascade.js WASM) in Web Workers + ZIP bundling + GLB metadata embedding
**Confidence:** MEDIUM

## Summary

This phase is mostly about making the existing browser worker conversion production-grade: enforce a hard 15MB cap early, run conversion fully off the main thread, provide stage-based progress, and guarantee clean cancellation (no outputs) and actionable failures.

The output requirements (single downloadable bundle, GLB output with embedded metadata + JSON sidecar) are best met by (1) generating GLB + assembly metadata inside the worker, (2) embedding the metadata into the GLB JSON chunk (`asset.extras`) using a small, spec-correct GLB rewriter, and (3) packaging `*.glb` + `*.json` into a ZIP archive in the worker using a purpose-built ZIP library.

**Primary recommendation:** Use `opencascade-convert/browser` in a dedicated worker, implement cancel via `worker.terminate()`, embed metadata via a spec-correct GLB JSON-chunk patch, and build the download bundle ZIP with `fflate`.

## Standard Stack

### Core

| Library                       | Version               | Purpose                                           | Why Standard                                                                                        |
| ----------------------------- | --------------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `opencascade.js`              | `^2.0.0-beta.b5ff984` | OCCT CAD kernel in WASM                           | Required for STEP parsing/triangulation/export in browser (already used via `opencascade-convert`). |
| `opencascade-convert/browser` | workspace package     | STEP/IGES buffer conversion + metadata extraction | Existing project wrapper around OCCT; preserves names and produces BOM/nodeMap.                     |
| `Web Worker` (module worker)  | browser API           | Off-main-thread conversion + isolation            | Only reliable way to keep UI responsive and enable hard cancel.                                     |

### Supporting

| Library  | Version  | Purpose                        | When to Use                                                           |
| -------- | -------- | ------------------------------ | --------------------------------------------------------------------- |
| `fflate` | `^0.8.2` | ZIP creation in browser/worker | Create a single downloadable bundle (`.zip`) with GLB + JSON sidecar. |

### Alternatives Considered

| Instead of | Could Use                 | Tradeoff                                                                                                                                                   |
| ---------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fflate`   | `@zip-js/zip-js` (zip.js) | Strong streaming APIs and large-file features, but larger/less tree-shakeable for a simple 2-file bundle; keep as fallback if streaming becomes mandatory. |
| `fflate`   | `jszip`                   | Very common, but heavier and typically slower/more memory-hungry for large binary payloads; less ideal inside a worker for big GLBs.                       |

**Installation:**

```bash
npm install fflate
```

## Architecture Patterns

### Recommended Project Structure

Keep conversion, embedding, and packaging in the worker; keep UI concerns in the hook.

```
frontend/src/app/features/tools/step-converter/
├── hooks/
│   └── useStepConverterBrowser.ts
├── workers/
│   ├── stepConverter.worker.ts
│   └── stepBundle.worker.ts        # recommended: new worker for zip+metadata embedding
├── lib/
│   ├── glbPatch.ts                 # GLB JSON-chunk patcher (spec-correct)
│   ├── stepErrors.ts               # error taxonomy + mapping
│   └── stepMetadata.ts             # schema shaping (BOM + nodeMap + assembly tree)
└── types.ts
```

### Pattern 1: Stage-Based Worker Protocol (Request/Progress/Result)

**What:** A single request produces a single result (ZIP bundle) or a single failure; progress is emitted at stage boundaries.

**When to use:** Always, because OCCT calls are synchronous and cannot provide smooth progress.

**Recommended message schema:**

```ts
// main -> worker
type StartMsg = {
  type: 'START';
  id: string; // stable request id (e.g., crypto.randomUUID())
  fileName: string;
  fileSize: number;
  inputFormat: 'step' | 'iges';
  input: ArrayBuffer; // transferred
  options: {
    triangulate: {
      linearDeflection?: number;
      angularDeflection?: number;
      relative?: boolean;
      parallel?: boolean;
    };
  };
};

// worker -> main
type ProgressMsg = {
  type: 'PROGRESS';
  id: string;
  stage:
    | 'load-wasm'
    | 'parse'
    | 'triangulate'
    | 'write-glb'
    | 'metadata'
    | 'embed-metadata'
    | 'zip';
};

type DoneMsg = {
  type: 'DONE';
  id: string;
  zipName: string;
  zipBytes: ArrayBuffer; // transferred
};

type ErrorMsg = {
  type: 'ERROR';
  id: string;
  error: {
    code:
      | 'FILE_TOO_LARGE'
      | 'UNSUPPORTED_EXTENSION'
      | 'INVALID_STEP'
      | 'UNSUPPORTED_STEP_CONTENT'
      | 'WASM_LOAD_FAILED'
      | 'CONVERSION_FAILED'
      | 'METADATA_FAILED'
      | 'GLB_PATCH_FAILED'
      | 'ZIP_FAILED'
      | 'OUT_OF_MEMORY';
    message: string; // user-facing
    detail?: Record<string, unknown>; // for logging/diagnostics
  };
};
```

**Cancel pattern (locked decision “immediately stop”):**

- Implement cancel by calling `worker.terminate()` from the main thread.
- Rationale: OCCT triangulation/write are synchronous; an in-band `CANCEL` message cannot preempt those calls reliably.
- After cancel: keep `file` in React state; recreate the worker on retry.

### Pattern 2: Embed Metadata in GLB via `asset.extras`

**What:** Patch the GLB JSON chunk, inserting a single namespaced metadata object at `asset.extras`.

**When to use:** Always, to satisfy OUT-02 and keep metadata co-located with the binary model.

**Where to embed (prescriptive):**

- `gltf.asset.extras.bunlarStepConverter = <metadata>`

This avoids polluting standard fields and is safe for glTF clients (unknown extras are ignored).

### Pattern 3: Single Download Bundle (ZIP) with GLB + JSON Sidecar

**What:** Produce exactly one downloadable `.zip` file containing:

- `<base>.glb` (with embedded metadata)
- `<base>.metadata.json` (same metadata; canonical for parsing)

**When to use:** Always, per locked decision “single download bundle”.

### Anti-Patterns to Avoid

- **Soft cancel (in-band abort flag only):** cannot stop OCCT synchronous work; violates “cancel stops immediately”.
- **Multiple downloads (separate links for GLB/BOM/nodeMap):** violates “single download bundle”.
- **Embedding metadata as ad-hoc binary chunk:** GLB allows unknown chunks, but most tooling won’t preserve them; `asset.extras` is the interoperable path.
- **Base64-embedding BIN into `.gltf` JSON:** inflates output by ~33% and increases memory pressure; use `.glb`.

## Don't Hand-Roll

| Problem                       | Don't Build        | Use Instead                    | Why                                                                                                           |
| ----------------------------- | ------------------ | ------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| ZIP archive writing           | Custom ZIP encoder | `fflate`                       | ZIP format has edge cases (CRC, central directory, timestamps). `fflate` is small, fast, and worker-friendly. |
| glTF/GLB “full parser/writer” | A full glTF SDK    | Minimal GLB JSON-chunk patcher | Only need to edit JSON chunk; full SDK adds weight and more moving parts.                                     |

**Key insight:** Memory is the main constraint in browser CAD conversion; avoid solutions that duplicate large buffers (base64, multiple intermediate copies) or that run on the main thread.

## Common Pitfalls

### Pitfall 1: Progress messages don’t show during meshing

**What goes wrong:** UI appears frozen even though it’s in a worker.
**Why it happens:** OCCT triangulation/export are synchronous; the worker cannot `postMessage` while inside the WASM call.
**How to avoid:** Use stage-based progress (emit before each heavy call) and set expectations (e.g., “Meshing (this may take a while)”).
**Warning signs:** No progress events between `triangulate` start/end on large assemblies.

### Pitfall 2: Cancel doesn’t actually stop work

**What goes wrong:** User clicks cancel, but CPU keeps running and output eventually appears.
**Why it happens:** In-band cancel cannot preempt a synchronous WASM call.
**How to avoid:** Implement cancel via `worker.terminate()` and discard any late messages by request id.
**Warning signs:** CPU stays high after cancel; conversion completes anyway.

### Pitfall 3: WASM asset fails to load in a worker build

**What goes wrong:** `createConverter()` rejects; errors like failed fetch for `.wasm`.
**Why it happens:** Bundler not configured to treat `.wasm` as a URL asset; wrong base path; missing caching headers.
**How to avoid:** Follow OpenCascade.js bundler guidance (“import the .wasm assets so bundler fingerprints and caches them”); verify worker can fetch the emitted wasm file in dev and prod.
**Warning signs:** Works in dev but fails in `vite build`/preview; network 404 for `.wasm`.

### Pitfall 4: Units/scale mismatch (mm vs m)

**What goes wrong:** Converted model is 1000x too big/small.
**Why it happens:** glTF units are meters; STEP may be mm/in; conversion pipeline must apply correct length-unit scaling.
**How to avoid:** Verify exported scale with known reference models; if needed, configure `RWGltf_CafWriter` coordinate/length conversion using `RWMesh_CoordinateSystemConverter` and/or read document length units from XCAF.
**Warning signs:** Bounding box dimensions inconsistent with known part size.

### Pitfall 5: Metadata too big or causes GLB corruption

**What goes wrong:** GLB won’t load in viewers after embedding metadata.
**Why it happens:** GLB chunk lengths/padding incorrect; JSON chunk not padded with 0x20; file length not updated.
**How to avoid:** Implement GLB rewrite exactly per spec: 12-byte header; JSON chunk first; 4-byte alignment; JSON padding with spaces, BIN padding with zeros.
**Warning signs:** GLTFLoader throws JSON parse errors; viewers show “invalid GLB”.

## Code Examples

### Create ZIP Bundle in Worker (Two Files)

```ts
// Source: https://github.com/101arrowz/fflate (README)
import { strToU8, zipSync } from 'fflate';

export function makeZipBundle(params: {
  glbName: string;
  glbBytes: Uint8Array;
  metadataName: string;
  metadataJson: unknown;
}): Uint8Array {
  const metadataBytes = strToU8(JSON.stringify(params.metadataJson));
  return zipSync(
    {
      [params.glbName]: params.glbBytes,
      [params.metadataName]: metadataBytes,
    },
    // For GLB (already binary) and JSON, compression level 0–1 is usually fine.
    // Keep it low to reduce CPU time.
    { level: 1 }
  );
}
```

### Patch GLB JSON Chunk to Embed `asset.extras`

```ts
// Source (GLB chunk rules): https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#glb-file-format-specification
// - JSON chunk type: 0x4E4F534A, padded with 0x20
// - BIN chunk type:  0x004E4942, padded with 0x00
// - 4-byte alignment required

const GLB_HEADER_LEN = 12;
const CHUNK_HEADER_LEN = 8;
const CHUNK_JSON = 0x4e4f534a;
const CHUNK_BIN = 0x004e4942;

export function patchGlbAssetExtras(
  glb: Uint8Array,
  extrasPatch: unknown
): Uint8Array {
  // Minimal algorithm:
  // 1) Validate magic/version.
  // 2) Locate the first JSON chunk.
  // 3) Parse JSON, apply `asset.extras` patch.
  // 4) Re-encode JSON (UTF-8), pad with 0x20 to 4-byte boundary.
  // 5) Copy through remaining chunks (BIN and any unknown chunks) without re-encoding.
  // 6) Rewrite chunk lengths + total length.
  throw new Error(
    'Implement per spec; keep this function small and heavily tested.'
  );
}
```

### Configure Length Units (If Scale Fix Needed)

```ts
// Source: https://ocjs.org/reference-docs/classes/RWMesh_CoordinateSystemConverter.html
// Source: https://ocjs.org/reference-docs/classes/RWGltf_CafWriter.html
// - RWMesh_CoordinateSystemConverter has InputLengthUnit/OutputLengthUnit setters.
// - RWGltf_CafWriter exposes SetCoordinateSystemConverter().

// Pseudocode only; confirm exact binding behavior in opencascade.js.
const writer = new oc.RWGltf_CafWriter(file, true);
const conv = writer.ChangeCoordinateSystemConverter();
conv.SetOutputLengthUnit(1.0); // meters
// Optionally set input length unit if you can read it from XCAFDoc_DocumentTool.GetLengthUnit.
writer.SetCoordinateSystemConverter(conv);
```

## State of the Art

| Old Approach               | Current Approach                               | When Changed                 | Impact                                                           |
| -------------------------- | ---------------------------------------------- | ---------------------------- | ---------------------------------------------------------------- |
| JSZip for browser zipping  | `fflate` / `zip.js` with worker/stream support | ~2021–2024 ecosystem shift   | Better performance and smaller bundles for large binary outputs. |
| In-band cancellation flags | Terminate the worker                           | Web Worker era best practice | Only reliable cancel for synchronous WASM workloads.             |

**Deprecated/outdated:**

- Base64 embedding binary into `.gltf` for download: increases output size and peak memory; prefer `.glb`.

## Open Questions

1. **Exact unit/scale handling end-to-end (STEP units → glTF meters)**

   - What we know: glTF linear units are meters; OCCT writer exposes length-unit conversion (`RWMesh_CoordinateSystemConverter`).
   - What's unclear: whether current pipeline already applies correct scaling by default for STEP/IGES units.
   - Recommendation: plan explicit verification with known-unit fixtures; implement scale correction only if tests show mismatch.

2. **“Node map one-to-one with mesh entries” interpretation**
   - What we know: `opencascade-convert` produces an assembly graph (node ids are stable path strings) and GLB nodes contain OCAF entries in their names.
   - What's unclear: whether “mesh entries” refers to glTF nodes-with-mesh, glTF mesh indices, or both.
   - Recommendation: define `nodeMap` as `nodeId -> gltfNodeIndex (+ meshIndex)` and enforce uniqueness; treat duplicates/missing as actionable errors.

## Sources

### Primary (HIGH confidence)

- Khronos glTF 2.0 spec (GLB chunk structure, padding/alignment, units): https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
- OpenCascade.js bundler guide (WASM as imported asset): https://ocjs.org/docs/getting-started/configure-bundler
- OpenCascade.js file size & caching notes (WASM size/compile cost): https://ocjs.org/docs/getting-started/file-size
- OpenCascade.js reference docs (writer + coordinate/length converter):
  - https://ocjs.org/reference-docs/classes/RWGltf_CafWriter.html
  - https://ocjs.org/reference-docs/classes/RWMesh_CoordinateSystemConverter.html
- fflate ZIP API (zipSync/Zip streams, async cancel): https://github.com/101arrowz/fflate

### Secondary (MEDIUM confidence)

- zip.js (streaming ZIP writer examples): https://github.com/gildas-lormeau/zip.js
- JSZip (baseline ZIP API): https://github.com/Stuk/jszip

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - verified via repo dependencies + official library docs.
- Architecture: MEDIUM - worker/ZIP/GLB patterns are well-specified; unit scaling behavior needs validation in this codebase.
- Pitfalls: HIGH - directly implied by specs + known WASM/worker constraints.

**Research date:** 2026-02-05
**Valid until:** 2026-03-07
