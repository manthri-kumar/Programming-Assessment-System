# Isolated Execution

## Purpose

Contain untrusted reference and student compilation and execution while exposing bounded, reproducible test outcomes.

## ADDED Requirements

### Requirement: Require isolation for all untrusted execution
Compilation and execution of student and reference programs SHALL occur only in the approved unprivileged isolation boundary. It SHALL deny network, host filesystem mounts, host secrets and elevated privileges. Missing isolation SHALL fail closed without direct host fallback.

#### Scenario: Isolation unavailable
- **WHEN** the isolation backend cannot start
- **THEN** assessment reports unavailable infrastructure and launches no compiler or submitted program on the host

#### Scenario: Host resource access attempt
- **WHEN** a program attempts network access, host-file access or privilege escalation
- **THEN** access is denied and the runner records the bounded failure without exposing host data

### Requirement: Protect the local worker control plane
The approved development/demonstration worker SHALL use project-owned rootless Podman behind a separate control service. FastAPI SHALL communicate with that service through a fixed mutually authenticated TLS endpoint and SHALL NOT receive the Podman socket, registry write credentials, or client-selected image/command/mount/limit controls. The service SHALL refuse jobs until the configured image includes a valid immutable digest and its observed toolchain manifest matches the approved policy.

#### Scenario: Missing local-worker trust material
- **GIVEN** the client certificate, trusted CA, immutable image digest, or inspected toolchain manifest is absent or mismatched
- **WHEN** FastAPI checks readiness or submits a job
- **THEN** the worker is unavailable and no container or host process is started

#### Scenario: Unauthenticated control request
- **GIVEN** a caller without a certificate signed by the project worker CA
- **WHEN** it connects to the control service
- **THEN** the TLS handshake or authorization check rejects the request before job parsing

### Requirement: Enforce server-owned resource limits
The runner SHALL bound compilation to 10 seconds, each test to 2 seconds and a job to 120 seconds; stdout/stderr to 64 KiB each; scratch to 16 MiB; processes to 64; memory to 256 MiB for C/Python and 512 MiB for Java. Client submissions SHALL NOT override these limits.

#### Scenario: Infinite loop and child process
- **WHEN** a test exceeds its deadline while descendants exist
- **THEN** the runner reports timeout, terminates the full process tree and releases the workspace

#### Scenario: Output or memory flood
- **WHEN** a submission exceeds output, memory, process or scratch limits
- **THEN** the runner stops it with a distinct resource outcome and bounded diagnostics

#### Scenario: Compilation hang
- **WHEN** compilation exceeds its deadline
- **THEN** compilation is terminated and tests are not started from stale artifacts

### Requirement: Report weighted test outcomes accurately
Each test SHALL record status, bounded stdout/stderr, exit code when available, and configured weight. Passing SHALL require successful exit and matching expected stdout under the documented outer-whitespace normalization; matching stdout with a crash SHALL fail.

#### Scenario: Correct output then crash
- **WHEN** stdout matches but execution exits nonzero
- **THEN** the case fails with runtime_error and contributes no passed weight

#### Scenario: Whitespace comparison
- **WHEN** actual and expected output differ only in leading or trailing whitespace
- **THEN** the case passes if execution succeeds, while differing internal whitespace remains a mismatch

### Requirement: Isolate jobs and clean every outcome
Each assessment SHALL have a unique workspace and artifacts. Cleanup SHALL run after success, failure, cancellation and timeout. Concurrent requests SHALL NOT read or execute another job's outputs.

#### Scenario: Repeated or overlapping jobs
- **WHEN** jobs submit different sources, including one compilation failure
- **THEN** each uses only its own artifacts, no failed job runs a previous executable, and all workspaces are removed

## Inputs and outputs
Inputs are bounded source and tests; outputs are isolated per-case outcomes, bounded streams and cleanup evidence.

## Expected behavior
All untrusted compilation and execution occurs only in the approved worker, or fails closed.

## Edge cases and failure handling
Worker absence, daemon failure and cleanup failure are infrastructure outcomes; host execution is forbidden.

## Acceptance criteria
Fake runner tests pass locally; real containment tests pass only with a verified pinned Linux worker.

## Dependencies
Depends on `test-execution-agent`, `observability`, `backend-architecture`.
