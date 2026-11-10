# Backend final results

Date: 2026-11-10
OpenSpec change: `backend-core-audit`  
State: implementation in progress; backend acceptance is not established.

## Progress

The task ledger contains **69 tasks**. **55 are verified complete and 14 remain open** after completing the all-specification scenario matrix.

## Implemented architecture

Exactly two top-level agents are registered and orchestrated:

1. `ImplementationEvaluationAgent` coordinates code preprocessing, Python/C/Java static syntax analysis, concept detection, normalized structural comparison, complexity analysis, secure runner delegation, rubric scoring, evidence, and limitations. It returns one typed `ImplementationEvaluationResult`.
2. `FeedbackAgent` consumes that exact result and coordinates error explanations, strengths/weaknesses, Knowledge Graph reasoning, prerequisites, learning recommendations, feedback, and final `assessment-report-v2` composition. It returns one typed `FeedbackResult`.

The old agent-named capabilities remain as internal services. They do not satisfy `BaseAgent`, do not appear in `registered_agents()`, and do not emit top-level `agent_complete` events. Internal results remain inspectable through report stages and API analysis fields.

The backend also includes bounded request models, invitation-gated teacher registration, role and assignment-ownership authorization, assignment/rubric/test management, submission/report histories, teacher analytics, student progress, SQLite transactions and immutable replay records, correlation-aware redacted logging, a guarded CLI, generated OpenAPI, versioned concept data, benchmark loaders and metric calculation.

## API behavior

`POST /assessments` invokes Agent 1 and then Agent 2. Its `agents` array and `agent_trace` expose exactly `implementation-evaluation` and `feedback`. The `analysis` object exposes typed internal service evidence without presenting those services as agents. Existing `assessment-report-v2` fields for stages, evaluation, graph reasoning, feedback, recommendations, versions, evidence lineage and limitations are retained.

Only the owning teacher may evaluate an assignment's submissions or view/change its protected reference, tests, and rubric. Students may create and view only their own submissions. Valid custom `core-v1` weights reach Agent 1 and are returned with score evidence. Role-scoped history, analytics, and progress derive from persisted evaluations; incomplete totals remain null and do not enter averages. Invalid/oversized inputs return stable validation errors. Learner syntax errors remain assessment results. Missing secure execution returns an infrastructure-unavailable response and a report with null total/category.

## Knowledge Graph verification

Automated coverage verifies graph versioning, duplicate/dangling/cyclic rejection, deterministic prerequisite ordering and paths, shared-ancestor deduplication, satisfied-prerequisite omission, unknown mastery, contradictory pass/fail evidence, reviewed zero-division concept mapping, and no invented concepts for unlabelled failures. Graph reasoning and recommendations run only inside `FeedbackAgent`.

## Verification results

The complete environment-independent backend suite reports **222 passed, 0 failed, 0 skipped**. `compileall` succeeds and `pip check` reports no broken requirements. Coverage includes assignment import, lifecycle recovery/privacy, worker protocol contracts, the requested two-agent cases across Python/C/Java, and persisted report retrieval after reopening SQLite with student/teacher ownership enforcement.

```text
.venv\Scripts\python.exe -m pytest -q
222 passed in 51.09s

.venv\Scripts\python.exe -m compileall -q backend worker tests scripts main.py
exit 0

.venv\Scripts\python.exe -m pip check
No broken requirements found.

git diff --check
exit 0

node <existing-openspec-1.14.1-cli> validate backend-core-audit --strict
Change 'backend-core-audit' is valid

node <existing-openspec-1.14.1-cli> validate implement-codeassess-frontend --strict
Change 'implement-codeassess-frontend' is valid
```

The connected frontend verification reports **61 Vitest tests passed**, **21 Playwright browser scenarios passed** across desktop/tablet/mobile, and successful strict TypeScript, ESLint, and production-build checks. Browser coverage includes student/teacher authentication, assignment create/edit/import, student submission, both agents, report v3, responsive/accessibility checks, and authorization/failure states. The report view renders typed syntax, concept, structural, complexity, secure-test, and bounded output evidence instead of relegating it to raw JSON.

Fake-runner tests supply deterministic outcomes to verify domain behavior. They are not real execution evidence. No student Python, C, or Java source was executed on the host. Docker Desktop or daemon availability was not checked.

## Benchmark status

No project accuracy metric is available or claimed. The frozen multi-language candidate corpus and expected outcomes remain `pending-independent-review`. A separate execution-error candidate set now covers Python, C, and Java syntax and runtime failures, but it is also unreviewed and has never been executed. The evaluation command refuses to publish project metrics from an unapproved corpus. Metric-arithmetic tests verify calculations only and are not grading-accuracy evidence.

The chosen zero-division expected behavior is `5\n5\n0\nError\n` for input `5 0\n`, because the program prints the first three arithmetic results before detecting the invalid division. The corrected fixture is versioned and documented; independent reviewer sign-off remains pending.

## Security verification and limitations

The execution service delegates only to `SubmissionRunner`. There is no host subprocess fallback. The approved local design uses an mTLS client and a separate non-root Linux control service that alone owns rootless Podman. Configuration requires a local-registry immutable image digest, exact toolchain labels, and a hash-pinned seccomp profile. Hidden expectations remain outside the job container. The image definition selects exact Debian Python/Clang/OpenJDK builds and the entrypoint provides bounded capture, deadlines, process-group termination, and workspace cleanup.

Those tests do not establish actual Linux kernel containment, C11/JDK compiler behavior, resource enforcement, streamed output limits, full process-tree termination, workspace disposal, or concurrent-job isolation. These claims require the approved concrete worker and real security suite.

## Remaining 14 tasks

- Independent evidence: 2.3 and 14.2 require external label sign-off for the zero-division fixture and benchmark corpus.
- Real isolated worker: 3.2-3.4 require a pinned built image and verified containment, limits, capture, unique workspaces, termination, and cleanup.
- Compiler authority: 10.2 and 10.3 require C11 and Java 17 compiler diagnostics inside the worker.
- Isolated API example: 8.3 requires the documented request to complete against the real isolated backend.
- Acceptance: 9.3-9.5 and 14.3-14.5 require the real-worker checks, independently approved labels, repeatable held-out metrics, and clean-environment acceptance.

Tasks 9.1 and 14.1 are verified complete through the versioned machine-readable scenario matrix and its exact-coverage regression test. A scenario mapped to a real-worker or independent-review check remains explicitly blocked and is never represented as passing.

## Complete-report capability

The backend can produce, persist, replay, and return a complete structured report using static evidence and approved-runner outcomes. When a secure runtime is unavailable, it produces a complete report about an incomplete assessment: execution is unavailable, total/category are null, functional success is not fabricated, and the limitation is traceable.

## Next steps

1. On the dedicated Linux worker, resolve and record the candidate Debian base's full amd64 digest and snapshot timestamps, then build/push/inspect the selected toolchains.
2. Generate project mTLS identities, record the final image and seccomp digests in ignored actual configuration, and start the non-root control service.
3. Run `scripts/worker/verify-local-worker.py` and retain its real containment, resource, cleanup and concurrency evidence.
4. Obtain independent review of the frozen labels and create a new immutable corpus version for any corrections.
5. Run the held-out benchmark twice, publish actual per-language results and failures, then perform backend acceptance.

OpenSpec sync and change archival remain deferred until backend acceptance. The separately approved frontend change is implemented and verified, but it does not satisfy the outstanding worker or benchmark gates.
