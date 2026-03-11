#!/usr/bin/env bash
set -euo pipefail

# smoketest.bash - Build local app image and run Podman pod to execute Playwright E2E smoke test
# Usage: ./scripts/smoketest.bash [all|build|run|logs|cleanup]
#  all (default): build image and run pod
#  build: build the app image only
#  run: run podman play kube and wait for Playwright test runner
#  logs: show last 200 lines of logs for containers in the pod
#  cleanup: remove pod and containers created by podman play kube

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="cablemodem:local"
POD_FILE="$REPO_ROOT/podman-play.yml"
POD_NAME="cablemodem-e2e"

usage() {
  cat <<'USAGE'
Usage: smoketest.bash [all|build|run|logs|cleanup]
  all     - build image then run pod (default)
  build   - build the app image
  run     - run podman play kube and wait for Playwright tests
  logs    - dump last 200 lines of pod logs
  cleanup - remove pod and containers created by the pod
USAGE
}

build_image() {
  echo "Building image ${IMAGE_NAME} from ${REPO_ROOT}..."
  podman build -t "${IMAGE_NAME}" "${REPO_ROOT}"
}

run_pod() {
  echo "Running Podman pod from ${POD_FILE}..."
  podman play kube "${POD_FILE}"
  # allow containers to start
  sleep 2

  # Try to identify the test runner (playwright/test runner). Look for container with 'playwright' in name or a python image.
  runner=$(podman ps -a --format '{{.ID}} {{.Names}} {{.Image}}' | egrep -i 'playwright|python:3' | awk '{print $1}' | head -n1 || true)

  if [ -n "$runner" ]; then
    echo "Found test runner container: $runner — waiting for it to exit..."
    podman wait "$runner" >/dev/null || true
    rc=$(podman inspect -f '{{.State.ExitCode}}' "$runner" 2>/dev/null || echo 1)
    echo "Playwright exit code: $rc"
    echo "--- Playwright logs (tail 200) ---"
    podman logs --tail=200 "$runner" || true
    exit "$rc"
  else
    echo "Could not identify test runner container. Showing pod logs for '${POD_NAME}':"
    podman ps -a --filter name="${POD_NAME}" -q | xargs -r podman logs --tail=200 || true
  fi
}

show_logs() {
  podman ps -a --filter name="${POD_NAME}" -q | xargs -r podman logs --tail=200 || true
}

cleanup() {
  echo "Stopping and removing pod '${POD_NAME}' and related containers..."
  podman pod rm -f "${POD_NAME}" 2>/dev/null || true
  cids=$(podman ps -a --filter name="${POD_NAME}" -q || true)
  if [ -n "$cids" ]; then
    podman rm -f $cids || true
  fi
}

case "${1:-all}" in
  build) build_image ;;
  run) run_pod ;;
  logs) show_logs ;;
  cleanup) cleanup ;;
  all) build_image; run_pod ;;
  *) usage; exit 2 ;;
esac
