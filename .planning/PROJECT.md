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

- ✓ Reduce triangle counts while preserving mesh quality; avoid mesh/triangle explosions — v1
- ✓ Browser WASM conversion runs entirely in memory (buffers only), producing downloadable outputs — v1
- ✓ STEP-only input supported — v1
- ✓ Output GLB plus metadata: assembly tree, node map, BOM — v1
- ✓ Enforce 15 MB input cap in browser conversion — v1
- ✓ Conversion output renders smoothly enough for interactive exploration (baseline) — v1

### Active

- [ ] Remove `cad-converter` from Nx workspace and repository
- [ ] Remove `occt-api` from Nx workspace and repository
- [ ] Remove docs/scripts/CI references to removed projects; ensure remaining Nx tasks run cleanly

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
| Optimize triangulation for fewer triangles + better mesh quality | Current GLBs are too heavy for Three.js              | ✓ v1      |
| Use browser WASM conversion for public app                       | Avoid server-side conversion costs                   | ✓ v1      |
| Keep dual entry points (browser + Node/CLI)                      | Preserve local workflows while enabling browser use  | — Pending |
| STEP-only input                                                  | Narrow scope to the most important format            | ✓ v1      |
| Output GLB + metadata (assembly tree, node map, BOM)             | Explorer needs hierarchy and BOM context             | ✓ v1      |
| No temp files; in-memory buffers only                            | Browser-friendly and avoids file system dependencies | ✓ v1      |
| Redesign API surface of `opencascade-convert`                    | Current API can change                               | — Pending |
| Keep OpenCascade.js beta build                                   | Required for feature coverage                        | ✓ v1      |

## Current State

Shipped v1 with:

- Browser STEP conversion producing GLB + metadata (bundle + embedded extras)
- Mesh quality baseline safeguards (face merging, absolute tessellation defaults, bounded retry-on-explosion)
- Assembly Hierarchy Explorer selection workflow (tree<->3D selection sync, visibility, isolate, fit)

Known tech debt (tracked in `.planning/milestones/v1-MILESTONE-AUDIT.md`): Explorer does not yet open Step Converter bundles directly; E2E coverage for Explorer is missing.

## Current Milestone: v1.1 Nx Cleanup

**Goal:** Remove `cad-converter` and `occt-api` from the Nx workspace and repository so the monorepo focuses on the browser conversion + explorer workflow.

**Target outcomes:**

- Remove Nx project configuration for `cad-converter`
- Remove Nx project configuration for `occt-api`
- Remove scripts/docs/CI references so `nx graph`, `nx affected`, and standard tasks run cleanly
- Confirm the remaining workspace (frontend + e2e + conversion-in-browser path) still builds and runs

---

_Last updated: 2026-02-13 after starting v1.1 milestone_
