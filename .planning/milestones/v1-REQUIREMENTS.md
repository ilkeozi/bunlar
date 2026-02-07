# Requirements Archive: v1 Explorer-Ready Browser Conversion

**Archived:** 2026-02-07
**Status:** ✅ SHIPPED

This is the archived requirements specification for v1.
For current requirements, start a new milestone (fresh `.planning/REQUIREMENTS.md`).

---

# Requirements: opencascade-convert optimization

**Defined:** 2026-01-30
**Core Value:** STEP assemblies load smoothly in the Assembly Hierarchy Explorer because conversion produces efficient, high-quality meshes.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Conversion

- [x] **CONV-01**: User can load a STEP file (≤ 15 MB) in the browser for conversion
- [x] **CONV-02**: Conversion preserves assembly structure and part names from STEP
- [x] **CONV-03**: Conversion preserves units/scale so the model renders at correct size
- [x] **CONV-04**: Conversion runs off the main thread with progress and cancel
- [x] **CONV-05**: Conversion reports actionable errors (invalid STEP, size cap, unsupported data)

### Mesh Quality

- [x] **MESH-01**: Conversion produces meshes suitable for real-time rendering on mid-range desktop Chrome
- [x] **MESH-02**: Conversion avoids triangle/mesh explosions while maintaining visual fidelity

### Output & Metadata

- [x] **OUT-01**: User can download GLB output from the browser (direct `.glb` or a single bundle that contains the `.glb`)
- [x] **OUT-02**: Output includes metadata: assembly tree, node map, BOM

### Explorer UX

- [x] **EXPL-01**: Selecting a tree node highlights the corresponding geometry in 3D
- [x] **EXPL-02**: Selecting geometry in 3D highlights the corresponding tree node
- [x] **EXPL-03**: User can hide/isolate parts and fit camera to selection

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Mesh Optimization

- **MESH-03**: Curvature-aware adaptive meshing
- **MESH-04**: Geometry instancing detection
- **MESH-05**: Progressive mesh refinement
- **MESH-06**: Hierarchy-aware LOD
- **MESH-07**: Automatic geometry healing before meshing
- **MESH-08**: Mesh quality metrics + report

### Metadata Enrichment

- **OUT-03**: BOM enrichment (mass properties, bounding boxes)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature                           | Reason                               |
| --------------------------------- | ------------------------------------ |
| Support every CAD format          | STEP-only focus for v1               |
| Full CAD editing in browser       | Not required for conversion pipeline |
| Lossless parametric export in GLB | GLB is mesh-only; not feasible       |
| Unlimited file sizes              | Browser memory limits; cap required  |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase   | Status   |
| ----------- | ------- | -------- |
| CONV-01     | Phase 1 | Complete |
| CONV-02     | Phase 1 | Complete |
| CONV-03     | Phase 1 | Complete |
| CONV-04     | Phase 1 | Complete |
| CONV-05     | Phase 1 | Complete |
| MESH-01     | Phase 2 | Complete |
| MESH-02     | Phase 2 | Complete |
| OUT-01      | Phase 1 | Complete |
| OUT-02      | Phase 1 | Complete |
| EXPL-01     | Phase 3 | Complete |
| EXPL-02     | Phase 3 | Complete |
| EXPL-03     | Phase 3 | Complete |

**Coverage:**

- v1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---

## Milestone Summary

**Shipped:** 12 of 12 v1 requirements
**Adjusted:** None
**Dropped:** None

---

_Archived: 2026-02-07 as part of v1 milestone completion_
