#!/usr/bin/env python3
import argparse
import math
import os
import sys
from pathlib import Path

import FreeCAD as App


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import STEP/IGES in FreeCAD and export a GLB."
    )
    parser.add_argument("--input", help="Path to input STEP/IGES")
    parser.add_argument("--output", help="Path to output GLB/GLTF")
    parser.add_argument(
        "--linear-deflection",
        type=float,
        default=None,
        help="Override mesh linear deflection",
    )
    parser.add_argument(
        "--angular-deflection",
        type=float,
        default=None,
        help="Override mesh angular deflection (radians)",
    )
    return parser.parse_args()


def get_mesh_params(args: argparse.Namespace) -> tuple[float, float]:
    part_params = App.ParamGet("User parameter:BaseApp/Preferences/Mod/Part")
    linear = part_params.GetFloat("MeshDeviation", 0.1)
    angular = part_params.GetFloat("MeshAngularDeflection", 0.523599)
    if angular > math.tau:
        angular = math.radians(angular)
    env_linear = os.environ.get("CAD_LINEAR_DEFLECTION")
    env_angular = os.environ.get("CAD_ANGULAR_DEFLECTION")
    if env_linear:
        try:
            linear = float(env_linear)
        except ValueError:
            print(
                f"Invalid CAD_LINEAR_DEFLECTION: {env_linear}",
                file=sys.stderr,
            )
            raise SystemExit(2)
    if env_angular:
        try:
            angular = float(env_angular)
        except ValueError:
            print(
                f"Invalid CAD_ANGULAR_DEFLECTION: {env_angular}",
                file=sys.stderr,
            )
            raise SystemExit(2)
    if args.linear_deflection is not None:
        linear = float(args.linear_deflection)
    if args.angular_deflection is not None:
        angular = float(args.angular_deflection)
    return linear, angular


def ensure_tessellation(doc, args: argparse.Namespace) -> None:
    linear, angular = get_mesh_params(args)
    for obj in doc.Objects:
        shape = getattr(obj, "Shape", None)
        if shape is None:
            continue
        try:
            if shape.isNull():
                continue
        except Exception:
            continue
        try:
            shape.tessellate(linear, angular)
        except TypeError:
            shape.tessellate(linear)
        except Exception as exc:
            print(
                f"Failed to tessellate {getattr(obj, 'Label', obj.Name)}: {exc}",
                file=sys.stderr,
            )


def is_helper_object(obj) -> bool:
    name = getattr(obj, "Name", "") or ""
    label = getattr(obj, "Label", "") or ""
    name_prefixes = (
        "Origin",
        "X_Axis",
        "Y_Axis",
        "Z_Axis",
        "XY_Plane",
        "XZ_Plane",
        "YZ_Plane",
    )
    label_prefixes = (
        "Origin",
        "X-axis",
        "Y-axis",
        "Z-axis",
        "XY-plane",
        "XZ-plane",
        "YZ-plane",
    )
    return name.startswith(name_prefixes) or label.startswith(label_prefixes)


def select_export_objects(doc) -> list:
    group_children: set[str] = set()
    for obj in doc.Objects:
        if is_helper_object(obj):
            continue
        children = getattr(obj, "Group", None)
        if not children:
            continue
        for child in children:
            group_children.add(child.Name)
    export_objects = []
    for obj in doc.Objects:
        if is_helper_object(obj):
            continue
        if obj.Name in group_children:
            continue
        export_objects.append(obj)
    if export_objects:
        for obj in export_objects:
            children = getattr(obj, "Group", None)
            if children:
                return [obj]
        return [export_objects[0]]
    export_objects = [obj for obj in doc.Objects if not is_helper_object(obj)]
    return export_objects


def main() -> None:
    args = parse_args()
    input_value = args.input or os.environ.get("CAD_INPUT")
    output_value = args.output or os.environ.get("CAD_OUTPUT")

    if not input_value or not output_value:
        print(
            "Missing --input/--output (or CAD_INPUT/CAD_OUTPUT).",
            file=sys.stderr,
        )
        raise SystemExit(2)

    input_path = Path(str(input_value)).resolve()
    output_path = Path(str(output_value)).resolve()

    if not input_path.exists():
        print(f"Input file does not exist: {input_path}", file=sys.stderr)
        raise SystemExit(2)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = None
    importer = None
    try:
        import Import

        importer = Import
        try:
            doc = importer.open(str(input_path))
        except Exception:
            doc = None
        if doc is None:
            doc = App.newDocument("CadImport")
            try:
                importer.insert(str(input_path), doc.Name, False)
            except TypeError:
                importer.insert(str(input_path), doc.Name)
    except Exception as exc:
        print(f"Failed to import via FreeCAD Import: {exc}", file=sys.stderr)
        doc = None

    if doc is None:
        print("FreeCAD import failed; no document available.", file=sys.stderr)
        raise SystemExit(2)

    doc.recompute()
    ensure_tessellation(doc, args)

    if output_path.suffix.lower() not in (".glb", ".gltf"):
        print("Output must be .glb or .gltf for FreeCAD export.", file=sys.stderr)
        raise SystemExit(2)
    if importer is None or not hasattr(importer, "export"):
        print(
            "FreeCAD Import.export not available; cannot export glTF/GLB.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    export_objects = select_export_objects(doc)
    try:
        importer.export(export_objects, str(output_path))
    except Exception as exc:
        print(f"Import.export failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
    finally:
        if doc is not None:
            App.closeDocument(doc.Name)

    if not output_path.exists():
        print("Import.export did not create an output file.", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
