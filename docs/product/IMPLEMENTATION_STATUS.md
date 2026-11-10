# CodeAssess implementation status

Evidence date: 2026-11-09  
Active delivery changes: `complete-codeassess-university-readiness`, `add-ai-assignment-import`

This ledger distinguishes code presence from verified behavior. A specification or checked task is not itself runtime evidence.

## Current verification

| Area | Status | Current evidence | Remaining gate |
| --- | --- | --- | --- |
| Two-agent architecture | VERIFIED | `ImplementationEvaluationAgent` followed by `FeedbackAgent`; backend regression suite passes. | Real isolated execution evidence is still required for full backend acceptance. |
| Backend/API/SQLite | VERIFIED for environment-independent behavior | 138 backend tests passed on 2026-11-09; compilation and dependency checks passed. | Worker-backed compilation/execution, clean-environment acceptance, and measured recovery/load gates. |
| Frontend | VERIFIED for report-v3/import browser behavior | 44 Vitest tests, TypeScript, ESLint, production build, and 18 Playwright scenarios passed on 2026-11-09. | Mandatory real-worker and real-OCR acceptance remain blocked. |
| Assignment document import | PARTIALLY VERIFIED | Secure local image/PDF ingestion, embedded PDF text, provenance, review, canonical confirmation, and responsive browser workflow pass. | Real OCR/handwriting provider evaluation and independent labels are blocked. |
| Static Python/C/Java assessment | PARTIALLY VERIFIED | Parser, normalized IR, deterministic service, scoring, and orchestration tests pass. | Authoritative C11/Java 17 compiler evidence requires the isolated worker. |
| Secure execution | BLOCKED | Fail-closed adapter, worker entrypoint, mTLS configuration, and policy tests exist. | No approved worker image digest, built worker, or real containment run has been observed. |
| Knowledge Graph and recommendations | VERIFIED for defined static fixtures | Graph integrity, deterministic traversal, recommendations, and two-agent handoff tests pass. | Independently reviewed benchmark outcomes remain blocked. |
| Accuracy/research claims | BLOCKED | Candidate corpus and arithmetic tests exist. | Labels are pending independent review; no project accuracy is published. |
| University/institution features | PARTIALLY VERIFIED / FEATURE-GATED | Migration-safe institution, course, cohort, enrollment, teacher, availability, and default-local-scope persistence exists. | Cross-tenant enforcement, management APIs, grade review, analytics, and measured concurrency remain open. |
| Assessment report v3 | VERIFIED for environment-independent behavior | Typed evidence and feedback, additive v3 composition, v2 replay compatibility, persistence, audience redaction, responsive UI, and API/browser tests pass. | Real execution evidence must still be produced by an approved worker. |

## OpenSpec ledger reconciliation

| Change | Verified checklist | Status |
| --- | ---: | --- |
| `fix-assignment-creation-validation` | 13/13 | Completed and covered by current regression suites. |
| `fix-registration-error-reporting` | 8/8 | Completed and covered by current regression suites. |
| `implement-codeassess-frontend` | 41/41 | Completed for its approved scope; later report-v3 work is additive. |
| `backend-core-audit` | 55/69 | Fourteen tasks remain owned by this ledger and are not claimed complete here. |
| `complete-codeassess-university-readiness` | 29/47 | Environment-independent implementation verified; 18 tasks remain open, including all mandatory real-worker and independent-review gates. |
| `add-ai-assignment-import` | In progress | Local-first implementation is verified for embedded PDF text and deterministic adapter contracts; real provider evidence gates remain open. |

The inherited 14 open `backend-core-audit` tasks are `2.3`, `3.2`, `3.3`, `3.4`, `8.3`, `9.3`, `9.4`, `9.5`, `10.2`, `10.3`, `14.2`, `14.3`, `14.4`, and `14.5`. They cover independent review, a real isolated worker and compiler authority, a real isolated API example, held-out metrics, clean-environment verification, and final acceptance. They remain in that ledger; this change may supply evidence but must not duplicate a completion claim.

## Fresh baseline commands

```text
.venv\Scripts\python.exe -m pytest -q
110 passed in 9.84s

cd frontend && npm test -- --run
42 passed (8 files)

cd frontend && npm run typecheck
exit 0

cd frontend && npm run lint
exit 0

cd frontend && npm run build
exit 0 (1966 modules; built in 8.88s)

node <cached @fission-ai/openspec 1.14.1>/bin/openspec.js validate --all --strict
5 changes passed, 0 failed
```

The first sandboxed baseline attempt stalled after 29 tests because Windows localhost socket tests could not complete in the restricted sandbox. It was interrupted and is not counted. The historical 110-test baseline came from the approved non-sandboxed invocation; the current 127-test result below supersedes it.

## Current implementation verification

```text
.venv\Scripts\python.exe -m pytest -q
127 passed in 17.13s

.venv\Scripts\python.exe -m compileall -q backend tests
exit 0

.venv\Scripts\python.exe -m pip check
No broken requirements found

cd frontend && npm test -- --run
43 passed (8 files)

cd frontend && npm run typecheck
exit 0

cd frontend && npm run lint
exit 0

cd frontend && npm run build
exit 0

cd frontend && npx playwright test
15 passed in 1.1m using installed system Chrome and a disposable API/database

npm audit --offline
0 vulnerabilities

openspec validate --all --strict
5 changes passed, 0 failed

git diff --check
exit 0
```

The older baseline block is retained as historical before-change evidence. Current results are 138 backend, 44 frontend, and 18 browser tests. Backend and pilot readiness remain **BLOCKED**, because WSL2 lacks the approved rootless Podman/Clang/Java worker dependencies, no real OCR provider is provisioned, and candidate corpora have not received qualified independent review.

