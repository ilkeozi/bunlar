#!/usr/bin/env python3
import argparse
import json
import struct
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a GLB/GLTF file and print node hierarchy summary."
    )
    parser.add_argument("--input", required=True, help="Path to .glb or .gltf")
    parser.add_argument(
        "--tree",
        action="store_true",
        help="Print node tree (bounded by --max-depth/--max-nodes).",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=4,
        help="Max depth when printing node tree.",
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=200,
        help="Max nodes printed in tree view.",
    )
    return parser.parse_args()


def read_gltf(path: Path) -> dict:
    if path.suffix.lower() == ".gltf":
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    if path.suffix.lower() != ".glb":
        raise ValueError("Input must be .glb or .gltf.")
    data = path.read_bytes()
    if len(data) < 12:
        raise ValueError("GLB too small.")
    magic, version, length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF":
        raise ValueError("Invalid GLB magic header.")
    if version != 2:
        raise ValueError(f"Unsupported GLB version: {version}")
    if length != len(data):
        raise ValueError("GLB length mismatch.")
    offset = 12
    json_chunk = None
    while offset + 8 <= len(data):
        chunk_len, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk_data = data[offset : offset + chunk_len]
        offset += chunk_len
        if chunk_type == 0x4E4F534A:
            json_chunk = chunk_data
            break
    if json_chunk is None:
        raise ValueError("Missing JSON chunk in GLB.")
    return json.loads(json_chunk.decode("utf-8"))


def node_label(idx: int, node: dict) -> str:
    name = node.get("name")
    if name:
        return f"{idx}: {name}"
    return str(idx)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"Input not found: {input_path}", file=sys.stderr)
        raise SystemExit(2)

    try:
        gltf = read_gltf(input_path)
    except Exception as exc:
        print(f"Failed to parse glTF: {exc}", file=sys.stderr)
        raise SystemExit(2)

    nodes = gltf.get("nodes", [])
    scenes = gltf.get("scenes", [])
    scene_index = gltf.get("scene", 0)
    root_nodes = []
    if scenes and 0 <= scene_index < len(scenes):
        root_nodes = scenes[scene_index].get("nodes", [])

    meshes = gltf.get("meshes", [])
    materials = gltf.get("materials", [])

    print(f"Nodes: {len(nodes)}")
    print(f"Meshes: {len(meshes)}")
    print(f"Materials: {len(materials)}")
    if root_nodes:
        label_list = [node_label(i, nodes[i]) for i in root_nodes if i < len(nodes)]
        print(f"Root nodes ({len(root_nodes)}): " + ", ".join(label_list))
    else:
        print("Root nodes: <none>")

    if not args.tree:
        return

    printed = 0
    truncated = False

    def walk(idx: int, depth: int) -> None:
        nonlocal printed, truncated
        if truncated:
            return
        if idx >= len(nodes):
            return
        if printed >= args.max_nodes:
            truncated = True
            return
        node = nodes[idx]
        print(f"{'  ' * depth}- {node_label(idx, node)}")
        printed += 1
        if depth >= args.max_depth:
            return
        for child in node.get("children", []):
            walk(child, depth + 1)

    for root in root_nodes:
        walk(root, 0)
        if truncated:
            break

    if truncated:
        print(
            f"... truncated after {args.max_nodes} nodes (adjust --max-nodes)."
        )


if __name__ == "__main__":
    main()
