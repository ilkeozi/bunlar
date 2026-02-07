---
milestone: v1
audited: 2026-02-07T21:05:00Z
status: tech_debt
scores:
  requirements: 12/12
  phases: 3/3
  integration: 1/2
  flows: 2/2
gaps:
  requirements: []
  integration: []
  flows: []
tech_debt:
  - area: integration
    items:
      - 'Explorer does not ingest the Step Converter output bundle (.zip with .glb + .metadata.json) nor parse asset.extras.bunlarStepConverter; Explorer only supports re-conversion from STEP.'
  - area: testing
    items:
      - 'No Playwright E2E coverage for Assembly Hierarchy Explorer selection/visibility/fit workflow (currently human-verified).'
      - 'Step Converter Browser has an error-path E2E, but no success-path E2E asserting a non-empty downloadable bundle.'
  - area: robustness
    items:
      - 'Selection sync relies on GLTFLoader parser associations + glTF nodeIndex->name OCAF parsing; upgrades to three/drei could break mapping without automated coverage.'
      - 'GLB JSON parsing logic is duplicated across worker + viewer utilities (drift risk).'
---

# v1 Milestone Audit

This audit checks requirements coverage, phase verifications, cross-phase integration seams, and end-to-end user flows.

## Milestone Scope

- **Roadmap phases:** 01, 02, 03
- **Definition of done:** v1 requirements in `.planning/REQUIREMENTS.md` are satisfied

## Requirements Coverage (12/12)

| Area            | Requirements | Status |
| --------------- | ------------ | ------ |
| Conversion      | CONV-01..05  | ✓      |
| Mesh Quality    | MESH-01..02  | ✓      |
| Output/Metadata | OUT-01..02   | ✓      |
| Explorer UX     | EXPL-01..03  | ✓      |

Notes:

- Traceability table in `.planning/REQUIREMENTS.md` now reflects Phase 3 completion for EXPL-01..03.

## Phase Verification Status (3/3)

| Phase | Name                         | Verification | Report                                                               |
| ----- | ---------------------------- | ------------ | -------------------------------------------------------------------- |
| 01    | Browser Conversion + Outputs | passed       | `.planning/phases/01-browser-conversion-outputs/01-VERIFICATION.md`  |
| 02    | Mesh Quality Baseline        | passed       | `.planning/phases/02-mesh-quality-baseline/02-VERIFICATION.md`       |
| 03    | Explorer Selection Workflow  | passed       | `.planning/phases/03-explorer-selection-workflow/03-VERIFICATION.md` |

## Cross-Phase Integration

What works end-to-end (internal Explorer pipeline):

- Assembly Explorer route -> browser worker conversion -> GLB + NodeMap metadata -> 3D render -> selection/visibility/fit

Integration seam to track (not a v1 requirement, but a useful workflow gap):

- Step Converter Browser produces a bundle (`.zip` with `.glb` + `.metadata.json`, and metadata embedded under `asset.extras.bunlarStepConverter`), but Assembly Explorer does not consume that bundle; it only supports converting from STEP.

## E2E Flows

Functional (human-verified):

- Step Converter Browser: convert + download bundle; stable errors
- Assembly Hierarchy Explorer: upload STEP -> convert -> render -> tree<->3D selection sync -> hide/isolate/show-all -> fit

Automation coverage gaps:

- No Playwright E2E for the Explorer selection workflow (Flow B)
- No success-path Playwright E2E for Step Converter bundle generation (Flow A)

## Tech Debt & Follow-ups

1. Add an Explorer "Open bundle" path (zip/glb+metadata) and/or parse `asset.extras.bunlarStepConverter` to load without re-conversion.
2. Add Playwright E2E for Explorer Flow B with stable test surfaces (data-testid for tree rows + toolbar actions).
3. Add a Step Converter success E2E (fixture STEP) asserting a non-empty downloadable bundle.
4. Add runtime schema validation for Explorer metadata shape (stable error code on mismatch).
5. Reduce duplication of GLB JSON parsing to a shared utility to reduce drift risk.
