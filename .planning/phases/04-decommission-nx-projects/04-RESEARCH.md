# Phase 4: Decommission Nx Projects - Research

**Researched:** 2026-02-13
**Domain:** Nx (v22) project discovery + workspace configuration cleanup
**Confidence:** HIGH

## Summary

This phase is primarily about Nx _project discovery_, not code changes: ensure `cad-converter` and `occt-api` no longer appear as Nx projects (`nx show projects`, project graph) and that no repo scripts/docs/CI still invoke them via `nx run`.

In this repo, `cad-converter` is an Nx project because it has an explicit `cad-converter/project.json`. `occt-api` is an Nx project for two reasons: it has `packages/occt-api/project.json`, and (critically) its `packages/occt-api/package.json` is inside the root `package.json` `workspaces` glob (`packages/*`), which Nx includes as projects by default. Removing only `project.json` is _not sufficient_ to satisfy NX-02; you must also exclude `packages/occt-api` from npm workspaces (or delete it).

**Primary recommendation:** Remove `cad-converter/project.json`, remove `packages/occt-api/project.json`, and exclude `packages/occt-api` from root `package.json` workspaces (then update lockfile), followed by `npx nx reset` + `npx nx show projects` verification.

## Standard Stack

### Core

| Tool                      | Version (repo)            | Purpose                                                                 | Why Standard                                          |
| ------------------------- | ------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------- |
| Nx                        | `22.3.3` (`package.json`) | Project graph, task running, CI orchestration                           | Workspace-wide convention for build/test/e2e          |
| npm workspaces            | (root `package.json`)     | Defines workspace packages (Nx treats these `package.json` as projects) | Nx uses workspaces to include `package.json` projects |
| `project.json`            | (per-project)             | Explicit Nx project definition                                          | Determines project name/root/targets                  |
| `package.json` `nx` field | (optional)                | Project configuration without `project.json`                            | Nx merges inferred tasks + `nx.targets`               |

### Supporting

| Tool/Command                 | Purpose                                             | When to Use                                 |
| ---------------------------- | --------------------------------------------------- | ------------------------------------------- |
| `npx nx show projects`       | Authoritative list of projects Nx currently sees    | Before/after removals                       |
| `npx nx show project <name>` | Confirms project exists and where config comes from | Detects “still inferred” projects           |
| `npx nx reset`               | Clears Nx daemon + cached project graph state       | After changing workspaces/project discovery |
| `rg` (ripgrep)               | Find leftover references in repo                    | Before final verification                   |

## Architecture Patterns

### Where Nx Projects Are Defined In This Repo (current)

- **Explicit `project.json`:**
  - `cad-converter/project.json` (targets: `convert`, `docker-build`, `smoke`)
  - `packages/occt-api/project.json` (target: `serve`)
  - `packages/opencascade-convert/project.json`
- **Inferred / package.json projects (workspaces):**
  - Root `package.json` has `workspaces: ["packages/*", "frontend", "frontend-e2e"]`
  - Nx currently lists:
    - `@bunlar/frontend`, `@bunlar/frontend-e2e` (from their `package.json` names)
    - `occt-api` (explicit project name overrides the package name)

### Pattern: Removing a `project.json`-defined Project

**What:** Delete the `project.json` file and remove references to its targets.
**When to use:** Projects that only exist in Nx via `project.json` (example: `cad-converter`).
**Repo evidence:** `cad-converter` has no `package.json`, so once `cad-converter/project.json` is removed, it should no longer be discovered.

### Pattern: Removing a Workspace Package Project

**What:** Exclude the package path from root workspaces so Nx does not include its `package.json` as a project.
**When to use:** Any `packages/*/package.json` that should not appear in the Nx graph (example: `packages/occt-api`).
**Example (root `package.json`):**

```jsonc
{
  "workspaces": ["packages/*", "!packages/occt-api", "frontend", "frontend-e2e"]
}
```

**Source:** Nx docs: project configuration reference ("Including package.json files as projects in the graph").

### Anti-Patterns to Avoid

- **Assume deleting `packages/occt-api/project.json` is enough:** Nx will still include `packages/occt-api/package.json` as a project because it is matched by root `workspaces`.
- **Edit `.nx/workspace-data/*` files:** they are generated cache; clear with `npx nx reset` instead.
- **Leave docs/scripts invoking removed targets:** `nx run cad-converter:convert` / `nx run occt-api:serve` will become broken commands.

