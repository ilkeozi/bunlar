# Tasks: Retire Stale Material-Ingestion Spec

**Input**: Design documents from `/specs/002-retire-stale-spec/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Validation is documentation/process focused. Use repeatable manual validation tasks for pointer resolution, scope boundaries, and planning continuity.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure feature artifact layout is complete and active pointer targets this feature.

- [x] T001 Verify feature artifact directory exists at `specs/002-retire-stale-spec/` with baseline files (`spec.md`, `plan.md`, `checklists/requirements.md`)
- [x] T002 Confirm active feature pointer in `.specify/feature.json` targets `specs/002-retire-stale-spec`
- [x] T003 [P] Verify SPECKIT marker points to current plan in `AGENTS.md`
- [x] T004 [P] Verify SPECKIT marker points to current plan in `agents.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define governance primitives and validation references required by all user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Confirm stale-retirement decision rationale is documented in `specs/002-retire-stale-spec/research.md`
- [x] T006 Confirm baseline entity/state definitions are complete in `specs/002-retire-stale-spec/data-model.md`
- [x] T007 [P] Confirm active/retired status schema is defined in `specs/002-retire-stale-spec/contracts/spec-baseline-status.contract.yaml`
- [x] T008 [P] Confirm operator validation flow is documented in `specs/002-retire-stale-spec/quickstart.md`

**Checkpoint**: Foundation ready; user stories can proceed.

---

## Phase 3: User Story 1 - Retire Invalid Spec Source (Priority: P1) 🎯 MVP

**Goal**: Remove stale spec from active planning flow and make the replacement baseline explicit.

**Independent Test**: Active pointer resolves to `specs/002-retire-stale-spec/spec.md`, and stale baseline is clearly marked non-active in feature documentation.

### Validation for User Story 1

- [x] T009 [P] [US1] Run `.specify/scripts/bash/setup-plan.sh --json` and capture active resolution evidence in `specs/002-retire-stale-spec/quickstart.md`
- [x] T010 [P] [US1] Add explicit stale-vs-active baseline verification checklist section in `specs/002-retire-stale-spec/quickstart.md`

### Implementation for User Story 1

- [x] T011 [US1] Add retired baseline reference note (pointing to `001-material-ingestion-refactor`) in `specs/002-retire-stale-spec/spec.md`
- [x] T012 [US1] Add traceability mapping from retired baseline to replacement baseline in `specs/002-retire-stale-spec/research.md`
- [x] T013 [US1] Record active-baseline ownership statement in `specs/002-retire-stale-spec/plan.md`

**Checkpoint**: US1 complete and independently testable.

---

## Phase 4: User Story 2 - Preserve Existing Implementation (Priority: P2)

**Goal**: Enforce that stale-spec retirement remains documentation/process-only with zero runtime code changes.

**Independent Test**: File-change review shows edits only under spec/process metadata and docs boundaries.

### Validation for User Story 2

- [x] T014 [P] [US2] Add explicit allowed-path validation checklist to `specs/002-retire-stale-spec/quickstart.md` (`.specify/`, `specs/`, `AGENTS.md`, `agents.md`)
- [x] T015 [P] [US2] Add forbidden-path examples (`apps/`, `packages/`, runtime service files) to `specs/002-retire-stale-spec/quickstart.md`

### Implementation for User Story 2

- [x] T016 [US2] Add no-code-change governance constraint section in `specs/002-retire-stale-spec/plan.md`
- [x] T017 [US2] Add no-code-change acceptance trace in `specs/002-retire-stale-spec/spec.md`
- [x] T018 [US2] Add scope-audit step template (git status/diff review) in `specs/002-retire-stale-spec/quickstart.md`

**Checkpoint**: US2 complete and independently testable.

---

## Phase 5: User Story 3 - Establish Clean Future Planning Baseline (Priority: P3)

**Goal**: Ensure future planning/task generation uses the new baseline and excludes stale-only assumptions.

**Independent Test**: Regenerated planning artifacts reference the new baseline and omit stale-only requirements.

### Validation for User Story 3

- [x] T019 [P] [US3] Add planning continuity checklist for `/speckit-plan` and `/speckit-tasks` outputs in `specs/002-retire-stale-spec/quickstart.md`
- [x] T020 [P] [US3] Add stale-assumption exclusion review checklist in `specs/002-retire-stale-spec/checklists/requirements.md`

### Implementation for User Story 3

- [x] T021 [US3] Add baseline status lifecycle examples (`active`, `retired`) in `specs/002-retire-stale-spec/contracts/spec-baseline-status.contract.yaml`
- [x] T022 [US3] Add forward-planning guardrails and expected outputs in `specs/002-retire-stale-spec/plan.md`
- [x] T023 [US3] Add explicit operator handoff steps for future planning in `specs/002-retire-stale-spec/quickstart.md`

**Checkpoint**: US3 complete and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency pass across all feature artifacts.

- [x] T024 [P] Cross-check requirement-to-task traceability alignment in `specs/002-retire-stale-spec/spec.md` and `specs/002-retire-stale-spec/tasks.md`
- [x] T025 [P] Run full quickstart validation flow and record final confirmation notes in `specs/002-retire-stale-spec/quickstart.md`
- [x] T026 Ensure AGENTS context remains aligned with active plan path in `AGENTS.md` and `agents.md`
- [x] T027 Prepare final feature summary note for reviewers in `specs/002-retire-stale-spec/plan.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2; defines MVP.
- **Phase 4 (US2)**: Depends on Phase 2 and aligns with US1 status decisions.
- **Phase 5 (US3)**: Depends on Phase 2 and should include US1/US2 guardrails.
- **Phase 6 (Polish)**: Depends on completion of targeted user stories.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2; no dependency on other stories.
- **US2 (P2)**: Starts after Phase 2; should align with US1 baseline status decisions.
- **US3 (P3)**: Starts after Phase 2; should consume US1/US2 governance and validation patterns.

### Within Each User Story

- Validation tasks first.
- Documentation/contract updates second.
- Consistency and traceability checks last.
- Complete story validation before moving on.

### Parallel Opportunities

- Setup tasks T003-T004 can run in parallel after T001-T002.
- Foundational tasks T007-T008 can run in parallel after T005-T006.
- In US1, T009 and T010 can run in parallel.
- In US2, T014 and T015 can run in parallel.
- In US3, T019 and T020 can run in parallel.
- Polish tasks T024 and T025 can run in parallel.

---

## Parallel Example: User Story 2

```bash
Task: "T014 [US2] Add allowed-path validation checklist in specs/002-retire-stale-spec/quickstart.md"
Task: "T015 [US2] Add forbidden-path examples in specs/002-retire-stale-spec/quickstart.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete US1 tasks (Phase 3).
3. Validate active-pointer replacement and stale-baseline retirement evidence.
4. Pause for review before wider governance polishing.

### Incremental Delivery

1. Foundation + US1 secures active-baseline correction.
2. Add US2 to lock no-code-change boundaries.
3. Add US3 to ensure future planning continuity.
4. Finish with cross-artifact polish.

### Parallel Team Strategy

1. Align on Phase 1/2 validation primitives.
2. Contributor A drives US1, Contributor B drives US2, Contributor C drives US3.
3. Reconcile using shared quickstart and plan consistency checks.

---

## Notes

- [P] tasks touch different files and avoid direct dependencies.
- Each story remains independently testable via documented validation flows.
- Scope is intentionally constrained to spec/process artifacts with no runtime code edits.
