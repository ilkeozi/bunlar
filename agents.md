# Agents Guide

This workspace is an Nx monorepo centered on an interactive atomic visualizer built with React (Vite) and Playwright end-to-end tests. The key folders you will work with are outlined below.

## Top-Level Layout

- `frontend/` – Vite/React application that renders the atom visualizer experience.
- `frontend-e2e/` – Playwright configuration and specs that exercise `frontend` end-to-end.
- `docs/` – Markdown references for the product (e.g. `atoms-visualizer.md`).
- `packages/` – Reserved for shareable Nx libraries (currently empty).
- `node_modules/`, `package.json`, `nx.json`, `tsconfig*.json` – Workspace tooling and dependency management.

## Frontend App (`frontend/`)

The app is a Vite project configured via `vite.config.mts` and TypeScript `tsconfig.*.json` files. The main entry point is `src/main.tsx`, which mounts the React tree and imports the Tailwind-based global stylesheet (`src/styles.css`). Nx treats this package as a standalone workspace, so any generators or task runs should target the `frontend` project name.

### `src/app`

- `app.tsx` – Composes the overall UI shell with Tailwind utility classes and shadcn components.
- `components/` – Feature-facing UI pieces (element selector, stats, subject selector, etc.) built on Radix + shadcn primitives.
- `data/` – Static data sources such as the periodic element definitions.
- `i18n/` – Lightweight translation helpers and copy tables.
- `lessons/` – Views and layouts tailored to educational content (e.g. periodic table scene).
- `state/` – Zustand stores that manage atom selection and learning state.
- `utils/` – Simulation helpers like particle distribution math.
- `visualizer/` – Three.js scene graph pieces: atom canvas, nucleus, electron cloud, lighting rigs, and associated color/texture hooks.

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

- Generate new UI primitives with `npx shadcn@latest add <component>` from the `frontend/` directory; output lands in `src/components/ui` and respects the alias config.
- Prefer colocating feature-specific components under `src/app/components` or `src/app/lessons` so that shared primitives stay focused.
- Zustand stores in `src/app/state` should expose selectors for components to avoid unnecessary rerenders; follow the pattern used by `useAtomStore` and `useLearningStore`.
- Three.js systems live under `src/app/visualizer`; keep React Three Fiber hooks out of generic UI directories to preserve tree shaking.

## End-to-End Tests (`frontend-e2e/`)

- `playwright.config.ts` configures browsers, timeouts, and project options.
- `src/example.spec.ts` demonstrates navigating the app and asserting UI behavior.
- `test-output/` captures Playwright artifacts (videos, traces) from recent runs.

## Documentation (`docs/`)

- `atoms-visualizer.md` – Product notes that explain goals and UX decisions for the atom visualizer.

## Workflow Notes

- Run app locally with `npx nx serve frontend`.
- Execute unit tests via `npx nx test frontend` and Playwright specs with `npx nx e2e frontend-e2e`.
- Generate additional libraries in `packages/` using Nx generators when you need shared logic.
- Keep Node.js ≥20.19 around to satisfy the Vite engine check; older runtimes will build but emit warnings.

Keep this guide handy when orienting new contributors or wiring up automation agents.
