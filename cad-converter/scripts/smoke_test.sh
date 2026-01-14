#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DEFAULT_INPUT_HOST="${WORKSPACE_ROOT}/cad-converter/samples/input.step"
DEFAULT_OUTPUT_HOST="${WORKSPACE_ROOT}/cad-converter/samples/output.gltf"
DEFAULT_INPUT_CONTAINER="/workspace/cad-converter/samples/input.step"
DEFAULT_OUTPUT_CONTAINER="/workspace/cad-converter/samples/output.gltf"

INPUT_HOST="${DEFAULT_INPUT_HOST}"
OUTPUT_HOST="${DEFAULT_OUTPUT_HOST}"
INPUT_CONTAINER="${DEFAULT_INPUT_CONTAINER}"
OUTPUT_CONTAINER="${DEFAULT_OUTPUT_CONTAINER}"
USER_CFG_HOST=""
USER_CFG_CONTAINER=""
LINEAR_DEFLECTION=""
ANGULAR_DEFLECTION=""

resolve_paths() {
  python3 - "$WORKSPACE_ROOT" "$1" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
value = pathlib.Path(sys.argv[2])
if not value.is_absolute():
    value = (root / value).resolve()
if root not in value.parents and value != root:
    print("OUTSIDE", file=sys.stderr)
    sys.exit(2)
rel = value.relative_to(root).as_posix()
print(str(value))
print(f"/workspace/{rel}")
PY
}

resolve_pair() {
  local value="$1"
  local resolved
  resolved="$(resolve_paths "$value")"
  RESOLVED_HOST="${resolved%%$'\n'*}"
  RESOLVED_CONTAINER="${resolved#*$'\n'}"
  if [[ -z "${RESOLVED_HOST:-}" || -z "${RESOLVED_CONTAINER:-}" ]]; then
    echo "Failed to resolve path: ${value}" >&2
    exit 2
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input)
      if [[ "$2" == /workspace/* ]]; then
        INPUT_CONTAINER="$2"
        INPUT_HOST="${WORKSPACE_ROOT}/${2#/workspace/}"
      else
        resolve_pair "$2"
        INPUT_HOST="${RESOLVED_HOST}"
        INPUT_CONTAINER="${RESOLVED_CONTAINER}"
      fi
      shift 2
      ;;
    --output)
      if [[ "$2" == /workspace/* ]]; then
        OUTPUT_CONTAINER="$2"
        OUTPUT_HOST="${WORKSPACE_ROOT}/${2#/workspace/}"
      else
        resolve_pair "$2"
        OUTPUT_HOST="${RESOLVED_HOST}"
        OUTPUT_CONTAINER="${RESOLVED_CONTAINER}"
      fi
      shift 2
      ;;
    --user-cfg)
      if [[ "$2" == /workspace/* ]]; then
        USER_CFG_CONTAINER="$2"
        USER_CFG_HOST="${WORKSPACE_ROOT}/${2#/workspace/}"
      else
        resolve_pair "$2"
        USER_CFG_HOST="${RESOLVED_HOST}"
        USER_CFG_CONTAINER="${RESOLVED_CONTAINER}"
      fi
      shift 2
      ;;
    --linear-deflection)
      LINEAR_DEFLECTION="$2"
      shift 2
      ;;
    --angular-deflection)
      ANGULAR_DEFLECTION="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
 done

if [[ ! -f "${INPUT_HOST}" ]]; then
  echo "Sample input not found: ${INPUT_HOST}" >&2
  echo "Place a STEP file at cad-converter/samples/input.step" >&2
  echo "or pass --input /path/to/model.step" >&2
  exit 2
fi
if [[ -n "${USER_CFG_HOST}" && ! -f "${USER_CFG_HOST}" ]]; then
  echo "FreeCAD user.cfg not found: ${USER_CFG_HOST}" >&2
  exit 2
fi

OUTPUT_DIR="$(dirname "${OUTPUT_HOST}")"
mkdir -p "${OUTPUT_DIR}"

EXTRA_ARGS=()
if [[ -n "${USER_CFG_CONTAINER}" ]]; then
  EXTRA_ARGS=(--user-cfg "${USER_CFG_CONTAINER}")
fi
if [[ -n "${LINEAR_DEFLECTION}" ]]; then
  EXTRA_ARGS+=(--linear-deflection "${LINEAR_DEFLECTION}")
fi
if [[ -n "${ANGULAR_DEFLECTION}" ]]; then
  EXTRA_ARGS+=(--angular-deflection "${ANGULAR_DEFLECTION}")
fi

bash "${WORKSPACE_ROOT}/cad-converter/scripts/docker_convert.sh" \
  --input "${INPUT_CONTAINER}" \
  --output "${OUTPUT_CONTAINER}" \
  "${EXTRA_ARGS[@]}"

echo "Wrote glTF: ${OUTPUT_HOST}"
