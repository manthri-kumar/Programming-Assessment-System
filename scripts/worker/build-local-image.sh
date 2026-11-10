#!/usr/bin/env bash
set -euo pipefail

: "${BASE_IMAGE:?Set BASE_IMAGE to an immutable registry reference ending in @sha256:<64 hex>}"
: "${DEBIAN_SNAPSHOT:?Set DEBIAN_SNAPSHOT to a verified snapshot timestamp such as YYYYMMDDTHHMMSSZ}"
: "${DEBIAN_SECURITY_SNAPSHOT:?Set DEBIAN_SECURITY_SNAPSHOT to a verified security snapshot timestamp}"

case "$BASE_IMAGE" in
  *@sha256:????????????????????????????????????????????????????????????????) ;;
  *) printf 'BASE_IMAGE must contain a full sha256 digest\n' >&2; exit 1 ;;
esac

command -v podman >/dev/null || { printf 'rootless Podman is required on the Linux worker\n' >&2; exit 1; }
test "$(id -u)" -ne 0 || { printf 'Do not build or run the worker as root\n' >&2; exit 1; }

image="${WORKER_IMAGE:-localhost:5000/assessment/worker:local}"
podman build --pull=never --no-cache \
  --build-arg "BASE_IMAGE=$BASE_IMAGE" \
  --build-arg "DEBIAN_SNAPSHOT=$DEBIAN_SNAPSHOT" \
  --build-arg "DEBIAN_SECURITY_SNAPSHOT=$DEBIAN_SECURITY_SNAPSHOT" \
  --tag "$image" --file worker/Dockerfile .

podman run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges \
  --user 65532:65532 --entrypoint /bin/sh "$image" -c \
  'python3.11 --version && clang-14 --version | head -n 1 && javac -version && cat /opt/assessment-worker/toolchains.json'

printf 'Built %s. Push it to the project-owned TLS registry, then record the registry manifest digest; a local image ID is not acceptance evidence.\n' "$image"
