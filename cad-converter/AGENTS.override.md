# AGENTS.override.md

## CAD Converter notes

- The `cad-converter/` app converts STEP/IGES to glTF/GLB using FreeCAD 1.0.2 in a Docker image.
- Prefer running conversions via `nx run cad-converter:convert` or the Docker helper scripts.
- Export uses FreeCAD's headless importer and exporter, and tessellates shapes using FreeCAD mesh preferences or CLI overrides.
- Axis/plane helper objects are omitted; export targets the first top-level assembly or object.
- Place any local FreeCAD prefs under `cad-converter/config/` (ignored by git) and pass them via `--user-cfg`.
