# Project Milestones: opencascade-convert optimization

## v1 Explorer-Ready Browser Conversion (Shipped: 2026-02-07)

**Delivered:** Browser-first STEP -> GLB conversion with assembly metadata plus a usable Assembly Explorer workflow (tree<->3D selection, visibility controls, fit camera).

**Phases completed:** 1-3 (13 plans total)

**Key accomplishments:**

- Browser worker conversion with progress/cancel and a single downloadable bundle (GLB + metadata JSON)
- GLB metadata embedding via `asset.extras` with stable error codes for UI mapping
- Mesh quality baseline safeguards (absolute tessellation defaults + bounded retry-on-explosion + persisted warnings)
- Explorer selection workflow: leaf-only tree selection, 3D picking, isolate/show-all semantics, fit-to-selection/visible
- Robust 3D pick mapping using GLTFLoader parser associations to bridge scene objects to NodeMap/OCAF entries

**Stats:**

- 81 files created/modified
- 8,827 lines added (TypeScript/CSS/etc.)
- 3 phases, 13 plans, 28 tasks
- Timeline: 2026-02-05 -> 2026-02-07

**Git range:** `eb53b60` -> `v1`

**What's next:** Close v1 tech-debt seams (Explorer "open bundle" path, add E2E coverage, reduce GLB parsing duplication).

---
