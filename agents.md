# Agents Guide

This workspace is an Nx monorepo centered on interactive science visualizations (chemistry + climate tech) built with React (Vite) and Playwright end-to-end tests. The key folders you will work with are outlined below.

## Top-Level Layout

- `apps/frontend/` – Vite/React application that renders the chemistry + climate-tech visualizations.
- `cad-converter/` – Dockerized FreeCAD-based STEP/IGES → glTF/GLB converter.
- `apps/frontend-e2e/` – Playwright configuration and specs that exercise `frontend` end-to-end.
- `docs/` – Markdown references for the product (e.g. `atoms-visualizer.md`).
- `packages/` – Reserved for shareable Nx libraries (currently empty).
- `node_modules/`, `package.json`, `nx.json`, `tsconfig*.json` – Workspace tooling and dependency management.

## Frontend App (`apps/frontend/`)

The app is a Vite project configured via `vite.config.mts` and TypeScript `tsconfig.*.json` files. The main entry point is `src/main.tsx`, which mounts the React tree and imports the Tailwind-based global stylesheet (`src/styles.css`). Nx treats this package as a standalone workspace, so any generators or task runs should target the `frontend` project name.

### `src/app`

- `app.tsx` – Composes the overall UI shell with Tailwind utility classes and shadcn components.
- `components/` – Shared app UI (site header, language selector, subject cards).
- `data/` – Static data sources (periodic elements, climate-tech parts catalog).
- `features/` – Domain modules (see below).
- `i18n/` – Lightweight translation helpers and copy tables.
- `pages/` – Route-level pages (subjects, module pages).
- `state/` – Global Zustand stores (language, app state).

### `src/app/features`

- `chemistry/<model>/` – Each model (bohr, dalton, rutherford, thomson) keeps its own `components/`, `state/`, and `visualizer/` folders.
- `climate-tech/carbon-aware-motor-assembly/` – Feature-specific `components/`, `visualizer/`, and `types` for the gearbox assembly experience. Theater mode is implemented via `TheaterShell` and uses a tooltip avoid-rect to keep callouts off the controls; if tooltips still overlap the panel (see recent screenshots), adjust the avoid-rect logic or controls layout.

### Other notable folders

- `src/components/ui/` – Shared shadcn UI primitives (button, card, select, switch, etc.).
- `src/lib/` – Cross-cutting helpers (e.g. the `cn` Tailwind class combiner).
- `src/assets/` – Static assets consumed by the React app.
- `public/` – Files served as-is by Vite (favicons, manifest, etc.).
- `dist/` – Production build output (generated).

### Styling & design system

- Tailwind is configured through `tailwind.config.ts` and `postcss.config.cjs`.
- `components.json` drives shadcn component generation (aliases map to `@/components` and `@/lib`).
- Global design tokens live in `src/styles.css`; component styles rely on Tailwind utilities rather than bespoke CSS modules.

### Code generation & conventions

- Generate new UI primitives with `npx shadcn@latest add <component>` from the `apps/frontend/` directory; output lands in `src/components/ui` and respects the alias config.
- Prefer colocating feature-specific components under `src/app/features/<domain>/<module>/components` so that shared primitives stay focused.
- Zustand stores in `src/app/state` should expose selectors for components to avoid unnecessary rerenders; follow the pattern used by `useAtomStore` and `useLearningStore`.
- Three.js systems live under each feature's `visualizer/` folder (e.g., `features/chemistry/*/visualizer`, `features/climate-tech/*/visualizer`). Keep React Three Fiber hooks out of generic UI directories to preserve tree shaking.

## End-to-End Tests (`apps/frontend-e2e/`)

- `playwright.config.ts` configures browsers, timeouts, and project options.
- `src/example.spec.ts` demonstrates navigating the app and asserting UI behavior.
- `test-output/` captures Playwright artifacts (videos, traces) from recent runs.

## Documentation (`docs/`)

- `atoms-visualizer.md` – Product notes that explain goals and UX decisions for the atom visualizer.

## Workflow Notes

- Run app locally with `npx nx serve frontend`.
- Execute unit tests via `npx nx test frontend` and Playwright specs with `npx nx e2e frontend-e2e`.
- Build the CAD converter image with `npx nx run cad-converter:docker-build`.
- Run the converter with `npx nx run cad-converter:convert`.
- Generate additional libraries in `packages/` using Nx generators when you need shared logic.
- Keep Node.js ≥20.19 around to satisfy the Vite engine check; older runtimes will build but emit warnings.

Keep this guide handy when orienting new contributors or wiring up automation agents.

## Codex automation

- Codex discovers this file as `AGENTS.md` at the repo root; add `AGENTS.override.md` in subdirectories for scoped overrides.
- Codex uses the global config by default; set `CODEX_HOME` only when you need a repo-specific profile.
- Update `AGENTS.md` or scoped overrides when changes affect workflows, project layout, or automation expectations.
- MCP servers: `openaiDeveloperDocs` for OpenAI/Codex docs; `nx-mcp` for Nx graph/tasks; `shadcn` for UI primitives under `apps/frontend/src/components/ui`.
- If a Codex skill is available, open its `SKILL.md` and follow the prescribed workflow or scripts.
- Always use the OpenAI developer documentation MCP server if you need to work with the OpenAI API, ChatGPT Apps SDK, Codex, or related docs without me having to explicitly ask.
- Prefer the `openaiDeveloperDocs` MCP server for documentation lookups whenever possible, and mention when a source could not be reached.
- When MCP servers exist for a task (for example `shadcn` or `nx-mcp`), use them as the primary source of truth before falling back to manual lookups.

### Available skills (repo-local)

- `vercel-react-best-practices` (path: `.codex/skills/vercel-react-best-practices` → `.agents/skills/vercel-react-best-practices/SKILL.md`)
- `web-design-guidelines` (path: `.codex/skills/web-design-guidelines` → `.agents/skills/web-design-guidelines/SKILL.md`)

## Codex verification

- Run `codex mcp list` to confirm MCP servers are registered.
- Run `codex exec "Summarize the current instructions."` from the repo root to verify instruction discovery order.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
