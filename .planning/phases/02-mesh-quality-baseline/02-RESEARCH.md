# Phase 02: Mesh Quality Baseline - Research

**Researched:** 2026-02-07
**Domain:** OCCT/OpenCascade.js triangulation + glTF export tuning for real-time viewing
**Confidence:** MEDIUM

## Summary

Phase 02 success depends mostly on controlling tessellation at conversion time (OCCT meshing) and on keeping the resulting glTF structurally cheap to render/interact with (draw calls, primitive counts, triangle counts). In this repo, tessellation is done explicitly via `BRepMesh_IncrementalMesh` (OpenCascade.js) before export, and export is handled by `RWGltf_CafWriter`. The primary runtime problems (“triangle explosions”, sluggish orbit, sluggish selection) are downstream of overly aggressive meshing settings and/or an unbounded “quality” policy.

The repo already exposes the core meshing knobs (`linearDeflection`, `angularDeflection`, `relative`, `parallel`) and already embeds metadata into GLB via `asset.extras.bunlarStepConverter`. Phase 02 should implement: (1) a deterministic baseline meshing profile (quality-first), (2) post-conversion geometry accounting (triangles, vertices, primitives, nodes), (3) a “triangle explosion” retry loop that coarsens meshing only when thresholds are exceeded, and (4) persisted warnings (`conversionWarnings[]`) in metadata.

**Primary recommendation:** Use `BRepMesh_IncrementalMesh_2()` for meshing + a post-write GLB triangle counter; if triangles exceed the chosen explosion threshold, retry conversion with coarser deflections (bounded retries), then persist warnings into `asset.extras.bunlarStepConverter.conversionWarnings[]`.

## Standard Stack

### Core

| Library                                | Version                | Purpose                                             | Why Standard                                                                              |
| -------------------------------------- | ---------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `opencascade.js`                       | `2.0.0-beta.b5ff984`   | OCCT in WASM; STEP/IGES read; meshing; glTF writing | Existing converter stack in repo; exposes OCCT meshing + `RWGltf_CafWriter`               |
| OCCT mesher `BRepMesh_IncrementalMesh` | (via `opencascade.js`) | Tessellation control (triangle density/quality)     | The only reliable place to control triangle counts without geometry-destroying decimation |
| OCCT writer `RWGltf_CafWriter`         | (via `opencascade.js`) | glTF/GLB export from XCAF doc                       | Standard OCCT pipeline; supports name formats + face merging                              |

### Supporting

| Library              | Version    | Purpose                                          | When to Use                            |
| -------------------- | ---------- | ------------------------------------------------ | -------------------------------------- |
| `@react-three/fiber` | `^9.0.3`   | WebGL render loop for Explorer view              | FPS overlay + smooth orbit measurement |
| `three`              | `^0.171.0` | Renderer stats (`renderer.info`), geometry stats | Overlay + runtime validation           |
| `@react-three/drei`  | `^10.7.6`  | `useGLTF`, `OrbitControls`, `Loader`             | Explorer viewer already uses it        |
| `fflate`             | `^0.8.2`   | zip bundling of conversion outputs               | Step converter worker already uses it  |

### Alternatives Considered

| Instead of                          | Could Use                         | Tradeoff                                                                                                                             |
| ----------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Conversion-time tessellation tuning | Runtime decimation/simplification | High risk of mechanical artifacts (holes/cracks, lost sharp edges, normals issues); conflicts with locked “preserve fidelity” policy |

**Installation:** (already present)

```bash
npm install
```

## Architecture Patterns

### Recommended Project Structure

Conversion knobs and heuristics touch these locations:

```
packages/opencascade-convert/src/occt/
├── triangulation.ts       # BRepMesh_IncrementalMesh_2 settings + defaults
└── writer-core.ts         # RWGltf_CafWriter configuration

frontend/src/app/features/tools/step-converter/workers/
└── stepConverter.worker.ts # Browser conversion; GLB post-analysis; metadata injection

frontend/src/app/features/climate-tech/assembly-viewer/
├── workers/assemblyConverter.worker.ts # Uses opencascade-convert writeBuffer()
└── visualizer/AssemblyCanvas.tsx       # Dev FPS/debug overlay host
```

