# Requirements: opencascade-convert optimization

**Defined:** 2026-01-30
**Core Value:** STEP assemblies load smoothly in the Assembly Hierarchy Explorer because conversion produces efficient, high-quality meshes.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Conversion

- [ ] **CONV-01**: User can load a STEP file (≤ 15 MB) in the browser for conversion
- [ ] **CONV-02**: Conversion preserves assembly structure and part names from STEP
- [ ] **CONV-03**: Conversion preserves units/scale so the model renders at correct size
- [ ] **CONV-04**: Conversion runs off the main thread with progress and cancel
- [ ] **CONV-05**: Conversion reports actionable errors (invalid STEP, size cap, unsupported data)

### Mesh Quality

- [ ] **MESH-01**: Conversion produces meshes suitable for real-time rendering on mid-range desktop Chrome
- [ ] **MESH-02**: Conversion avoids triangle/mesh explosions while maintaining visual fidelity

### Output & Metadata

- [ ] **OUT-01**: User can download GLB output from the browser (direct `.glb` or a single bundle that contains the `.glb`)
- [ ] **OUT-02**: Output includes metadata: assembly tree, node map, BOM

### Explorer UX

- [ ] **EXPL-01**: Selecting a tree node highlights the corresponding geometry in 3D
- [ ] **EXPL-02**: Selecting geometry in 3D highlights the corresponding tree node
- [ ] **EXPL-03**: User can hide/isolate parts and fit camera to selection

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

| Requirement | Phase   | Status  |
| ----------- | ------- | ------- |
| CONV-01     | Phase 1 | Pending |
| CONV-02     | Phase 1 | Pending |
| CONV-03     | Phase 1 | Pending |
| CONV-04     | Phase 1 | Pending |
| CONV-05     | Phase 1 | Pending |
| MESH-01     | Phase 2 | Pending |
| MESH-02     | Phase 2 | Pending |
| OUT-01      | Phase 1 | Pending |
| OUT-02      | Phase 1 | Pending |
| EXPL-01     | Phase 3 | Pending |
| EXPL-02     | Phase 3 | Pending |
| EXPL-03     | Phase 3 | Pending |

**Coverage:**

- v1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---

_Requirements defined: 2026-01-30_
_Last updated: 2026-01-30 after roadmap creation_
