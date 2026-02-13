#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+############

# Requirements: opencascade-convert optimization

**Defined:** 2026-02-13
**Core Value:** STEP assemblies load smoothly in the Assembly Hierarchy Explorer because conversion produces efficient, high-quality meshes.

## v1.1 Requirements

Requirements for v1.1. Each maps to roadmap phases.

### Nx Workspace Cleanup

- [ ] **NX-01**: Nx no longer includes `cad-converter` as a project (no targets, no graph node)
- [ ] **NX-02**: Nx no longer includes `occt-api` as a project (no targets, no graph node)
- [ ] **NX-03**: Repository contains no scripts/docs/CI references that assume `cad-converter` or `occt-api` exist in Nx
- [ ] **NX-04**: Remaining Nx projects run cleanly after removal (serve/build/test/e2e as applicable)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Explorer + Converter Hardening

- **EXPL-04**: Explorer can open a Step Converter bundle (zip/glb+metadata) without re-conversion
- **TEST-01**: Playwright E2E coverage for Assembly Hierarchy Explorer selection/visibility/fit
- **TEST-02**: Step Converter success-path E2E asserting a non-empty downloadable bundle
- **REF-01**: Reduce GLB JSON parsing duplication across worker + viewer utilities
- **API-01**: Dual entry points (browser + Node/CLI) with redesigned `opencascade-convert` API surface

## Out of Scope

Explicitly excluded for v1.1.

| Feature                             | Reason                     |
| ----------------------------------- | -------------------------- |
| New conversion formats (IGES, etc.) | Scope is workspace cleanup |
| New mesh optimization techniques    | Scope is workspace cleanup |
| New Explorer UX features            | Scope is workspace cleanup |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase   | Status  |
| ----------- | ------- | ------- |
| NX-01       | Phase 4 | Pending |
| NX-02       | Phase 4 | Pending |
| NX-03       | Phase 6 | Pending |
| NX-04       | Phase 6 | Pending |

**Coverage:**

- v1.1 requirements: 4 total
- Mapped to phases: 4
- Unmapped: 0 ✓

---

_Requirements defined: 2026-02-13_
