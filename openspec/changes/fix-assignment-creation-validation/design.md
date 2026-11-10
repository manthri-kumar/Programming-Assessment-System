# Design

## Context

See `proposal.md` for motivation. The backend already has an authoritative Pydantic request model and graph-membership checks. The current teacher form serializes most fields correctly, but permits unchecked concept text and exposes only a generic API error message. Existing browser coverage bypasses the form by creating assignments through direct API calls.

The design must preserve the endpoint, teacher ownership, hidden-test filtering, authentication, authorization, SQLite persistence, and the exactly-two-agent assessment workflow.

## Goals / Non-Goals

**Goals:**

- Make valid creation through the real teacher form reliable and contract-compatible.
- Prevent predictable invalid submissions and map authoritative backend failures to fields.
- Verify persistence and teacher/student visibility through unit, API, and browser tests.
- Keep server validation authoritative and backward compatible.

**Non-Goals:**

- Redesigning the teacher UI or changing its black-and-yellow theme.
- Relaxing backend validation or exposing hidden tests/reference solutions.
- Changing scoring, agent responsibilities, secure execution, or frontend features unrelated to assignment authoring.
- Claiming functional execution evidence when the isolated worker is unavailable.

## Decisions

### 1. Preserve the existing backend request shape

The frontend request builder will continue using the current `AssignmentCreate` shape. The backend contract is already capable of accepting the default form payload, so changing field names or adding a parallel endpoint would unnecessarily break clients.

Alternative considered: loosen backend validation. Rejected because unknown concepts, malformed tests, and rubric errors would corrupt assessment configuration rather than repair integration.

### 2. Use the Knowledge Graph endpoint as the concept source

The form will load the backend's public concept graph and validate/select identifiers from that result. The backend will still repeat graph-membership validation to handle stale UI state and direct callers.

Alternative considered: hardcode the current six identifiers in the frontend. Rejected because graph versions can evolve and duplicate allowlists drift.

### 3. Add assignment-specific error normalization

The frontend will normalize `ApiError.detail` for assignment creation. FastAPI validation arrays will map `loc` paths to form controls; domain errors such as `unknown_concepts` will map to the concepts control. Only allowlisted, user-actionable text will render. Raw objects, stack traces, credentials, hidden-test values, and server internals will not render.

Alternative considered: globally replace every API error message. Rejected as a broader behavior change with regression risk outside assignment creation.

### 4. Validate twice without duplicating dynamic policy

Static form constraints (required values, supported enums, finite/positive weights, unique test IDs, byte limits, rubric total, valid date serialization) will be checked before submission for fast feedback. Dynamic policy (authorization, ownership, graph membership, persistence invariants) remains authoritative on the server.

### 5. Test the actual UI boundary

Component tests will inspect the emitted payload and error rendering. API tests will cover validation, authorization, persistence, and filtering. Browser tests will create through the teacher form, verify teacher and student views, submit source, and inspect the persisted report. The report may correctly state execution unavailable; no simulated execution evidence will be introduced.

## Risks / Trade-offs

- [Concept graph cannot be loaded] → Disable final submission of concept-dependent data, retain entered values, and show a retryable load error rather than accepting unchecked identifiers.
- [Backend validation format evolves] → Use a defensive detail parser with a safe generic fallback and contract tests for supported formats.
- [Client validation diverges from Pydantic] → Keep server validation authoritative and add shared request examples/contract tests; do not infer authorization or dynamic graph policy in the client.
- [End-to-end test lacks an isolated runner] → Assert the explicit execution-unavailable limitation while still verifying both agents, report persistence, and frontend access.

## Migration Plan

No database migration or endpoint version change is required. Implement the focused frontend behavior, add regression tests, and run the existing backend/frontend suites. Rollback consists of reverting the form and error-normalization changes; persisted assignments remain compatible.
