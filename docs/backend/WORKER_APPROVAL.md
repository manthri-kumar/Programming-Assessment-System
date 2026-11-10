# Isolated worker approval record

Status: **local architecture and Clang approved; concrete image/trust material not yet verified**.

Real Python, C11, and Java 17 execution stays disabled until every field below has an exact reviewed value. A base-image tag, local Docker availability, or unit tests are insufficient.

## Required approval values

| Decision | Required exact value | Current state |
| --- | --- | --- |
| Linux base image | Registry path plus immutable manifest digest | Official Debian `bookworm-20261005-slim` candidate selected; full digest unresolved and intentionally absent |
| Toolchains in that image | CPython 3.11 patch version, approved C compiler and patch version with C11 support, JDK 17 patch/build, and their package/source provenance | Selected Debian builds: Python `3.11.2-6+deb12u9`, Clang `1:14.0.6-12`, OpenJDK `17.0.21+9-1~deb12u1`; not yet built/observed |
| Final worker image | Project-owned repository plus immutable final image digest | Unbuilt/unverified |
| Registry | Project-owned registry hostname, repository, read identity, retention and immutability policy | Local TLS registry `localhost:5000/assessment/worker` selected; not configured |
| Control plane | Dedicated worker service endpoint and protocol version; API must not receive a Docker/containerd socket | Separate loopback `worker-policy-v1` service over HTTPS selected; implemented, not deployed |
| Authentication | Mutual TLS identities plus a short-lived audience-bound service token, or an equivalently reviewed workload-identity mechanism | Project-owned mTLS CA/server/API identities selected; certificates not generated |
| Authorization | API identity may submit/read/cancel only its own opaque jobs; worker identity may pull only the approved repository/digest | Unselected |
| Network policy | API-to-control-plane allowlist only; job containers use no network | Unverified |
| Runtime policy | Rootless or dedicated container runtime, restrictive seccomp profile, AppArmor/SELinux policy where supported, read-only root, all capabilities dropped, `no-new-privileges`, UID/GID 65532, no host mounts/devices/secrets | Rootless Podman and hash-pinned host seccomp profile selected/encoded; not verified |
| Resource policy | 1 CPU; 256 MiB Python/C; 512 MiB Java with 256 MiB JVM heap; 64 PIDs; 16 MiB scratch; 64 KiB per stdout/stderr; compile 10 s; test 2 s; job 120 s | Encoded; not verified |
| Cleanup evidence | Full container/process-tree termination, unique workspace removal, no stale artifacts, cancellation cleanup and concurrent-job isolation | Unit-level only |
| Audit/retention | Redacted job metadata, image/policy/toolchain versions, cleanup outcome, retention duration and access policy | Duration unapproved |

## Recommended boundary for approval

The intended boundary is a dedicated Linux worker host or VM. The FastAPI service sends a bounded, authenticated `worker-policy-v1` job to a protected control service. That service creates one container from the approved digest, supplies the JSON job through a non-filesystem control channel, applies the server-owned policy, validates the bounded response, force-removes the container, and reports cleanup evidence. The API service has no registry write permission, runtime socket, host path, or ability to select an image, command, mount, limit, or compiler flag.

The registry and identity provider may be local/project-owned or a cloud service, but company infrastructure and credentials are prohibited. The choice must be recorded here and in the OpenSpec review before real-runner acceptance.

## Minimum permissions

- API: invoke worker health/submit/status/cancel for this project; no container-runtime or registry credentials.
- Control service: pull the single approved digest, create/inspect/kill/remove project job containers, and read only project policy; no privileged containers or host mounts.
- Job container: no external identity, credential, network, device, runtime socket, or host filesystem access.
- Reviewer/operator: approve image/policy versions and read redacted evidence; deployment permissions are separate from application users.

## Approval and verification sequence

1. Select and record the base image, digest, registry, control plane, identity mechanism, seccomp/LSM policy, and retention duration.
2. Clang is approved as the authoritative C11 compiler; preserve its exact version in the image labels and evidence.
3. Build the final image from the reviewed Dockerfile; record the immutable digest and SBOM/toolchain versions.
4. Configure the dedicated worker without exposing its runtime socket to FastAPI.
5. Run real fixtures for correct output, compile failure without the word `error`, crash-after-output, infinite loop with descendants, output/memory/PID/scratch exhaustion, filesystem/network attempts, cancellation, overlap, stale artifacts and cleanup.
6. Run the same complete API request twice and verify deterministic decisions and cleanup evidence.
7. Only then mark tasks 3.2-3.4, 8.3, 10.2, 10.3 and the real-worker acceptance tasks complete.
