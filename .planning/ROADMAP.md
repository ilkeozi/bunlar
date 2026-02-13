# Roadmap: opencascade-convert optimization

## Overview

This roadmap delivers a browser-first STEP to GLB conversion pipeline that preserves assembly metadata and produces meshes that render smoothly in the Assembly Hierarchy Explorer. Work proceeds from reliable conversion and outputs, through mesh quality tuning, to a usable explorer workflow with selection and visibility controls.

## Milestones

- ✅ **v1** — Explorer-ready browser conversion (Phases 1-3) — shipped 2026-02-07

  - Roadmap archive: `.planning/milestones/v1-ROADMAP.md`
  - Requirements archive: `.planning/milestones/v1-REQUIREMENTS.md`

- 🚧 **v1.1** — Nx cleanup (Phases 4-6) — in progress (started 2026-02-13)

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Browser Conversion + Outputs** - Users can convert STEP in-browser and download GLB with assembly metadata.
- [x] **Phase 2: Mesh Quality Baseline** - Converted meshes are performant and avoid triangle explosions.
- [x] **Phase 3: Explorer Selection Workflow** - Users can select, highlight, and manage parts in the explorer.

- [ ] **Phase 4: Decommission Nx Projects** - Remove `cad-converter` and `occt-api` from Nx.
- [ ] **Phase 5: Remove Unused Artifacts** - Delete remaining artifacts and fix references/imports.
- [ ] **Phase 6: Workspace Verification** - Confirm remaining Nx tasks run cleanly after removal.

## Phase Details

<details>
<summary>✅ v1 (Phases 1-3) — SHIPPED 2026-02-07</summary>

### Phase 1: Browser Conversion + Outputs

**Goal**: Users can convert STEP in the browser and get GLB plus assembly metadata reliably.
**Depends on**: Nothing (first phase)
**Requirements**: CONV-01, CONV-02, CONV-03, CONV-04, CONV-05, OUT-01, OUT-02
**Success Criteria** (what must be TRUE):

1. User can load a STEP file up to 15 MB in the browser and start conversion.
2. User sees conversion run off the main thread with progress and can cancel it.
3. Converted output preserves assembly structure, part names, and correct units/scale.
4. User can download an output bundle that includes a GLB plus assembly metadata (assembly tree, node map, BOM).
5. User receives actionable errors for invalid STEP files, size cap violations, or unsupported data.
   **Plans**: 4 plans

Plans:

- [x] 01-01-PLAN.md — Add GLB metadata embedding helper (TDD)
- [x] 01-02-PLAN.md — Browser conversion: STEP-only + size cap + progress/cancel + bundle download
- [x] 01-03-PLAN.md — Human verify: end-to-end conversion + bundle contents
- [x] 01-04-PLAN.md — Gap closure: emit UNSUPPORTED_STEP_CONTENT for empty/unsupported STEP content

### Phase 2: Mesh Quality Baseline

**Goal**: Converted meshes render smoothly without triangle explosions on mid-range desktop Chrome.
**Depends on**: Phase 1
**Requirements**: MESH-01, MESH-02
**Success Criteria** (what must be TRUE):

1. User can orbit and interact with converted assemblies at smooth frame rates in the explorer.
2. User observes meshes that maintain visual fidelity without runaway triangle counts.
   **Plans**: 5 plans

Plans:

- [x] 02-01-PLAN.md — Enable face merging + switch Explorer meshing defaults to absolute deflection
- [x] 02-02-PLAN.md — Retry-on-triangle-explosion + persisted warnings + Step Converter warning UI
- [x] 02-03-PLAN.md — Dev-only FPS/debug overlay for Explorer canvas
- [x] 02-04-PLAN.md — Human verify: FPS baseline + warning persistence
- [x] 02-05-PLAN.md — Gap closure: Explorer worker bounded retry-on-explosion + structured conversionWarnings

Verification:

- Status: passed
- Report: .planning/phases/02-mesh-quality-baseline/02-VERIFICATION.md

### Phase 3: Explorer Selection Workflow

**Goal**: Users can navigate assemblies via synchronized tree and 3D selection controls.
**Depends on**: Phase 2
**Requirements**: EXPL-01, EXPL-02, EXPL-03
**Success Criteria** (what must be TRUE):

1. User can select a tree node and see the corresponding geometry highlighted in 3D.
2. User can select geometry in 3D and see the corresponding tree node highlighted.
3. User can hide or isolate parts and fit the camera to the current selection.
   **Plans**: 4 plans

Plans:

- [x] 03-01-PLAN.md — Store + NodeMap utilities for selection/visibility semantics
- [x] 03-02-PLAN.md — 3D canvas: picking, outline highlight, visibility enforcement, fit controller
- [x] 03-03-PLAN.md — Explorer UI: tree + toolbar wired to store (tree<->3D sync)
- [x] 03-04-PLAN.md — Human verify: end-to-end selection/visibility/fit workflow

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase                           | Plans Complete | Status   | Completed  |
| ------------------------------- | -------------- | -------- | ---------- |
| 1. Browser Conversion + Outputs | 4/4            | Complete | 2026-02-06 |
| 2. Mesh Quality Baseline        | 5/5            | Complete | 2026-02-07 |
| 3. Explorer Selection Workflow  | 4/4            | Complete | 2026-02-07 |

</details>

### 🚧 v1.1 Nx Cleanup (Phases 4-6)

### Phase 4: Decommission Nx Projects

**Goal**: Nx no longer includes `cad-converter` or `occt-api` as projects.
**Depends on**: Phase 3
**Requirements**: NX-01, NX-02
**Success Criteria** (what must be TRUE):

1. `nx graph` / `nx show projects` no longer lists `cad-converter`.
2. `nx graph` / `nx show projects` no longer lists `occt-api`.
3. Running common Nx commands does not error due to missing project configuration.
   **Plans**: 2 plans

Plans:

- [ ] 04-01-PLAN.md — Remove `cad-converter` Nx project config + targets
- [ ] 04-02-PLAN.md — Remove `occt-api` Nx project config + targets

### Phase 5: Remove Unused Artifacts

**Goal**: Removed projects are fully deleted and no longer referenced from code/scripts.
**Depends on**: Phase 4
**Requirements**: (supports NX-03)
**Success Criteria** (what must be TRUE):

1. No remaining imports/references to `cad-converter` or `occt-api` code.
2. Workspace dependency graph has no dangling references.
   **Plans**: 1 plan

Plans:

- [ ] 05-01-PLAN.md — Remove repo artifacts + fix references/imports

### Phase 6: Workspace Verification

**Goal**: The remaining workspace runs cleanly after removals.
**Depends on**: Phase 5
**Requirements**: NX-03, NX-04
**Success Criteria** (what must be TRUE):

1. Docs/scripts/CI contain no references to `cad-converter` or `occt-api`.
2. `nx affected` (or equivalent) runs without configuration errors.
3. Remaining core tasks run cleanly (frontend build/test, e2e where configured).
   **Plans**: 2 plans

Plans:

- [ ] 06-01-PLAN.md — Purge docs/scripts/CI references; update any developer docs
- [ ] 06-02-PLAN.md — Run remaining Nx targets; fix fallout

## Progress (v1.1)

| Phase                       | Plans Complete | Status  | Completed |
| --------------------------- | -------------- | ------- | --------- |
| 4. Decommission Nx Projects | 0/2            | Pending | -         |
| 5. Remove Unused Artifacts  | 0/1            | Pending | -         |
| 6. Workspace Verification   | 0/2            | Pending | -         |
