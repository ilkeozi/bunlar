#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FREECAD_SCRIPT = SCRIPT_DIR / "freecad_export.py"


def require_binary(name: str, hint: str) -> None:
    if shutil.which(name):
        return
    print(f"Missing required executable: {name}", file=sys.stderr)
    print(hint, file=sys.stderr)
    raise SystemExit(2)


def run(cmd: list[str], env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, check=True, env=env)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert STEP to glTF/GLB using FreeCAD."
    )
    parser.add_argument("--input", required=True, help="Path to input STEP/IGES")
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output .gltf or .glb (default recommendation: .gltf)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable FreeCAD export debug output",
    )
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
    parser.add_argument(
        "--user-cfg",
        help="Path to FreeCAD user.cfg to reuse GUI export preferences",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    user_cfg_value = args.user_cfg or os.environ.get("CAD_USER_CFG")
    user_cfg_path = Path(user_cfg_value).resolve() if user_cfg_value else None

    if not input_path.exists():
        print(f"Input file does not exist: {input_path}", file=sys.stderr)
        raise SystemExit(2)
    if user_cfg_path and not user_cfg_path.exists():
        print(f"FreeCAD user.cfg not found: {user_cfg_path}", file=sys.stderr)
        raise SystemExit(2)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    require_binary("freecadcmd", "Install FreeCAD so freecadcmd is available.")

    env = os.environ.copy()
    env.update(
        {
            "CAD_INPUT": str(input_path),
            "CAD_OUTPUT": str(output_path),
        }
    )
    if args.linear_deflection is not None:
        env["CAD_LINEAR_DEFLECTION"] = str(args.linear_deflection)
    if args.angular_deflection is not None:
        env["CAD_ANGULAR_DEFLECTION"] = str(args.angular_deflection)
    env["CAD_SCRIPT"] = str(FREECAD_SCRIPT)
    if args.debug or os.environ.get("CAD_DEBUG") == "1":
        env["CAD_DEBUG"] = "1"
    try:
        cmd = ["freecadcmd"]
        if user_cfg_path:
            cmd.extend(["--user-cfg", str(user_cfg_path)])
        cmd.extend(
            [
                "-c",
                "import os, runpy, sys; script=os.environ['CAD_SCRIPT']; sys.argv=[script]; runpy.run_path(script, run_name='__main__')",
            ]
        )
        run(cmd, env=env)
    except subprocess.CalledProcessError as exc:
        if exc.returncode == -11:
            print(
                "FreeCAD crashed during import. Some STEP files trigger OCAF import issues.",
                file=sys.stderr,
            )
            print(
                "Try reducing file complexity or re-exporting from CAD with simpler assembly settings.",
                file=sys.stderr,
            )
        raise


if __name__ == "__main__":
    main()
