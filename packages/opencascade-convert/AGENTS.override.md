# Agents Override (opencascade-convert)

## Scope

Applies to `packages/opencascade-convert`.

## Key notes

- Node-only library; do not add browser-specific code or bundler configs.
- `opencascade.js` is ESM; keep dynamic `import('opencascade.js/dist/node.js')` in the library.
- Preserve metadata defaults (names, colors, layers, materials) unless explicitly asked.
- Use Nx targets for local workflow:
  - `npx nx run opencascade-convert:build`
  - `npx nx run opencascade-convert:convert -- --input ...`

## Files of interest

- `packages/opencascade-convert/src/index.ts` (public API)
- `packages/opencascade-convert/src/converter.ts` (core conversion pipeline)
- `packages/opencascade-convert/src/occt/` (OpenCascade integration)
- `packages/opencascade-convert/src/cli.ts` (CLI entry)
- `packages/opencascade-convert/project.json` (Nx targets)
