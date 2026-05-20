# Implementation Plan: Material Ingestion Domain Refactor

**Branch**: `[001-material-ingestion-refactor]` | **Date**: 2026-05-20 | **Spec**: [/Users/ilker/source/bunlar/specs/001-material-ingestion-refactor/spec.md](/Users/ilker/source/bunlar/specs/001-material-ingestion-refactor/spec.md)

**Input**: Feature specification from `/specs/001-material-ingestion-refactor/spec.md`

**Note**: This plan is produced by `/speckit-plan` and covers phases through design artifacts.

## Summary

Refactor `apps/material-ingestion` into strict ownership boundaries (`shared/`, `material-ingestion/`, `uns/`) and introduce one transport-agnostic orchestration flow callable from both CLI and HTTP API. The orchestration enforces deterministic stage order, FIFO same-context queueing, and stop-and-resume failure handling.

## Technical Context

**Language/Version**: Python `>=3.10`

**Primary Dependencies**: `pypdf`, `pdfplumber`, setuptools packaging, Nx task runner

**Storage**: Filesystem-based ingestion inputs and normalized outputs under `apps/material-ingestion/data`

**Testing**: `pytest` via Nx (`test-unit`, `test-integration`, `material-ingestion-e2e`)

**Target Platform**: Local/dev and CI Linux/macOS environments running Nx + Python virtual environment

**Project Type**: Nx-managed Python application evolving from CLI-first to multi-channel orchestration service

**Performance Goals**: 95% of successful runs complete without operator intervention; failed stage identified in under 5 minutes

**Constraints**: Strict folder ownership with no exception paths; single active run per context; FIFO queue for same context; failed runs resume from last successful stage

**Scale/Scope**: Initial channel scope is `CLI` and `HTTP API`; current primary source remains UNS data pipeline

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Spec-first check: scope, behavior, constraints, acceptance criteria, and out-of-scope items are explicit and current.
- [x] Simplicity/evolvability check: proposed structure is the simplest viable approach and any abstraction/shared code is justified.
- [x] Verification-first check: each implementation slice has an independent validation path; automated tests or clear manual validation are defined.
- [x] User-centered quality check: UX consistency, accessibility practicality, and empty/loading/error/edge states are intentionally addressed.
- [x] Performance/reliability check: impacted paths include error handling, graceful failure expectations, and a validation approach for performance impact.
- [x] Documentation/automation fidelity check: required guidance updates are identified.

## Project Structure

### Documentation (this feature)

```text
specs/001-material-ingestion-refactor/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── ingestion-orchestration.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
apps/material-ingestion/
├── src/material_ingestion/
│   ├── shared/                     # cross-domain reusable pipeline components
│   ├── material_ingestion/         # ingestion-domain orchestration + policies
│   ├── uns/                        # UNS-specific adapters/extractors/normalizers
│   ├── cli.py                      # CLI transport adapter into orchestration core
│   └── ...
├── tests/
│   ├── unit/
│   └── integration/
└── data/
    ├── incoming/
    └── working/

apps/backend/
└── src/                            # HTTP API transport entrypoint integration target
```

**Structure Decision**: Keep the existing Nx app boundary (`apps/material-ingestion`) and refactor internals into strict domain ownership folders to preserve current package and test workflows while meeting anti-mixing constraints.

## Phase 0: Research Output

- Completed: [/Users/ilker/source/bunlar/specs/001-material-ingestion-refactor/research.md](/Users/ilker/source/bunlar/specs/001-material-ingestion-refactor/research.md)
- All prior clarifications are resolved into explicit decisions for channel scope, concurrency policy, failure policy, and ownership enforcement.

## Phase 1: Design Output

- Data model: [/Users/ilker/source/bunlar/specs/001-material-ingestion-refactor/data-model.md](/Users/ilker/source/bunlar/specs/001-material-ingestion-refactor/data-model.md)
- Interface contracts: [/Users/ilker/source/bunlar/specs/001-material-ingestion-refactor/contracts/ingestion-orchestration.openapi.yaml](/Users/ilker/source/bunlar/specs/001-material-ingestion-refactor/contracts/ingestion-orchestration.openapi.yaml)
- Quickstart: [/Users/ilker/source/bunlar/specs/001-material-ingestion-refactor/quickstart.md](/Users/ilker/source/bunlar/specs/001-material-ingestion-refactor/quickstart.md)
- Agent context update: `agents.md` SPECKIT marker now points to this feature plan.

## Post-Design Constitution Re-Check

- [x] Spec-first check remains satisfied after design artifact generation.
- [x] Simplicity/evolvability remains satisfied: no unnecessary project split introduced.
- [x] Verification-first remains satisfied with explicit unit/integration/contract/regression validation targets.
- [x] User-centered quality remains satisfied through reduced operator/manual burden.
- [x] Performance/reliability remains satisfied through deterministic stages, queueing, and recovery semantics.
- [x] Documentation/automation fidelity remains satisfied with generated plan artifacts and updated agent guidance pointer.

## Complexity Tracking

No constitution violations requiring justification.
