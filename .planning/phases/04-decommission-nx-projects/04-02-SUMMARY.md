---
phase: 04-decommission-nx-projects
plan: 02
subsystem: infra
tags: [nx, npm-workspaces, typescript, monorepo]

# Dependency graph
requires:
  - phase: 04-decommission-nx-projects
    provides: '04-01 removed cad-converter from Nx project discovery'
provides:
  - 'Removed occt-api from Nx project discovery (explicit + inferred)'
  - 'Root workspace + TS build graph no longer traverse packages/occt-api'
affects:
  [
    phase-05-remove-unused-artifacts,
    phase-06-workspace-verification,
    nx-project-graph,
  ]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - 'Nx plugin scoping via include/exclude to prevent inferred projects'

key-files:
  created: []
  modified:
    - packages/occt-api/project.json
    - package.json
    - package-lock.json
    - tsconfig.json
    - nx.json

key-decisions:
  - 'Use an explicit npm workspaces allowlist (instead of negation globs) to reliably exclude packages/occt-api.'
  - 'Exclude packages/occt-api from @nx/js/typescript plugin inference to prevent Nx rediscovery.'

patterns-established:
  - 'Decommissioning Nx projects: remove project.json + drop workspace inclusion + remove root TS references + exclude from plugin inference when needed'

# Metrics
duration: 5 min
completed: 2026-02-13
---

# Phase 4 Plan 02: Decommission Nx Projects Summary

**occt-api is removed from the Nx project graph and can no longer be re-inferred from packages/occt-api.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-13T18:26:56Z
- **Completed:** 2026-02-13T18:32:46Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Deleted the explicit Nx project definition for occt-api.
- Excluded packages/occt-api from workspace + TS composite build traversal.
- Scoped Nx TypeScript inference to prevent occt-api rediscovery.

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove explicit Nx project config for occt-api** - `08259a4` (chore)
2. **Task 2: Exclude packages/occt-api from workspaces and align TS references** - `597b09b` (chore)

## Files Created/Modified

- `packages/occt-api/project.json` - Removed explicit Nx project definition.
- `package.json` - Workspace allowlist excludes packages/occt-api.
- `package-lock.json` - Updated to match new workspaces.
- `tsconfig.json` - Root project references no longer include packages/occt-api.
- `nx.json` - Excludes packages/occt-api from @nx/js/typescript plugin inference.

## Decisions Made

None - followed plan as specified (using the plan's documented workspaces allowlist fallback).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Nx still inferred @bunlar/occt-api after workspace exclusion**

- **Found during:** Task 2 (Exclude packages/occt-api from npm workspaces and align TypeScript references)
- **Issue:** Even after moving to an explicit workspace allowlist, `npx nx show projects` still listed `@bunlar/occt-api`.
- **Fix:** Added an exclude glob to the `@nx/js/typescript` plugin configuration so Nx does not infer projects from `packages/occt-api/**`.
- **Files modified:** `nx.json`
- **Verification:** Task 2 verify command passed (Nx projects JSON contains no `occt-api`/`@bunlar/occt-api`; `nx graph` HTML generated).
- **Committed in:** `597b09b` (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required to satisfy NX-02 (prevent rediscovery). No scope creep.

## Issues Encountered

- `npm install` emitted peer dependency override warnings and existing vulnerability audit output; lockfile updated as required by the plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for Phase 5 (delete decommissioned artifacts and clean up remaining references).

---

_Phase: 04-decommission-nx-projects_
_Completed: 2026-02-13_
