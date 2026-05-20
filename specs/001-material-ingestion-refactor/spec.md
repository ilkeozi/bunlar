# Feature Specification: Material Ingestion Domain Refactor

**Feature Branch**: `[001-material-ingestion-refactor]`

**Created**: 2026-05-20

**Status**: Draft

**Input**: User description: "material-ingestion project is currently mainly uns related but its contents in root , I need to refeactor it so that I dont get mixed up when creating others like uns. there maybe shared things at base but want related implementations in proper folders. I want to preserve and utilise the folder structures to some point. Also everything seems cli whilst in the end this will not be a cli project most probably, pipeline shoould execute for different things like cli, or future and I shoould noot be executing them one by one by hand."

## Clarifications

### Session 2026-05-20

- Q: Which two invocation channels are in initial scope for orchestration parity? → A: CLI and HTTP API
- Q: How should conflicting concurrent runs for the same ingestion context be handled? → A: Queue new run if same context is active
- Q: How should downstream-stage failure be handled after earlier stages succeed? → A: Stop, mark failed, allow resume from last successful stage
- Q: What ownership policy should govern folder structure boundaries? → A: Enforce strict ownership (`shared/`, `material-ingestion/`, `uns/`) with no exceptions

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Separate Domain Boundaries (Priority: P1)

As a contributor, I need material-ingestion functionality to live in clearly dedicated project areas so it does not get mixed with UNS-related work.

**Why this priority**: Clear boundaries are required to prevent ongoing confusion and accidental cross-domain changes.

**Independent Test**: Can be fully tested by onboarding a contributor to add one material-ingestion change and confirming they can complete it without touching UNS implementation locations.

**Acceptance Scenarios**:

1. **Given** a contributor is adding a material-ingestion change, **When** they navigate the project structure, **Then** material-ingestion locations are explicit and distinct from UNS implementation locations.
2. **Given** a contributor is adding a UNS change, **When** they navigate the project structure, **Then** UNS locations remain isolated from material-ingestion implementation locations.

---

### User Story 2 - Reuse Shared Foundations Without Domain Mixing (Priority: P2)

As a contributor, I need shared building blocks to stay in a common base area while domain-specific logic stays in domain folders.

**Why this priority**: This preserves reuse while keeping ownership and maintenance clear.

**Independent Test**: Can be fully tested by creating one shared capability and confirming both domains can consume it without placing domain logic in shared areas.

**Acceptance Scenarios**:

1. **Given** a reusable capability is needed by multiple domains, **When** it is added, **Then** it is placed in the shared base area and referenced by each domain without duplicating behavior.
2. **Given** a change request is domain-specific, **When** it is implemented, **Then** the change is contained in that domain's implementation area rather than shared base areas.

---

### User Story 3 - Run Ingestion Through a Single Orchestration Flow (Priority: P3)

As an operator, I need ingestion pipelines to run from different invocation channels (current and future) without manually running multiple separate steps.

**Why this priority**: A single orchestration flow reduces operational friction and lowers execution error risk.

**Independent Test**: Can be fully tested by invoking the same ingestion workflow from at least two channels and verifying both execute equivalent end-to-end behavior.

**Acceptance Scenarios**:

1. **Given** an operator starts ingestion from one supported channel, **When** the workflow runs, **Then** all required pipeline stages execute automatically in the correct order.
2. **Given** an operator starts ingestion from a different supported channel, **When** the workflow runs, **Then** it follows the same orchestration rules and outcome expectations.

---

### Edge Cases

