# Tasks: Material Ingestion Domain Refactor

**Input**: Design documents from `/specs/001-material-ingestion-refactor/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Include automated unit, integration, and contract tests for orchestration behavior, plus regression coverage for existing UNS flows.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create scaffolding for strict domain folders and orchestration artifacts.

- [ ] T001 Create domain package directories in `apps/material-ingestion/src/material_ingestion/shared/`, `apps/material-ingestion/src/material_ingestion/material_ingestion/`, and `apps/material-ingestion/src/material_ingestion/uns/`
- [ ] T002 [P] Add package init files in `apps/material-ingestion/src/material_ingestion/shared/__init__.py`, `apps/material-ingestion/src/material_ingestion/material_ingestion/__init__.py`, and `apps/material-ingestion/src/material_ingestion/uns/__init__.py`
- [ ] T003 [P] Create orchestration contract test directory and baseline file in `apps/material-ingestion/tests/integration/test_ingestion_orchestration_contract.py`
- [ ] T004 [P] Add HTTP orchestration API stub module in `apps/backend/src/app/ingestion/ingestion.controller.ts` and `apps/backend/src/app/ingestion/ingestion.module.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build core primitives that all user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T005 Implement `PipelineRun` domain model in `apps/material-ingestion/src/material_ingestion/material_ingestion/pipeline_run.py`
- [ ] T006 [P] Implement `ExecutionStage` domain model in `apps/material-ingestion/src/material_ingestion/material_ingestion/execution_stage.py`
- [ ] T007 [P] Implement context FIFO queue manager in `apps/material-ingestion/src/material_ingestion/material_ingestion/context_queue.py`
- [ ] T008 Implement deterministic stage sequencer in `apps/material-ingestion/src/material_ingestion/material_ingestion/stage_sequencer.py`
- [ ] T009 Implement orchestration service entrypoint in `apps/material-ingestion/src/material_ingestion/material_ingestion/orchestration_service.py`
- [ ] T010 [P] Implement shared run outcome/result types in `apps/material-ingestion/src/material_ingestion/shared/run_result.py`
- [ ] T011 [P] Add foundational unit tests for models and queue behavior in `apps/material-ingestion/tests/unit/test_pipeline_run.py` and `apps/material-ingestion/tests/unit/test_context_queue.py`

**Checkpoint**: Foundation ready; user stories can proceed.

---

## Phase 3: User Story 1 - Separate Domain Boundaries (Priority: P1) 🎯 MVP

**Goal**: Enforce strict folder ownership so material-ingestion and UNS implementations no longer mix.

**Independent Test**: Add a representative change and verify ownership validation blocks misplaced files while allowing correctly placed files.

### Validation for User Story 1

- [ ] T012 [P] [US1] Add ownership policy test cases in `apps/material-ingestion/tests/unit/test_placement_rules.py`
- [ ] T013 [P] [US1] Add merge-blocking validation integration test in `apps/material-ingestion/tests/integration/test_ownership_gate.py`

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `DomainArea` and `PlacementRule` entities in `apps/material-ingestion/src/material_ingestion/material_ingestion/placement_rules.py`
- [ ] T015 [US1] Implement ownership validator service in `apps/material-ingestion/src/material_ingestion/material_ingestion/ownership_validator.py`
- [ ] T016 [US1] Refactor UNS-specific extractors into `apps/material-ingestion/src/material_ingestion/uns/extractors/` and update imports in `apps/material-ingestion/src/material_ingestion/cli.py`
- [ ] T017 [US1] Move shared cross-domain utilities into `apps/material-ingestion/src/material_ingestion/shared/` and update usage in `apps/material-ingestion/src/material_ingestion/pipeline.py`
- [ ] T018 [US1] Add ownership gate command entry in `apps/material-ingestion/cli.py` and wire to validator
- [ ] T019 [US1] Document strict ownership rules and migration guidance in `apps/material-ingestion/README.md`

**Checkpoint**: US1 complete and independently testable.

---

## Phase 4: User Story 2 - Reuse Shared Foundations Without Domain Mixing (Priority: P2)

**Goal**: Keep reusable capabilities in shared area while preserving domain boundaries.

**Independent Test**: Demonstrate one shared component consumed by both domain and UNS flows without placing domain logic in shared folder.

### Validation for User Story 2