### Pattern 1: Two-Stage Conversion With Retry-on-Explosion

**What:** Convert once with baseline quality; compute triangle/primitive counts from GLB JSON; if “explosion” thresholds are exceeded, retry conversion with coarser meshing until it fits or retries are exhausted.

**When to use:** Always, because “triangle explosion” handling is locked policy (auto-adjust, warn after conversion, persist warnings).

**Key constraints (from CONTEXT):** preserve fidelity; only coarsen when thresholds are exceeded; warn post-conversion; persist warnings.

**Example (repo-adjacent pseudocode):**

```ts
// Source: frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts
// Pattern: convert -> analyze -> maybe retry -> embed warnings

const attempts: Array<{ triangulate: TriangulatePayload; reason: string }> = [
  { triangulate: baselineTriangulate, reason: 'baseline' },
  {
    triangulate: coarsen(baselineTriangulate, 1),
    reason: 'triangle-explosion-retry-1',
  },
  {
    triangulate: coarsen(baselineTriangulate, 2),
    reason: 'triangle-explosion-retry-2',
  },
];

const warnings: any[] = [];
let glb: Uint8Array | null = null;

for (const attempt of attempts) {
  glb = await convertStepDocToGlb({
    converter,
    docHandle,
    triangulate: attempt.triangulate,
  });
  const stats = summarizeGlbTriangles(glb);
  if (!isTriangleExplosion(stats)) break;
  warnings.push({
    code: 'TRIANGLE_EXPLOSION',
    message: `Triangle explosion detected (${stats.triangles} tris). Retrying with coarser meshing.`,
    detail: {
      attempt: attempt.reason,
      stats,
      triangulate: attempt.triangulate,
    },
  });
}
```

### Pattern 2: Pre-Mesh Bounding Box to Make Deflection “Unit-Aware”

**What:** Compute a `Bnd_Box` for the assembly shape before meshing; use it (plus STEP unit scale already read in the worker) to choose an absolute `linearDeflection` in input units.

**When to use:** When you need predictable quality across STEP unit systems (mm/cm/in/m) without relying on `relative` (which can explode on micro-edges).

**Example:**

```ts
// Source: node_modules/opencascade.js/dist/opencascade.full.d.ts (Bnd_Box, BRepBndLib)
// and packages/opencascade-convert/src/occt/triangulation.ts (compound assembly construction)

const box = new oc.Bnd_Box_1();
oc.BRepBndLib.AddOptimal(
  compound,
  box,
  /*useTriangulation*/ false,
  /*useShapeTolerance*/ true
);
const min = box.CornerMin();
const max = box.CornerMax();

// maxDim in input units
const maxDim = Math.max(
  Math.abs(max.X() - min.X()),
  Math.abs(max.Y() - min.Y()),
  Math.abs(max.Z() - min.Z())
);

// Choose an absolute chordal tolerance in meters, clamp, then convert to input units.
const targetChordalMeters = clamp(maxDimMeters * 2.5e-4, 5e-5, 1e-3);
const linearDeflectionInputUnits = targetChordalMeters / scaleToMeters;
```

### Anti-Patterns to Avoid

- **Auto-decimating to hit FPS:** violates locked “preserve mechanical fidelity”; use retry-on-explosion only.
- **Treating `angularDeflection` as degrees:** OCCT takes radians; wrong units can cause runaway triangles or severe faceting.
- **Turning on `relative` by default without clamps:** OCCT semantics scale deflection by edge size; tiny edges can drive deflection toward ~0 and explode triangles.

## Don't Hand-Roll

