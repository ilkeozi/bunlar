<!--
Sync Impact Report
- Version change: template (unversioned) -> 1.0.0
- Modified principles:
  - PRINCIPLE_1_NAME -> I. Spec-First Delivery
  - PRINCIPLE_2_NAME -> II. Simplicity and Evolvability
  - PRINCIPLE_3_NAME -> III. Verification-First Delivery
  - PRINCIPLE_4_NAME -> IV. User-Centered Quality
  - PRINCIPLE_5_NAME -> V. Performance and Reliability Discipline
  - Added: VI. Documentation and Automation Fidelity
- Added sections:
  - Engineering Constraints
  - Delivery Workflow and Quality Gates
- Removed sections:
  - None
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md
  - ✅ .specify/templates/spec-template.md
  - ✅ .specify/templates/tasks-template.md
  - ⚠ pending: .specify/templates/commands/*.md (directory not present)
- Follow-up TODOs:
  - None
-->
# Bunlar Constitution

## Core Principles

### I. Spec-First Delivery
Non-trivial work MUST start from a clear specification before implementation begins.
Specifications MUST describe the user problem, expected behavior, acceptance criteria,
important constraints, and out-of-scope items. Scope changes MUST be reflected in the
specification before implementation continues.

### II. Simplicity and Evolvability
Implementation SHOULD prefer the simplest structure that solves the current problem while
keeping future refactoring possible. Abstractions, shared modules, architectural
boundaries, and reusable infrastructure MUST be justified by actual product needs,
maintainability needs, or repeated usage. Premature architecture MUST be avoided.

### III. Verification-First Delivery
Every change MUST define an appropriate validation path before it is considered complete.
Automated tests SHOULD be used where practical, especially for business logic, data
transformations, permissions, API behavior, critical UI flows, and regression-prone
behavior. When automated tests are not feasible or not yet justified, the change MUST
include clear, repeatable manual validation steps. Bug fixes SHOULD include regression
tests when practical.

### IV. User-Centered Quality
User-facing behavior MUST be understandable, consistent with the existing product
experience, and accessible where practical. UX complexity MUST be justified by user
value. New flows SHOULD handle empty, loading, error, and edge states intentionally.

### V. Performance and Reliability Discipline
Changes affecting loading, rendering, data fetching, background work, or interactive
behavior MUST consider performance, error handling, and graceful failure.
Performance-sensitive changes SHOULD document expected impact and validation approach.

### VI. Documentation and Automation Fidelity
Workflow, tooling, architecture, and behavior changes MUST update the relevant project
guidance when they change how humans or agents should work. Project-specific commands,
folder conventions, runtime versions, framework details, and local development
instructions SHOULD live in AGENTS.md, README.md, or project documentation rather than
in this constitution.

## Engineering Constraints

- This constitution MUST stay at principle and governance level.
- Exact stack, commands, folder conventions, and runtime versions SHOULD be defined in
  AGENTS.md, README.md, or project documentation.
- Shared code MUST have a clear reason to be shared.
- Public interfaces, data contracts, and user-facing behavior changes SHOULD be
  documented.
- Secrets, tokens, credentials, local environment files, and private keys MUST NOT be
  committed.
- New dependencies SHOULD be justified by clear product or maintenance value.

## Delivery Workflow and Quality Gates

- Specification artifacts SHOULD be created or updated in order: `spec.md` -> `plan.md`
  -> `tasks.md`.
- Planning MUST include a constitution check.
- Each user story or implementation slice MUST have an independent validation path.
- Risky or behavior-changing work MUST include automated tests or documented manual
  validation.
- Bug fixes SHOULD include regression coverage when practical.
- Plans SHOULD identify risks, trade-offs, and assumptions.
- Reviews MUST confirm alignment with the relevant specification, validation path, and
  applicable project guidance.

## Governance

- This constitution supersedes lower-level guidance when there is conflict.
- AGENTS.md, README.md, specifications, and project documentation provide
  implementation-specific guidance.
- Amendments require rationale, Sync Impact Report update, template alignment review, and
  semantic version update.
- Semantic versioning policy:
  - MAJOR for incompatible removals or redefinitions of principles.
  - MINOR for new principles, new sections, or materially expanded obligations.
  - PATCH for clarifications that do not change policy intent.

**Version**: 1.0.0 | **Ratified**: 2026-05-20 | **Last Amended**: 2026-05-20