## Don't Hand-Roll

| Problem                       | Don't Build                                       | Use Instead                                           | Why                                                     |
| ----------------------------- | ------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------- |
| “Is the project still in Nx?” | Manually inspect cached `.nx/workspace-data` JSON | `npx nx show projects` + `npx nx show project <name>` | Commands reflect Nx’s current discovery + merged config |
| “Nx still shows old graph”    | Delete random `.nx` files by hand                 | `npx nx reset`                                        | Correctly clears daemon + cached graph state            |

## Common Pitfalls

### Pitfall: `occt-api` comes back under a different name

**What goes wrong:** After removing `packages/occt-api/project.json`, `nx show projects` may still list `@bunlar/occt-api` (package-based project).
**Why it happens:** Nx includes any workspace `package.json` as a project (root `workspaces` matches `packages/occt-api`).
**How to avoid:** Add `"!packages/occt-api"` to root `package.json` workspaces (or remove the folder entirely).
**Warning signs:** `npx nx show project @bunlar/occt-api` still succeeds.

### Pitfall: `npm ci` fails after changing workspaces

**What goes wrong:** CI errors because `package-lock.json` no longer matches root `package.json` workspaces.
**Why it happens:** npm lockfiles include workspace packages; changing `workspaces` requires regenerating the lockfile.
**How to avoid:** Run `npm install` once (not `npm ci`) after workspaces change; commit updated `package-lock.json`.

### Pitfall: TypeScript project references still include decommissioned package

**What goes wrong:** `tsc -b` or editor tooling still traverses `./packages/occt-api` because it is in `tsconfig.json` references.
**Why it happens:** Root `tsconfig.json` currently references `./packages/occt-api`.
**How to avoid:** Remove that reference if `occt-api` is truly decommissioned (aligns TS build graph with Nx graph).
**Warning signs:** Typecheck/build touches `packages/occt-api` unexpectedly.

## Code Examples

### Verify project removal (local)

```bash
# Clean cached graph state
npx nx reset

# Ensure projects are gone
npx nx show projects

# Should fail / exit non-zero once removed
npx nx show project cad-converter
npx nx show project occt-api
npx nx show project @bunlar/occt-api
```

### Find and remove leftover invocations

```bash
rg "nx run cad-converter" -n
rg "nx run occt-api" -n
rg "cad-converter:" -n
rg "occt-api:" -n
```

## State of the Art

| Old Approach                                | Current Approach (Nx v17+; in use here)                                                                    | Impact                                                                                         |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Central `workspace.json` lists all projects | Project discovery from `project.json` + workspace `package.json` (workspaces) + inferred tasks via plugins | Removing a project often requires updating _both_ `project.json` and `package.json` workspaces |

## Open Questions

1. **Is Phase 4 “remove from Nx” only, or also “remove from repo”?**
   - What we know: ROADMAP/REQUIREMENTS emphasize Nx graph/targets removal (NX-01/NX-02).
   - What's unclear: Whether `packages/occt-api` and `cad-converter` directories should be deleted in this phase.
   - Recommendation: Plan Phase 4 to meet NX-01/NX-02 without deleting code; keep deletion as a separate explicit step if needed.

## Sources

### Primary (HIGH confidence)

- Nx docs - `nx.json` reference (plugins include/exclude; cache reset guidance): https://nx.dev/reference/nx-json
- Nx docs - project configuration reference (workspaces `package.json` become projects; ignore by excluding from workspaces): https://nx.dev/reference/project-configuration

### Repository evidence (HIGH confidence)

- `cad-converter/project.json` (explicit Nx project)
- `packages/occt-api/project.json` + `packages/occt-api/package.json` (explicit + workspace package)
- Root `package.json` (`workspaces` includes `packages/*`; Nx `22.3.3`)
- Root `tsconfig.json` (references `./packages/occt-api`)
- `npx nx show projects` output includes `cad-converter` and `occt-api` today

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - verified via repo files + Nx docs
- Architecture: HIGH - verified via repo project discovery + Nx docs
- Pitfalls: HIGH - directly observed risks in this repo’s current config

**Valid until:** 2026-03-15 (Nx config behavior is stable, but verify if Nx upgrades)
