# Security and privacy review

Evidence date: 2026-11-10

## Verified by code and automated tests

- Authentication tokens, teacher invitation controls, assignment ownership, submission ownership, and report ownership are enforced by API tests.
- Operator access is server-provisioned through `CODEASSESS_OPERATOR_KEY`; it cannot be registered through public authentication. The endpoint returns only worker readiness category, graph version/readiness, and aggregate job states.
- Submission configuration snapshots are never included in student or teacher submission responses. A regression found and fixed an initial snapshot-field disclosure before this feature was marked complete.
- `teacher_explanation` is retained in persisted report v3 but removed from student API responses; owning teachers can read it and unrelated teachers remain denied.
- Hidden test inputs, expected outputs, reference source, credentials, host paths, and worker secrets are absent from operational status. Existing worker protocol tests keep hidden expectations outside the job container.
- Authentication, submission, and evaluation routes have configurable role/identity-aware fixed-window limits with bounded `Retry-After` metadata. Rate limiting occurs after protected-route authentication and does not grant access.
- SQLite jobs use stable IDs, leases, bounded infrastructure retry, cancellation, and canonical record linkage. Learner outcomes are completed rather than retried.
- Application retention redacts expired source and bounded execution output. SQLite backup/restore uses online backup plus integrity checks and refuses overwrite destinations.
- Audit serialization redacts password, hash, token, authorization, source, reference source, stdout, and stderr keys.
- Assignment imports require teacher authentication and owner scope; validate type, extension, magic signature, decoder/parser result, bytes, dimensions, pixels, pages, encryption, and active PDF features; use random path-confined private storage; enforce import/extraction rate limits and idempotency; and remove sources on deletion/expiry. PDFs are attachment-only and images use authenticated no-store/nosniff previews.
- Document content is never treated as an instruction or given assessment-worker/tool access. External OCR is absent; the local Tesseract-compatible adapter is disabled without an explicitly configured absolute executable.

## Real-worker verification: BLOCKED

WSL2 Ubuntu was observed on 2026-11-08 with a non-root user and Linux kernel `6.6.87.2-microsoft-standard-WSL2`. `podman`, `clang`, and `java` were not installed; only `/usr/bin/python3` was found. No package installation or host-security change was authorized. Therefore image provenance, mTLS transport, seccomp/cgroup/network/filesystem isolation, compiler versions, process cleanup, and real resource enforcement remain **BLOCKED**, not verified.

## Dependency and operational evidence

- `python -m pip check`: no broken requirements.
- `npm audit --offline`: 0 known vulnerabilities in the installed lockfile data.
- Backend regression suite: 222 passed.
- Frontend component suite: 61 passed; TypeScript, ESLint, and production build passed.
- Browser suite: 21 passed against a disposable local API/database using system Chrome.
- Strict OpenSpec validation: 6 changes passed, 0 failed.

These checks do not prove container containment. Fake-runner tests prove deterministic application behavior only and are not real worker evidence.

## Unresolved risks

- A server operator key must be provisioned through a protected secret mechanism and rotated operationally; it is deliberately absent by default.
- SQLite is appropriate for the current local milestone, but measured institutional concurrency thresholds are pending.
- Backup files contain sensitive academic records and must inherit restrictive filesystem permissions and encrypted storage controls outside the application.
- Real execution and independent benchmark review are mandatory before backend/pilot readiness can be PASS.

