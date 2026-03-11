#!/usr/bin/env bash
set -euo pipefail
if [ $# -lt 1 ]; then
  echo "Usage: $0 <path-to-coverage-html-directory> [port]"
  exit 2
fi
COV_DIR="$1"
PORT="${2:-8000}"
if [ ! -d "$COV_DIR" ]; then
  echo "Coverage directory not found: $COV_DIR"
  exit 1
fi
# Try Docker, then Podman, then local python server
if command -v docker >/dev/null 2>&1; then
  docker run --rm -p "${PORT}:${PORT}" -v "$(realpath "${COV_DIR}")":/srv -w /srv python:3.11-slim python -m http.server "${PORT}"
elif command -v podman >/dev/null 2>&1; then
  podman run --rm -p "${PORT}:${PORT}" -v "$(realpath "${COV_DIR}")":/srv -w /srv docker.io/library/python:3.11-slim python -m http.server "${PORT}"
else
  echo "Docker/Podman not found; serving locally with python -m http.server"
  (cd "${COV_DIR}" && python -m http.server "${PORT}")
fi