| Problem                   | Don't Build                      | Use Instead                                | Why                                                                               |
| ------------------------- | -------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------- |
| GLB asset extras patching | Custom GLB rewriter              | `injectAssetExtrasIntoGlb()`               | Already handles chunk padding/length correctness and merges `asset.extras` safely |
| Bounding box computation  | Manual traversal of mesh buffers | OCCT `Bnd_Box` + `BRepBndLib.AddOptimal()` | Uses exact B-Rep bounds pre-mesh; avoids needing triangles first                  |
| Tessellation              | Custom triangulator              | OCCT `BRepMesh_IncrementalMesh_2()`        | Handles curved surfaces + topology; standard CAD tessellation                     |

**Key insight:** Mesh simplification/decimation is where mechanical fidelity is most often silently destroyed; this phase should keep all geometry decisions inside OCCT tessellation plus writer grouping options.

## Common Pitfalls

### Pitfall 1: `relative=true` causes micro-edge explosions

**What goes wrong:** Relative deflection multiplies `linearDeflection` by each edge’s size; tiny edges yield tiny deflection values, forcing excessive subdivision and triangle blow-ups.
**Why it happens:** OCCT defines `isRelative` as: edge deflection = `theLinDeflection * size(edge)`; face deflection = max edge deflection.
**How to avoid:** Default to absolute, unit-aware `linearDeflection` (in input units) and use `relative` only when explicitly requested or when you can clamp the effective deflection.
**Warning signs:** Triangle counts jump by orders of magnitude on models with fillets/text/threads.

### Pitfall 2: “Explosion” detection after the wrong step

**What goes wrong:** You detect triangles too late (after packaging / UI), so the user already hit long hangs or OOM.
**Why it happens:** The worker currently packages zip and injects metadata after writing; explosion detection must occur immediately after GLB write, before heavy post-processing.
**How to avoid:** Parse GLB JSON immediately after writing (no BIN decode required for triangle counts).
**Warning signs:** Worker stalls on “packaging” or “metadata” when GLB is huge.

### Pitfall 3: Writer configuration mismatch between code paths

**What goes wrong:** Assembly Viewer uses `opencascade-convert`’s writer; Step Converter worker uses manual `RWGltf_CafWriter`; tuning one path doesn’t fix the other.
**Why it happens:** There are two export call sites.
**How to avoid:** Centralize writer settings in `packages/opencascade-convert/src/occt/writer-core.ts` and mirror them in `frontend/.../stepConverter.worker.ts` (or refactor worker to call `writeBuffer()` only).
**Warning signs:** Explorer is smooth but converter bundle preview is not (or vice versa).

## Code Examples

### Meshing: `BRepMesh_IncrementalMesh_2` (the only tessellation knob you reliably have)

```ts
// Source: node_modules/opencascade.js/dist/opencascade.full.d.ts (BRepMesh_IncrementalMesh_2)
new oc.BRepMesh_IncrementalMesh_2(
  compound,
  linearDeflection,
  relative,
  angularDeflection,
  parallel
);
```

### Writer: Merge faces to reduce primitive arrays / draw overhead

```ts
// Source: node_modules/opencascade.js/dist/opencascade.full.d.ts (RWGltf_CafWriter)
const writer = new oc.RWGltf_CafWriter(file, /*isBinary*/ true);
writer.SetNodeNameFormat(
  oc.RWMesh_NameFormat.RWMesh_NameFormat_ProductAndInstanceAndOcaf
);
writer.SetMeshNameFormat(
  oc.RWMesh_NameFormat.RWMesh_NameFormat_ProductAndInstanceAndOcaf
);

// Recommended default for Explorer smoothness:
writer.SetMergeFaces(true);
// Keep default: writer.SetSplitIndices16(false)
```

### Post-write GLB triangle counting (no BIN decode required)

```ts
// Source: frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts
function summarizeGlbTriangles(glb: Uint8Array) {
  const gltf = parseGlbJson(glb) as any;
  const accessors = gltf.accessors as any[];
  let triangles = 0;
  for (const mesh of gltf.meshes ?? []) {
    for (const prim of mesh.primitives ?? []) {
      const idxAcc =
        typeof prim.indices === 'number' ? accessors[prim.indices] : null;
      if (idxAcc && typeof idxAcc.count === 'number') {
        triangles += Math.floor(idxAcc.count / 3);
      }
    }
  }
  return { triangles };
}
```

