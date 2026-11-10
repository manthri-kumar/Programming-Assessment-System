# Backend security model

## Authentication and authorization

Passwords are stored as salted PBKDF2-SHA256 hashes. Access tokens are signed, expire after the configured lifetime, and are rejected when expired or altered. Authorization uses the current role from SQLite rather than trusting the role claim alone. Public student registration is allowed; teacher self-registration requires the server-owned `ASSESSMENT_TEACHER_REGISTRATION_CODE`.

Assignment ownership is the data-isolation boundary. Only the owner can receive or update reference source, hidden tests, and rubric data or inspect and evaluate submissions for that assignment. Students can list, read, evaluate, and retrieve reports only for their own submissions. Teacher analytics cover only owned assignments; student progress covers only the authenticated student.

Production configuration must provide a stable private `ASSESSMENT_SECRET`, protect the teacher invitation code, terminate TLS at a trusted boundary, restrict database-file access, and set an approved retention duration. Account recovery, tenant organizations, invitation rotation, and public-internet deployment hardening are not implemented in this milestone.

## Assessment execution

The API never invokes a student compiler or program directly. It delegates through `SubmissionRunner` and defaults to `FailClosedRunner`. The approved design requires a digest-pinned Linux worker behind a protected control channel. The policy disables network, uses a read-only root, drops capabilities, enables `no-new-privileges`, sets an unprivileged numeric user, bounds CPU/memory/PIDs/scratch, provides no host mounts or devices, and requests cleanup for every opaque job ID.

The mTLS control service retains hidden expected outputs and weights outside the job container. The container-only `worker/entrypoint.py` receives only source, test IDs, and test input; validates the bounded job again; uses fixed Python 3.11, Clang C11, and JDK 17 commands; caps stdout/stderr while streaming; applies compile/test/job deadlines; starts a fresh process group for each command; kills it on timeout or output overflow; and deletes the unique workspace in `finally`. The control service compares raw outcomes with hidden expectations. The container runtime remains responsible for cgroup and filesystem limits.

Unit tests validate policy construction, worker input/command policy, unique IDs, cleanup requests, and fail-closed behavior. They do not prove kernel containment, cgroup enforcement, process-tree cleanup after container failure, or concurrent workspace isolation. Those claims remain blocked until the approved image digest and real worker security suite exist.

## Data and diagnostics

Request sizes, source, tests, and weights are bounded before execution. Logs use correlation IDs and redact passwords, tokens, source, reference source, and process streams. Immutable assessment records retain versions and evidence lineage; retention cleanup redacts source/output fields. API errors expose stable categories and request IDs while unexpected exception details remain server-side.

Hidden tests and reference code never appear in student assignment responses, history, progress, or reports. The generated OpenAPI contains no credentials or local filesystem paths.
