#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="bunlar-cad-converter"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  docker build -t "${IMAGE_NAME}" -f "${WORKSPACE_ROOT}/cad-converter/Dockerfile" "${WORKSPACE_ROOT}"
fi

DOCKER_ARGS=(
  --rm
  -v "${WORKSPACE_ROOT}":/workspace
  -w /app
)
if [[ -n "${CAD_DEBUG:-}" ]]; then
  DOCKER_ARGS+=(-e "CAD_DEBUG=${CAD_DEBUG}")
fi
DOCKER_ARGS+=("${IMAGE_NAME}")

docker run "${DOCKER_ARGS[@]}" "$@"
