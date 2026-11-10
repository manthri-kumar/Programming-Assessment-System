# Tasks

## 1. Contract Characterization

- [x] 1.1 Add an API regression test proving the existing default teacher-form payload returns HTTP 201 and persists the owning teacher; verify with the focused backend test command.
- [x] 1.2 Add API validation tests for missing title, unsupported language, invalid rubric totals, malformed or duplicate tests, blank reference source, unknown concepts, unauthenticated access, and student access; verify exact status codes and safe response details.
- [x] 1.3 Add response-contract tests proving students cannot receive hidden test data or reference source while the owner can reload the created assignment; verify the focused backend tests pass.

## 2. Frontend Validation and Error Handling

- [x] 2.1 Load allowed assignment concepts from the existing concept-graph API and replace unchecked concept text submission with graph-backed validation; verify component tests cover loading, selection, stale concepts, and graph-load failure.
- [x] 2.2 Implement schema-aligned form validation for required fields, supported language, nonblank reference source, rubric weights, test identifiers and weights, byte limits, and timezone-aware deadline serialization; verify invalid forms do not issue a creation request.
- [x] 2.3 Implement safe assignment-specific normalization of FastAPI 422 details and domain errors into accessible field messages plus a summary; verify tests cover unknown concepts, duplicate tests, authorization, connectivity, and unexpected failures without exposing raw internals.
- [x] 2.4 Add a frontend contract test that submits the real form defaults, captures the JSON request, and proves it matches the backend assignment schema; verify the frontend test suite passes.

## 3. Persistence and Workflow Integration

- [x] 3.1 Add integration coverage proving a created assignment survives repository reload and remains owned and editable only by its creator; verify the focused persistence and authorization tests pass.
- [x] 3.2 Add integration coverage proving an available assignment appears in the student list and opens in the coding workspace without hidden tests or reference source; verify the focused API/frontend tests pass.
- [x] 3.3 Exercise a student submission through `ImplementationEvaluationAgent` followed by `FeedbackAgent`, persist the assessment report, and verify the report remains accessible with an explicit execution-unavailable limitation when no approved isolated runner exists.

## 4. Browser and Regression Verification

- [x] 4.1 Update the browser test to log in as a teacher, create an assignment through the actual form, and verify the successful teacher view; verify the Playwright scenario passes against local frontend and backend services.
- [x] 4.2 Extend the browser scenario to log in as a student, find and open the assignment, submit supported source, and view the persisted report; verify no hidden-test data appears and any secure-runner limitation is reported honestly.
- [x] 4.3 Run backend tests, frontend tests, TypeScript checks, linting, the production frontend build, and strict OpenSpec validation; record actual pass/fail/blocked results without claiming secure execution evidence that was not produced.

### Verification evidence (2026-11-07)

- Backend: `.venv\Scripts\python.exe -m pytest -q` — 110 passed, 0 failed.
- Frontend: `npm test -- --run --reporter=verbose` — 42 passed, 0 failed.
- TypeScript/lint/build: `npm run typecheck`, `npm run lint`, and `npm run build` — all passed.
- Browser: `npm run test:e2e` with the local fail-closed API — 15 passed across desktop, tablet, and mobile.
- OpenSpec: strict validation passed.
- Secure execution remained unavailable and fail-closed; no student source was executed on the application host and no functional-test evidence was fabricated.

## Workflow follow-up

- Archive the change only after implementation review and all acceptance criteria that do not require unavailable secure-runner infrastructure are satisfied.
