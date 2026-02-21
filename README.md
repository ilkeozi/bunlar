# Bunlar

Nx monorepo for interactive science visualizations (chemistry + climate tech) plus a CAD conversion toolchain.

## Projects

- `frontend/` – Vite + React app with Tailwind and Three.js visualizations.
- `frontend-e2e/` – Playwright end-to-end tests for the frontend.
- `packages/opencascade-convert/` – STEP/IGES → glTF/GLB/OBJ converter built on `opencascade.js`.
- `docs/` – Product notes and UX references (for example `docs/atoms-visualizer.md`).

## Requirements

- Node.js >= 20.19 (older runtimes work but emit Vite engine warnings).

## Quick start

```bash
npm install
```

Run the app:

```bash
npx nx serve frontend
```

## Common commands

Run unit tests:

```bash
npx nx test frontend
```

Run end-to-end tests:

```bash
npx nx e2e frontend-e2e
```

Build the CAD converter:

```bash
npx nx run opencascade-convert:build
```

Convert a CAD file:

```bash
npx nx run opencascade-convert:convert -- \
  --input /path/to/model.step \
  --output /path/to/model.glb \
  --format glb
```

## More details

- CAD converter docs: `packages/opencascade-convert/README.md`
- Frontend architecture and feature notes: `docs/`