- [ ] T020 [P] [US2] Add shared dependency rule tests in `apps/material-ingestion/tests/unit/test_shared_dependency_rules.py`
- [ ] T021 [P] [US2] Add cross-domain reuse integration test in `apps/material-ingestion/tests/integration/test_shared_component_reuse.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Create shared pipeline interfaces in `apps/material-ingestion/src/material_ingestion/shared/pipeline_ports.py`
- [ ] T023 [US2] Move reusable stage helpers to `apps/material-ingestion/src/material_ingestion/shared/stage_helpers.py`
- [ ] T024 [US2] Update material-ingestion orchestration to consume shared interfaces in `apps/material-ingestion/src/material_ingestion/material_ingestion/orchestration_service.py`
- [ ] T025 [US2] Update UNS adapters to consume shared interfaces in `apps/material-ingestion/src/material_ingestion/uns/source_adapter.py`
- [ ] T026 [US2] Add static ownership/dependency checker script in `apps/material-ingestion/scripts/check_ownership.py` and expose Nx target in `apps/material-ingestion/project.json`

**Checkpoint**: US2 complete and independently testable.

---

## Phase 5: User Story 3 - Run Ingestion Through a Single Orchestration Flow (Priority: P3)

**Goal**: Provide one orchestration flow callable via CLI and HTTP API with FIFO queueing and stop-and-resume behavior.

**Independent Test**: Start equivalent runs from CLI and HTTP API and confirm same stage sequence and run outcomes, including failure-resume path.

### Validation for User Story 3

- [ ] T027 [P] [US3] Add CLI orchestration integration tests in `apps/material-ingestion/tests/integration/test_cli_orchestration.py`
- [ ] T028 [P] [US3] Implement HTTP contract tests from OpenAPI in `apps/backend-e2e/src/backend/ingestion-orchestration.contract.spec.ts`
- [ ] T029 [P] [US3] Add failure-resume integration tests in `apps/material-ingestion/tests/integration/test_orchestration_resume.py`

### Implementation for User Story 3

- [ ] T030 [US3] Refactor CLI entrypoint to call orchestration service in `apps/material-ingestion/src/material_ingestion/cli.py`
- [ ] T031 [US3] Implement HTTP API start/get handlers in `apps/backend/src/app/ingestion/ingestion.controller.ts`
- [ ] T032 [US3] Implement backend orchestration bridge service in `apps/backend/src/app/ingestion/ingestion.service.ts`
- [ ] T033 [US3] Wire ingestion module into Nest app in `apps/backend/src/app/app.module.ts`
- [ ] T034 [US3] Implement same-context FIFO processing in `apps/material-ingestion/src/material_ingestion/material_ingestion/context_queue.py`
- [ ] T035 [US3] Implement stop-on-failure and resume-from-last-successful logic in `apps/material-ingestion/src/material_ingestion/material_ingestion/orchestration_service.py`
- [ ] T036 [US3] Add run status serialization aligned with contract in `apps/backend/src/app/ingestion/run-dto.ts`

**Checkpoint**: US3 complete and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Stabilize docs, regression checks, and end-to-end validation.

- [ ] T037 [P] Run UNS regression suite updates in `apps/material-ingestion/tests/integration/test_uns_source_adapter.py` and `apps/material-ingestion/tests/integration/test_pipeline.py`
- [ ] T038 [P] Update quickstart execution and validation steps in `specs/001-material-ingestion-refactor/quickstart.md`
- [ ] T039 Update architecture and runbook notes in `apps/material-ingestion/README.md` and `docs/`
- [ ] T040 Execute full validation commands and capture results in `specs/001-material-ingestion-refactor/plan.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2; defines MVP.
- **Phase 4 (US2)**: Depends on Phase 2 and integrates with ownership guardrails from US1.
- **Phase 5 (US3)**: Depends on Phase 2 and should consume structures established in US1/US2.
- **Phase 6 (Polish)**: Depends on completion of targeted user stories.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2; no dependency on other stories.
- **US2 (P2)**: Starts after Phase 2; should align with US1 ownership policies.
- **US3 (P3)**: Starts after Phase 2; can proceed in parallel but final merge should include US1/US2 conventions.

### Within Each User Story

- Validation tasks first.
- Domain/entities before service wiring.
- Service wiring before adapter/controller integration.
- Complete story validation before moving on.

### Parallel Opportunities

- Setup tasks T002-T004 can run in parallel after T001.
- Foundational tasks T006, T007, T010, T011 can run in parallel after T005 starts.
- In US1, T012, T013, and T014 can run in parallel.
- In US2, T020, T021, and T022 can run in parallel.
- In US3, T027, T028, and T029 can run in parallel.
- Polish tasks T037 and T038 can run in parallel.

---

## Parallel Example: User Story 3

```bash
# Parallel validation tasks
Task: "T027 [US3] CLI orchestration integration tests in apps/material-ingestion/tests/integration/test_cli_orchestration.py"
Task: "T028 [US3] HTTP contract tests in apps/backend-e2e/src/backend/ingestion-orchestration.contract.spec.ts"
Task: "T029 [US3] Failure-resume tests in apps/material-ingestion/tests/integration/test_orchestration_resume.py"

# Parallel implementation tasks after orchestration service baseline exists
Task: "T031 [US3] HTTP API handlers in apps/backend/src/app/ingestion/ingestion.controller.ts"
Task: "T034 [US3] FIFO queue behavior in apps/material-ingestion/src/material_ingestion/material_ingestion/context_queue.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete US1 tasks (Phase 3).
3. Validate ownership gates and migration guidance.
4. Demo/refactor checkpoint before multi-channel work.

### Incremental Delivery

1. Foundation + US1 delivers structure safety.
2. Add US2 to stabilize shared reuse model.
3. Add US3 for CLI + HTTP orchestration parity.
4. Finish with regression and docs polish.

### Parallel Team Strategy

1. Team aligns on Phase 1/2 interfaces.
2. Developer A drives US1, Developer B drives US2, Developer C drives US3.
3. Integrate behind ownership checks and shared contracts.

---

## Notes

- [P] tasks touch different files and avoid direct dependencies.
- Each story is independently testable using listed integration/contract checks.
- Keep strict folder ownership enforcement active during all phases.
