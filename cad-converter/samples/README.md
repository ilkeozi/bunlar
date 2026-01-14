# Samples

Place a STEP/IGES file here for smoke testing.

Default input path:
- `cad-converter/samples/input.step`

Default output path:
- `cad-converter/samples/output.gltf` (+ `cad-converter/samples/output.bin`)

Run the smoke test:

```bash
nx run cad-converter:smoke
```

To use a different file:

```bash
nx run cad-converter:smoke -- --input /absolute/or/workspace/relative/path.step
```
