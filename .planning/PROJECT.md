# opencascade-convert optimization

## What This Is

Improve the internal `opencascade-convert` package so STEP assemblies convert to GLB with fewer triangles and better mesh quality, enabling smooth rendering in the Assembly Hierarchy Explorer. The conversion should run in the user's browser (WASM) to avoid server costs, while keeping a Node/CLI entry point for local workflows.

## Core Value

STEP assemblies load smoothly in the Assembly Hierarchy Explorer because conversion produces efficient, high-quality meshes.

## Requirements

### Validated

- ✓ Assembly Hierarchy Explorer loads GLB and renders in Three.js (`frontend/src/app/features/climate-tech/assembly-viewer/`) — existing
- ✓ Browser worker conversion uses `opencascade-convert` to convert CAD buffers to GLB + metadata — existing
- ✓ CLI conversion entry exists in `opencascade-convert` — existing
- ✓ Node API conversion service exists (NestJS `occt-api`) — existing

### Active

- [ ] Reduce triangle counts while preserving mesh quality; avoid mesh/triangle explosions
- [ ] Browser WASM conversion runs entirely in memory (buffers only), producing downloadable outputs
- [ ] Dual entry points (browser + Node/CLI) with redesigned API surface
- [ ] STEP-only input supported
- [ ] Output GLB plus metadata: assembly tree, node map, BOM
- [ ] Enforce 15 MB input cap in browser conversion
- [ ] Conversion output should render smoothly in Assembly Hierarchy Explorer (target 30 fps on mid-range desktop Chrome)

### Out of Scope

- IGES or other CAD formats for v1 — STEP-only focus
- Per-part transforms or bounding boxes in metadata — not required now
- Hard triangle cap enforcement to a specific target — unknown/variable inputs
- Server-side conversion required for public app — avoid AWS compute costs

## Context

- Current Assembly Hierarchy Explorer loads converted GLB but suffers from high triangle counts and performance issues.
- `opencascade-convert` is messy with duplicate files and needs cleanup/refactor alongside triangulation improvements.
- The frontend will be public (AWS), so conversion must run client-side to avoid server costs.
- Existing monorepo includes `opencascade-convert`, `occt-api`, and browser worker pipelines.

## Constraints

- **Tech stack**: Use existing OpenCascade.js beta build (most functions available) — required dependency
- **Runtime**: Browser WASM conversion must be supported (Web Worker)
- **Input**: STEP only; max 15 MB per file in browser
- **I/O**: In-memory buffers only; no temp file generation
- **Performance**: Target smooth rendering (~30 fps) on mid-range desktop Chrome

## Key Decisions

| Decision                                                         | Rationale                                            | Outcome   |
| ---------------------------------------------------------------- | ---------------------------------------------------- | --------- |
| Optimize triangulation for fewer triangles + better mesh quality | Current GLBs are too heavy for Three.js              | — Pending |
| Use browser WASM conversion for public app                       | Avoid server-side conversion costs                   | — Pending |
| Keep dual entry points (browser + Node/CLI)                      | Preserve local workflows while enabling browser use  | — Pending |
| STEP-only input                                                  | Narrow scope to the most important format            | — Pending |
| Output GLB + metadata (assembly tree, node map, BOM)             | Explorer needs hierarchy and BOM context             | — Pending |
| No temp files; in-memory buffers only                            | Browser-friendly and avoids file system dependencies | — Pending |
| Redesign API surface of `opencascade-convert`                    | Current API can change                               | — Pending |
| Keep OpenCascade.js beta build                                   | Required for feature coverage                        | — Pending |

---

_Last updated: 2026-01-30 after initialization_