### Dev FPS overlay (cheap; update UI at low Hz)

```tsx
// Source pattern: frontend/src/app/features/climate-tech/assembly-viewer/visualizer/AssemblyCanvas.tsx
// Use r3f useFrame + renderer.info; throttle state updates.

const isDev = import.meta.env.DEV;
if (!isDev) return null;

// In a r3f component:
useFrame(({ gl }, delta) => {
  // accumulate frames/time; every 250ms setState({ fps, triangles: gl.info.render.triangles, calls: gl.info.render.calls })
});
```

## State of the Art

| Old Approach                                | Current Approach                        | When Changed | Impact                                                                       |
| ------------------------------------------- | --------------------------------------- | ------------ | ---------------------------------------------------------------------------- |
| “One-shot conversion” with fixed deflection | Retry-on-explosion + persisted warnings | Phase 02     | Prevents catastrophic meshes while preserving fidelity-first defaults        |
| Export many small face primitives           | `RWGltf_CafWriter.SetMergeFaces(true)`  | Phase 02     | Lower primitive count / JSON size; improves Explorer orbit + selection costs |

**Deprecated/outdated:**

- “Fix performance by runtime decimation”: likely to violate locked mechanical fidelity requirements.

## Open Questions

1. **What OCCT version is opencascade.js built against in this repo’s beta snapshot?**

   - What we know: `node_modules/opencascade.js/README.md` advertises 7.6.2, while OCCT refman at `dev.opencascade.org/doc/refman` is 7.9.0.
   - What’s unclear: Exact version for `2.0.0-beta.b5ff984` and whether any meshing defaults differ materially.
   - Recommendation: Treat `BRepMesh_IncrementalMesh` + `RWGltf_CafWriter` APIs as stable (they exist in bindings), but validate numeric behavior on baseline models.

2. **Should `relative` be default in Explorer conversion?**
   - What we know: Relative deflection semantics can explode triangles on micro-edges (OCCT-defined behavior).
   - What’s unclear: Typical STEP inputs in this product (feature scales).
   - Recommendation: Default `relative=false` with unit-aware absolute deflection; only enable `relative` behind explicit user control or after bounding-box based tuning.

## Sources

### Primary (HIGH confidence)

- Local bindings (API availability): `node_modules/opencascade.js/dist/opencascade.full.d.ts` (checked `BRepMesh_IncrementalMesh_2`, `RWGltf_CafWriter.SetMergeFaces/SetSplitIndices16`, `Bnd_Box`, `BRepBndLib.AddOptimal`).
- Repo conversion implementation:
  - `packages/opencascade-convert/src/occt/triangulation.ts`
  - `packages/opencascade-convert/src/occt/writer-core.ts`
  - `frontend/src/app/features/tools/step-converter/workers/stepConverter.worker.ts`
  - `packages/opencascade-convert/src/occt/glb-metadata.ts` (`injectAssetExtrasIntoGlb()`)

### Secondary (MEDIUM confidence)

- OCCT reference manual (behavior descriptions; version shown as 7.9.0 on site):
  - https://dev.opencascade.org/doc/refman/html/class_b_rep_mesh___incremental_mesh.html
  - https://dev.opencascade.org/doc/refman/html/class_r_w_gltf___caf_writer.html
  - https://dev.opencascade.org/doc/refman/html/_r_w_mesh___name_format_8hxx.html

### Tertiary (LOW confidence)

- `node_modules/opencascade.js/README.md` OpenCascade version badge (7.6.2) may be stale relative to the beta tarball used here.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - verified in repo + local type definitions.
- Architecture: MEDIUM - prescriptive pattern, but triangle thresholds need calibration on real models.
- Pitfalls: HIGH - derived from OCCT documented semantics + existing dual export paths.

**Research date:** 2026-02-07
**Valid until:** 2026-03-09
