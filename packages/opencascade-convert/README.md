# opencascade-convert

STEP/IGES → glTF/GLB/OBJ converter built on `opencascade.js` (Node + browser buffer API).

## Why this package

- Designed to run inside this Nx workspace (not published yet).
- Preserves metadata where available (part names, colors/materials, layers).
- Provides a CLI and TypeScript API suitable for publishing later.
- Exposes assembly metadata (BOM + node map) for downstream mapping.

## How it works

`opencascade-convert` uses `opencascade.js`, a WebAssembly (WASM) build of the Open CASCADE
Technology (OCCT) CAD kernel. The converter runs in Node.js, loads the OCCT WASM module, parses
STEP/IGES into an in-memory XCAF document, triangulates geometry, and writes glTF/GLB/OBJ files
from that document.

### Tech stack

- OCCT via `opencascade.js` (WASM + JS bindings)
- Node.js filesystem I/O (reads input, writes output)
- XCAF document model to preserve metadata where available
- Triangulation via OCCT mesh tools

### What is preserved

When present in the source CAD file and supported by OCCT:

- Part/product names
- Colors and materials
- Layers

### Limitations

- Conversion depends on triangulation settings; coarse settings are faster but less detailed.
- Names fall back to OCCT instance IDs (e.g. `NAUO###`) when the source file lacks product names.
- Large assemblies can take time and memory during triangulation.
- Assembly trees reuse product definitions; expect repeated occurrences for a single part.

## Workspace install

```bash
npm install
```

## CLI (Nx workspace)

```bash
npx nx run opencascade-convert:convert -- \
  --input /path/to/model.step \
  --output /path/to/model.glb \
  --format glb \
  --name-format productOrInstance \
  --linDeflection 1 \
  --angDeflection 0.5 \
  --parallel
```

Disable metadata preservation if needed:

```bash
npx nx run opencascade-convert:convert -- --input model.step --output model.glb --no-names
```

Write assembly metadata alongside the conversion:

```bash
npx nx run opencascade-convert:convert -- \
  --input /path/to/model.step \
  --output /path/to/model.glb \
  --bom-out /path/to/model.bom.json \
  --node-map-out /path/to/model.nodes.json
```

## API

```ts
import { createConverter } from 'opencascade-convert';

const converter = await createConverter();
const docHandle = converter.read('/path/to/model.step', 'step', {
  preserveNames: true,
  preserveColors: true,
  preserveLayers: true,
  preserveMaterials: true,
});
converter.triangulate(docHandle.get(), {
  linearDeflection: 1,
  angularDeflection: 0.5,
  parallel: true,
});
converter.write(docHandle, '/path/to/model.glb', 'glb', {
  nameFormat: 'productOrInstance',
});

const nodeMap = converter.createNodeMap(docHandle);
const bom = converter.createBom(docHandle);
```

### Buffer API (Node + Browser)

```ts
import { convertBuffer } from 'opencascade-convert';
import fs from 'node:fs';

const input = fs.readFileSync('/path/to/model.step');
const result = await convertBuffer({
  input,
  inputFormat: 'step',
  outputFormat: 'glb',
});

fs.writeFileSync('/path/to/model.glb', result.glb);
```

### Browser usage

Use the browser entry point and bundle `opencascade.js`'s WASM asset:

```ts
import { convertBuffer } from 'opencascade-convert/browser';

const result = await convertBuffer({
  input: myStepBytes,
  inputFormat: 'step',
  outputFormat: 'glb',
});
```

When bundling for the browser, make sure your bundler is configured to handle `opencascade.js`'s
`.wasm` asset (see the OpenCascade.js "Configuring Your Bundler" guide on ocjs.org).

## Name preservation notes

- If you still see `NAUO###` in Blender, the STEP file likely lacks product names.
- Export as AP242 (or enable product/part names) from your CAD tool for best results.
- The default glTF name format is `productOrInstance`.

## Assembly metadata (BOM + node map)

`createNodeMap` and `createBom` provide stable IDs you can map to glTF nodes.

`nodeMap` shape:

```json
{
  "roots": ["0:1"],
  "nodes": {
    "0:1": {
      "id": "0:1",
      "labelEntry": "0:1",
      "name": "Gear Box",
      "kind": "assembly",
      "productId": "0:1",
      "productName": "Gear Box",
      "parentId": null,
      "children": ["0:1/0:1:2"],
      "path": ["0:1"]
    }
  }
}
```

`bom` shape:

```json
{
  "roots": ["0:1"],
  "items": [
    {
      "productId": "0:1:2",
      "productName": "Flat Washer",
      "kind": "part",
      "quantity": 4,
      "instances": [
        {
          "nodeId": "0:1/0:1:2:1",
          "instanceId": "0:1:2:1",
          "name": "Flat Washer",
          "path": ["0:1", "0:1:2:1"]
        }
      ]
    }
  ]
}
```

## Build

```bash
npx nx run opencascade-convert:build
```

## Tests

```bash
npx nx run opencascade-convert:test
```

### Integration tests (opt-in)

Uses `src/__tests__/sample/input.step`.

```bash
npx nx run opencascade-convert:test:integration
```

## Publishing later

When ready, publish from `packages/opencascade-convert`.
