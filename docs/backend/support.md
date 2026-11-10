# Backend support matrix

This document records the approved initial backend boundary for `backend-core-audit`.

| Language | Supported input | Toolchain boundary | Current status |
| --- | --- | --- | --- |
| Python | Python 3.11 standard-library, one source file | CPython AST parsing; execution requires worker | static analysis available; execution blocked |
| C | C11, one translation unit, standard headers | tree-sitter-c parsing; authoritative Clang 14.0.6 candidate inside the isolated Linux worker | static analysis available; real compiler/execution verification blocked |
| Java | Java 17, one `Main.java`, class `Main`, standard library | tree-sitter-java parsing; JDK inside the isolated Linux worker | static analysis available; execution blocked |

All student and reference compilation/execution must happen in an unprivileged Linux isolation worker with network disabled, no host mounts/secrets, server-owned resource limits, and full process-tree cleanup. The approved local design uses rootless Podman behind a separate project-owned mTLS control service, but no digest-pinned image is configured. Docker Desktop or daemon availability is not acceptance evidence and was not probed during the current verification; the backend fails closed and does not run submissions on the host.

The preserved rubric is `legacy-v1` characterization plus `core-v1`: structure 0.20, syntax 0.40, tests 0.20, originality heuristic 0.20; Good >=75 and Average >=50. Missing required evidence produces an incomplete result with no total. Text similarity is not a misconduct verdict.

The existing zero-divisor teacher behavior is the documented candidate label: input `5 0` produces `5\n5\n0\nError\n`. The previous `Error\n`-only fixture conflicts with the teacher source and must not be silently reused. Independent label review remains pending, so this correction is not published as benchmark ground truth.

The initial local API now enforces teacher/student roles with short-lived signed bearer tokens and PBKDF2 password hashes. Public multi-tenant hosting and account recovery remain out of scope. Frontend functionality, external LLM APIs, multi-file projects, external packages, arbitrary compiler flags, and universal grading claims are out of scope.
