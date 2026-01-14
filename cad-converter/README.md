# CAD Converter

Programmatic STEP/IGES to glTF/GLB conversion using FreeCAD (headless Import/export).

## Docker (recommended, AWS-friendly)

```bash
nx run cad-converter:convert -- --input /path/to/model.step --output /path/to/model.gltf
```

This target builds the image on first run if it does not exist.

```bash
nx run cad-converter:docker-build
```

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /app \
  bunlar-cad-converter \
  --input /workspace/path/to/model.step \
  --output /workspace/path/to/model.gltf
```

The Docker image is built on Ubuntu 22.04 and extracts the FreeCAD 1.0.2 AppImage, so it is
suitable for AWS Batch/ECS/Fargate deployments without platform-specific installs.

To reuse GUI export preferences, pass a FreeCAD `user.cfg` that is available inside the container:

```bash
nx run cad-converter:convert -- \
  --input /path/to/model.step \
  --output /path/to/model.gltf \
  --user-cfg /path/to/FreeCAD/user.cfg
```

When running in Docker, the `user.cfg` path must be inside the repo so it is available at
`/workspace/...` in the container. The smoke test helper remaps host paths for you.

You can also override tessellation directly:

```bash
nx run cad-converter:convert -- \
  --input /path/to/model.step \
  --output /path/to/model.gltf \
  --linear-deflection 0.4 \
  --angular-deflection 0.8
```

## Smoke test (optional)

```bash
nx run cad-converter:smoke
```

Place a STEP file at `cad-converter/samples/input.step` or pass `--input` to point at another
file. Output defaults to `cad-converter/samples/output.gltf`.

You can also pass `--user-cfg` to reuse GUI export preferences during the smoke test.

## Inspect output (optional)

```bash
python3 cad-converter/scripts/inspect_glb.py --input cad-converter/samples/output.gltf --tree
```

## AWS outline (optional)

```bash
docker build -t bunlar-cad-converter -f cad-converter/Dockerfile .
```

Push to ECR and run as a Batch/ECS job with the same `--input/--output` args (paths inside the mounted
workspace or container volume).

## Local usage (optional)

```bash
python3 cad-converter/scripts/convert.py --input /path/to/model.step --output /path/to/model.gltf
```

Local usage requires `freecadcmd` on your PATH. For built-in glTF export without GUI modules,
prefer the FreeCAD 1.0.2 AppImage and expose `freecadcmd` from the extracted bundle.

## Notes

- This app only handles STEP/IGES to glTF/GLB for now and is intentionally metadata-agnostic.
- The converter uses FreeCAD's core glTF/GLB exporter via `freecadcmd` only.
- Manual GLB fallback is disabled; export fails if FreeCAD cannot write glTF/GLB.
- Export triggers tessellation using FreeCAD mesh preferences (from `user.cfg` if provided) or
  CLI overrides, omits FreeCAD origin/axis/plane helper objects, and exports the first
  top-level assembly (or first top-level object if no assemblies exist).
- Docker pins Ubuntu and FreeCAD versions for repeatability.
- Docker mounts the workspace at `/workspace`, so keep input/output paths inside the repo.
