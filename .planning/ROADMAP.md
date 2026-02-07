# Roadmap: opencascade-convert optimization

## Overview

This roadmap delivers a browser-first STEP to GLB conversion pipeline that preserves assembly metadata and produces meshes that render smoothly in the Assembly Hierarchy Explorer. Work proceeds from reliable conversion and outputs, through mesh quality tuning, to a usable explorer workflow with selection and visibility controls.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Browser Conversion + Outputs** - Users can convert STEP in-browser and download GLB with assembly metadata.
- [x] **Phase 2: Mesh Quality Baseline** - Converted meshes are performant and avoid triangle explosions.
- [ ] **Phase 3: Explorer Selection Workflow** - Users can select, highlight, and manage parts in the explorer.

## Phase Details

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
   **Plans**: TBD

Plans:

- [ ] 03-01: TBD during planning

## Progress

**Execution Order:**
Phases execute in numeric order: 2 -> 2.1 -> 2.2 -> 3 -> 3.1 -> 4

| Phase                           | Plans Complete | Status      | Completed  |
| ------------------------------- | -------------- | ----------- | ---------- |
| 1. Browser Conversion + Outputs | 4/4            | Complete    | 2026-02-06 |
| 2. Mesh Quality Baseline        | 5/5            | Complete    | 2026-02-07 |
| 3. Explorer Selection Workflow  | 0/TBD          | Not started | -          |