- If classification is ambiguous, the change is blocked from merge until a placement rule assigns it to exactly one ownership area (`shared/`, `material-ingestion/`, or `uns/`).
- On downstream-stage failure, the run stops immediately, is marked failed, and can be resumed from the last successful stage.
- Same-context run requests arriving during an active run are queued and executed in arrival order after the active run completes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define and document explicit ownership boundaries for material-ingestion, UNS, and shared base capabilities.
- **FR-001a**: Ownership boundaries MUST be enforced as strict folder ownership (`shared/`, `material-ingestion/`, `uns/`) with no exception paths.
- **FR-002**: The system MUST place material-ingestion implementation artifacts in dedicated material-ingestion locations separate from UNS implementation locations.
- **FR-003**: The system MUST preserve and continue to support existing shared base structures for cross-domain reuse.
- **FR-004**: The system MUST ensure shared base areas contain only cross-domain capabilities and no domain-specific behavior.
- **FR-005**: Contributors MUST be able to determine whether a change belongs to shared, material-ingestion, or UNS scope using documented placement rules.
- **FR-006**: The system MUST provide a single orchestration entry for ingestion execution that coordinates all required stages automatically.
- **FR-007**: The orchestration entry MUST be invocable from multiple channels without requiring manual step-by-step execution.
- **FR-007a**: Initial multi-channel support MUST include `CLI` and `HTTP API`.
- **FR-008**: The system MUST execute ingestion stages in a deterministic order with clear stage transition rules.
- **FR-009**: The system MUST produce execution outcomes that indicate full success, partial failure, or full failure for each run.
- **FR-009a**: On stage failure, the run MUST stop and be marked failed; resume MUST restart from the last successful stage rather than repeating all stages by default.
- **FR-010**: The system MUST prevent or safely manage conflicting concurrent runs targeting the same ingestion context.
- **FR-010a**: If a run is active for an ingestion context, additional requests for that same context MUST be queued and processed FIFO.
- **FR-011**: The system MUST provide actionable failure feedback that identifies which stage failed and what follow-up action is needed.
- **FR-012**: The system MUST include migration guidance so existing workflows move to the new structure without ambiguity.

### Key Entities *(include if feature involves data)*

- **Domain Area**: A logical ownership area (`material-ingestion`, `uns`, `shared`) with rules for what behavior can exist there.
- **Pipeline Run**: A single end-to-end ingestion execution request containing initiating channel, run context, stage states, and final outcome.
- **Execution Stage**: A named step in the ingestion flow with input prerequisites, completion criteria, and failure behavior.
- **Placement Rule**: A rule that maps a proposed change to the correct domain area.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of newly introduced material-ingestion changes in the first four weeks are placed in material-ingestion ownership areas with no UNS-location leakage.
- **SC-002**: At least 90% of contributors can correctly classify and place representative changes (shared vs domain-specific) on first attempt during review.
- **SC-003**: Operators can start a complete ingestion run in one action from each supported channel, with no manual stage-by-stage execution.
- **SC-003a**: 100% of initial-scope runs started from `CLI` and `HTTP API` follow the same stage sequence and outcome model.
- **SC-004**: At least 95% of successful ingestion runs complete all required stages without operator intervention.
- **SC-005**: Mean time to identify a failed stage and required follow-up action is under 5 minutes from run completion.

## Assumptions

- Existing UNS functionality remains active and should continue operating during and after restructuring.
- Shared base structures already contain reusable capabilities worth preserving.
- Initial rollout supports at least one current invocation channel and one additional channel path as part of orchestration standardization.
- Contributors performing migration have access to the placement rules and migration guidance.

## Constitution Alignment *(mandatory)*

- **CA-001 Spec Quality**: Problem statement, ownership boundaries, orchestration behavior, migration expectations, and out-of-scope boundaries are explicitly defined.
- **CA-002 Simplicity and Evolvability**: The feature separates shared and domain responsibilities to reduce coupling and support future non-CLI invocation channels.
- **CA-003 Validation Path**: Independent validation is defined per user story using placement checks, classification checks, and multi-channel orchestration execution checks.
- **CA-004 User-Centered Quality**: The feature improves contributor clarity, reduces operator manual effort, and defines handling for failure and concurrency edge states.
- **CA-005 Performance and Reliability**: Deterministic stage orchestration, conflict management, and explicit outcomes improve reliability and reduce run ambiguity.
- **CA-006 Documentation Fidelity**: Ownership rules, migration guidance, and run-operation guidance are required artifacts to keep contributors aligned.
