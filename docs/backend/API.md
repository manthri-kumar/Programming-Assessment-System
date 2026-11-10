# Backend API contract

The generated OpenAPI 3.1 contract is [`openapi.json`](openapi.json). Regenerate it with:

```powershell
.venv\Scripts\python.exe -m scripts.export_openapi
```

API version `0.2.x` adds the authenticated academic workflow. Additive response fields are permitted within the line. Removing or renaming fields, changing status meanings, or accepting a new rubric policy requires a reviewed API version change.

All protected routes use `Authorization: Bearer <token>`. The initial roles are `teacher` and `student`. Student registration is public. Teacher registration requires the server-owned `ASSESSMENT_TEACHER_REGISTRATION_CODE` in `teacher_registration_code`; if it is not configured, teacher registration fails closed. This initial environment-owned invitation is reusable and has no expiry or single-use lifecycle; the application does not simulate expired or consumed invitations. Only an assignment's owning teacher can read or change its reference source, hidden tests, and rubric or inspect its submissions. Students create and view only their own submissions.

## Academic workflow

1. `POST /auth/register` and `POST /auth/login` create a user and issue an expiring signed bearer token.
2. A teacher creates an assignment with `POST /assignments`. `rubric.weights` may override the four `core-v1` weights when they are finite, nonnegative, complete, and sum to one.
3. The owning teacher updates the assignment, rubric, reference, or tests with `PATCH /assignments/{id}`.
4. A student submits with `POST /submissions`; either the student owner or assignment owner invokes `POST /submissions/{id}/evaluate`.
5. Role-scoped history is available at `GET /submissions`; a persisted report is read at `GET /submissions/{id}/evaluation`.
6. `GET /teacher/analytics` returns aggregates for owned assignments. `GET /student/progress` returns aggregates for the authenticated student. Null totals are excluded from averages but retained in status counts.

## Frontend support contracts

- `GET /concept-graph` returns authenticated client-safe nodes and typed prerequisite edges from the validated graph.
- Assignment create/update contracts accept bounded `requirements`, `input_notes`, `output_notes`, `examples`, `constraints`, `concept_ids`, and a timezone-aware optional `deadline`. Student responses omit reference source, hidden tests, and rubric internals.
- `GET /bookmarks` and idempotent `PUT|DELETE /bookmarks/{assignment_id}` persist student-scoped bookmarks.
- `GET|PUT|DELETE /assignments/{assignment_id}/draft` persists one bounded, student-scoped draft without compilation or execution.
- `GET /student/activity` returns persisted submission, evaluation, draft, and bookmark events. Empty histories return an empty list; sample events are never generated at read time.

Teacher assignment lists are owner-scoped. Student lists expose all currently accessible assignments while preserving hidden fields. All new routes retain bearer authentication, bounded pagination, stable errors, and SQLite transactions.

List pagination uses `limit` (1–100) and nonnegative `offset`. History lists omit source; the authorized single-submission route returns it. No student response includes reference code or hidden tests.

## Direct assessment example

```http
POST /assessments
Authorization: Bearer <token>
Content-Type: application/json

{
  "language": "python",
  "source": "print(1)",
  "reference_source": "print(1)",
  "policy_version": "core-v1",
  "tests": [
    {
      "id": "case-1",
      "input": "",
      "expected_output": "1\n",
      "weight": 1,
      "concept_ids": ["input"]
    }
  ]
}
```

A learner syntax error returns HTTP 200 with `status: invalid_submission` and a null total. Missing isolated execution returns HTTP 503 with the incomplete result under `detail`. Invalid or oversized fields, duplicate test IDs, and unknown concepts return HTTP 422 before execution. An authenticated fake-runner contract test covers a complete HTTP 200 result and rubric arithmetic; it does not execute source code.

The response `agents` array and `agent_trace` contain exactly two top-level agents in order: `implementation-evaluation`, then `feedback`. The `analysis` object contains internal service entries for preprocessing, syntax, concepts, structure, complexity, and secure execution. Graph reasoning, `feedback`, `recommendations`, and the complete `assessment-report-v2` remain available without exposing their internal services as agents. A successful or incomplete assessment is stored as an immutable, content-hash-keyed SQLite assessment record and returns `assessment_record_id` and `request_hash`. Repeating an identical request reuses that replay record.

`GET /health` reports process liveness. `GET /ready` reports graph and runner readiness and returns 503 until the approved Linux worker is available. The API never falls back to host execution.

To opt into the approved local worker, set `ASSESSMENT_WORKER_CONFIG` to an absolute path containing a private `worker-client-v1` configuration derived from `worker/client.example.json`. The configured endpoint must be HTTPS, certificate paths must be absolute, and the image must include a verified immutable digest. Missing/invalid configuration or failed mTLS/toolchain readiness remains a 503 fail-closed state.

The OpenAPI artifact contains no filesystem paths or credentials. Source is capped at 64 KiB UTF-8 per source field, tests at 50, and test input/output at 64 KiB each. Middleware rejects a declared body larger than 8 MiB; production deployment must also enforce the same limit for streaming/chunked requests at the trusted ingress.
