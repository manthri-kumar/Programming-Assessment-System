# Project-owned local Linux worker

Status: configuration and code are prepared; no real execution evidence exists yet.

## Selected architecture

The academic/development deployment uses a dedicated non-root Linux account, rootless Podman, a project-owned TLS registry at `localhost:5000`, and the separate `worker/control_service.py`. FastAPI receives only a mutually authenticated HTTPS client identity. It does not receive the Podman socket, registry write credentials, host paths, or controls for images, commands, mounts, limits, or compiler flags.

The control service binds to Linux loopback, requires a client certificate signed by the project worker CA, verifies the configured immutable image reference and toolchain labels, and invokes one fixed rootless Podman command. The container has no network, a read-only root, all capabilities dropped, `no-new-privileges`, an approved hash-pinned seccomp profile, UID/GID 65532, no mounts/devices/secrets, 1 CPU, bounded memory/PIDs/tmpfs, and a unique opaque name. Cleanup force-removes the container after every outcome and is idempotent.

Hidden expected outputs and weights terminate at the control service. Only source, case IDs, and test input enter the job container. The container returns raw bounded output/status; the control service compares it with hidden expectations before returning a validated response to FastAPI.

## Selected toolchain candidates

The selected Debian amd64 package builds are CPython `3.11.2-6+deb12u9`, Clang `1:14.0.6-12` (upstream 14.0.6), and OpenJDK `17.0.21+9-1~deb12u1`. Their official Debian package URLs and review date are recorded in `worker/toolchain-policy.json`. They are selected, not yet observed in a built image. `worker/Dockerfile` installs exact versions from explicit Debian and Debian-security snapshot timestamps and fails if the resolved versions differ.

The candidate base is the official `docker.io/library/debian:bookworm-20261005-slim` tag. Its full multi-architecture/amd64 digest has not been recorded because it was not resolved from the worker registry in this session. The Dockerfile therefore has no default base and cannot build until `BASE_IMAGE` contains a full verified `@sha256:` reference.

## Reproducible setup sequence

Run these steps only on the dedicated Linux worker, never as root and never on the Windows application host:

1. Install rootless Podman, OpenSSL, and a project-owned TLS registry using the operating system's trusted administration process. Record their versions. Do not expose the Podman socket over TCP.
2. Resolve the official base image manifest for `linux/amd64`, record its full digest in a local copy of `worker/toolchain-policy.json`, and choose Debian snapshot timestamps that contain every selected package version.
3. Generate local development certificates with `scripts/worker/generate-dev-certs.sh`. Keep the CA and private keys under `.local/worker/` or the worker account's private configuration directory; never commit them.
4. Build with `scripts/worker/build-local-image.sh`. The script requires the immutable base reference and snapshot timestamps, runs as non-root, uses no mutable base pull, and prints observed toolchain versions.
5. Push the final image to the TLS-protected project registry. Inspect the registry manifest, record its full digest, and copy `worker/control.example.json` and `worker/client.example.json` to ignored `*.actual.json` files with the digest, certificate paths, and SHA-256 of the installed seccomp profile.
6. Start `worker/control_service.py --config <control.actual.json>` under the dedicated non-root worker account. Run FastAPI under a different account without membership/access to the Podman socket.
7. Run `scripts/worker/verify-local-worker.py --config <client.actual.json>`. Preserve its JSON result with the image, policy, seccomp and toolchain manifests.

The verification command checks real Python/C/Java echo programs, compile failures, crash-after-matching-output, outer/internal whitespace behavior, timeout with descendants, output/memory/PID/scratch exhaustion, network/host-file denial, concurrent jobs, protocol cancellation, and repeated cleanup. It exits nonzero on any mismatch. Unit tests only verify that this mandatory case inventory remains present; they are not substitutes for running it against the approved worker.

## Unverified controls

No image was built or pulled, no local registry or control service was started, no certificate was generated, and no student source was executed in this session. Kernel containment, cgroup classification, process-tree termination, scratch/PID exhaustion, concurrent isolation, and cleanup therefore remain unverified. The checked-in examples contain invalid digest placeholders and fail closed.

## Local verification on 2026-11-10

Read-only WSL inspection found an Ubuntu WSL2 distribution, kernel `6.6.87.2-microsoft-standard-WSL2`, running as UID 1000. `/usr/bin/python3` and `/usr/bin/openssl` exist; `podman`, `clang-14`, and `javac` are absent. No packages, certificates, images, registry, or host-security changes were installed/applied. Real Python 3.11, C11, and Java 17 worker execution is **BLOCKED**.

The control/entrypoint implementation was corrected to keep container stdin attached, transfer input without blocking the deadline, bound control response capture while streaming, kill the process group even after its parent exits, close capture descriptors, preserve the dedicated Podman account's runtime environment, require rootless cgroup-v2 CPU/memory/PID controls, and reject grading evidence when cleanup fails or a successful case lacks a zero exit code. The UTF-8 sanitizer cannot expand captured streams beyond the configured byte bound.

Environment-independent verification: `python -m pytest tests/test_worker_protocol.py tests/test_local_worker_control.py tests/test_container_runner_contract.py tests/test_worker_configuration.py -q` passed **45 tests**. Process adapters are intercepted in these tests; they establish contract behavior, not real containment. The real verifier now also includes full-size unread stdin and a child whose parent exits before the child. Resource classification, kernel isolation, certificate identity authorization, and all real execution gates remain unverified until the approved runtime and immutable image exist.

Next provisioning action requires separate administrator approval for trusted Ubuntu rootless-Podman dependencies and a dedicated worker account/registry. After provisioning, resolve and record the base digest and snapshot timestamps, build the image with the existing script, record its registry digest, prepare private mTLS material and hash-pinned seccomp configuration, and run `python scripts/worker/verify-local-worker.py --config .local/worker/client.actual.json`. Keep `ASSESSMENT_WORKER_CONFIG` unset until this configuration is reviewed and real verification passes.
