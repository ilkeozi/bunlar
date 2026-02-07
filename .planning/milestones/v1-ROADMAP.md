# Milestone v1: Explorer-Ready Browser Conversion

**Status:** ✅ SHIPPED 2026-02-07
**Phases:** 1-3
**Total Plans:** 13

## Overview

Browser-first STEP -> GLB conversion with embedded assembly metadata and bounded mesh-quality safeguards, plus an Assembly Hierarchy Explorer workflow where the tree and 3D view stay synchronized (selection, visibility, fit).

## Phases

### Phase 1: Browser Conversion + Outputs

**Goal**: Users can convert STEP in the browser and get GLB plus assembly metadata reliably.
**Depends on**: Nothing (first phase)
**Plans**: 4 plans

Plans:

- [x] 01-01-PLAN.md — Add GLB metadata embedding helper (TDD)
- [x] 01-02-PLAN.md — Browser conversion: STEP-only + size cap + progress/cancel + bundle download
- [x] 01-03-PLAN.md — Human verify: end-to-end conversion + bundle contents
- [x] 01-04-PLAN.md — Gap closure: emit UNSUPPORTED_STEP_CONTENT for empty/unsupported STEP content

**Details:**
Users can run conversion off the main thread (worker), see progress/cancel, and download a single bundle containing the GLB plus metadata (assembly tree, node map, BOM). Errors are stable and actionable.

### Phase 2: Mesh Quality Baseline

**Goal**: Converted meshes render smoothly without triangle explosions on mid-range desktop Chrome.
**Depends on**: Phase 1
**Plans**: 5 plans

Plans:

- [x] 02-01-PLAN.md — Enable face merging + switch Explorer meshing defaults to absolute deflection
- [x] 02-02-PLAN.md — Retry-on-triangle-explosion + persisted warnings + Step Converter warning UI
- [x] 02-03-PLAN.md — Dev-only FPS/debug overlay for Explorer canvas
- [x] 02-04-PLAN.md — Human verify: FPS baseline + warning persistence
- [x] 02-05-PLAN.md — Gap closure: Explorer worker bounded retry-on-explosion + structured conversionWarnings

**Details:**
Absolute tessellation defaults and bounded retry-on-explosion reduce pathological triangle counts. Conversion warnings are persisted, and a dev-only overlay supports performance baselining.

### Phase 3: Explorer Selection Workflow

**Goal**: Users can navigate assemblies via synchronized tree and 3D selection controls.
**Depends on**: Phase 2
**Plans**: 4 plans

Plans:

- [x] 03-01-PLAN.md — Store + NodeMap utilities for selection/visibility semantics
- [x] 03-02-PLAN.md — 3D canvas: picking, outline highlight, visibility enforcement, fit controller
- [x] 03-03-PLAN.md — Explorer UI: tree + toolbar wired to store (tree<->3D sync)
- [x] 03-04-PLAN.md — Human verify: end-to-end selection/visibility/fit workflow

**Details:**
Single-select workflow with leaf-only tree selection, synchronized 3D picking, per-node visibility toggles (including subtree), isolate with restore semantics, and fit-to-selection/visible camera behavior.

---

## Milestone Summary

**Decimal Phases:** None

**Key Decisions:**

- Shallow-merge GLB `asset.extras` when injecting metadata (preserve existing keys).
- Use stable error code taxonomy (e.g. `UNSUPPORTED_STEP_CONTENT`) for UI mapping.
- Default Explorer conversions to absolute tessellation; bounded retry when mesh stats exceed thresholds.
- Selection mapping uses GLTFLoader parser associations to map 3D picks back to glTF node indices and NodeMap/OCAF entries.

**Issues Resolved:**

- Triangle explosion mitigation + persisted warnings in conversion outputs.
- Explorer selection/visibility initially failed due to unreliable OCAF mapping; fixed by association-driven mapping and tests.

**Issues Deferred:**

- Explorer does not yet ingest Step Converter bundles (zip/glb+metadata) or parse `asset.extras.bunlarStepConverter` for direct load.
- Missing Playwright success-path E2E for Step Converter bundle generation.
- Missing Playwright E2E for Assembly Explorer selection/visibility/fit.

**Technical Debt Incurred:**

- Selection correctness relies on GLTFLoader parser association internals; upgrades to three/drei should be guarded by E2E tests.
- GLB JSON parsing exists in multiple places (drift risk).

---

_For current project status, see .planning/ROADMAP.md_
