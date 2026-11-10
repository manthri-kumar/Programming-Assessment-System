# Review status

- Change: backend-core-audit
- State: APPROVED FOR APPLY - implementation in progress.
- Application implementation: 55 of 69 tasks are verified complete after the exactly-two-agent, academic-workflow, and all-specification scenario-matrix work; 14 worker, independent-label, and acceptance tasks remain open, and secure execution remains fail-closed. Revalidation on 2026-11-05 collected and passed 99 environment-independent backend tests; historical counts are superseded by current collection.
- Architectural correction approved by the user's 2026-10-19 instruction: expose exactly `ImplementationEvaluationAgent` and `FeedbackAgent`; retain prior capabilities as internal services and preserve API/report compatibility where possible.
- Backend acceptance: NOT ESTABLISHED.
- Approval evidence: the user's follow-up explicitly stated that the specifications were complete and strict validation had passed, declared readiness to move to implementation, and instructed use of the OpenSpec apply workflow for `backend-core-audit`. This authorizes implementation but not later spec sync/archive or unsafe host execution.

## Review focus

1. Existing prototype is C-only; FastAPI, Python/Java submission adapters and all three agent classes are new work.
2. Proposed initial support: Python 3.11, C11, Java 17 Main.java, standard libraries, one source file.
3. Proposed runner: dedicated Linux worker boundary, strict server-owned limits, no host fallback.
4. Preserve 20/40/20/20 weights and 75/50 categories; core-v1 intentionally changes structure and syntax evidence. Missing components yield no total.
5. Correct the contradictory zero-division expected output only during approved implementation, with versioned fixture review.
6. Text dissimilarity remains a clearly labeled rubric heuristic. Concept guidance uses graph paths and task evidence, not inferred universal mastery.
7. Acceptance requires all mandatory supported-behavior tests passing and separately reported held-out metrics. Frontend remains deferred.

## Setup and verification record

- OpenSpec was absent. Initialized with the existing cached OpenSpec CLI 1.14.1, Node 22.22.2, using `init --tools codex`.
- Generated six Codex workflow skills under `.agents/skills/` and `openspec/config.yaml`; created the spec-driven change through the CLI.
- No global installation, application edits, deletion of tracked artifacts or student-code execution occurred.
- An initial ephemeral npm registry attempt failed DNS resolution; the existing cached CLI completed setup without a new installation.
- CLI validation result: `validate backend-core-audit --strict` PASSED. CLI status reports proposal, design, seven spec files and tasks complete as planning artifacts only.
- Backend tests: not run; no automated suite currently exists. This draft specifies its creation after approval.
- Implementation update: added `backend/models.py`, `backend/runner.py`, `tests/test_models_and_runner.py`, `requirements.txt`, `requirements-dev.txt`, and `docs/backend/support.md`. Five standard-library tests pass. No submission source was executed.
- Implementation update: added `backend/scoring.py` and `tests/test_scoring.py`; the legacy formula helpers and core-v1 weighting/boundary behavior are covered. The broader module/feedback characterization task remains pending.
- Current verification: 10/10 standard-library tests pass; `compileall`, `git diff --check`, and strict OpenSpec validation pass.
- Specification revision: expanded the change from 7 to 18 capability specifications, added explicit inputs/outputs, edge cases, failure handling, acceptance criteria and dependencies to every spec, and added implementation phases 10-14 to tasks.md. No application code was edited during this specification-only update.
- Apply update: implemented safe Python AST analysis, canonical IR hashing, concept graph validation/traversal, deterministic agent contracts, reviewed corpus loading, and fail-closed execution integration. Added `docs/BACKEND_FINAL_RESULTS.md`. No C/Java source or untrusted program was executed.
- Proposed defaults reconciled: Linux containers remain mandatory; SQLite is the initial persistence target; Python AST plus pinned tree-sitter C/Java provide static parsing; role authorization is implemented; minimal retention and independent labels remain policy requirements with the open details recorded in design.md.
- Secure execution blocker: Docker CLI is present, but `docker version` cannot connect to the Linux daemon (`dockerDesktopLinuxEngine` pipe unavailable). The production runner therefore fails closed; real-runner security acceptance is not claimed.
- Dependency update: project-local pinned dependencies were installed in `.venv`; no global tool was installed.
- Apply verification: FastAPI, role authorization, SQLite persistence, Python/C/Java static parsing, normalized IR, deterministic agents, graph traversal, direct assessment API, and generated OpenAPI are implemented to the extent recorded in `tasks.md`.
- Continuation update: added legacy goldens, bounded IR edit comparison, unsupported dependency/layout checks, complete deterministic orchestration, evidence-linked graph feedback, SQLite schema v2 replay/retention, structured observability, stable API errors, container control-plane contracts, a frozen candidate split, and a review-gated benchmark command.
- Two-agent amendment: refactored prior agent-named stages into typed internal services; registered and orchestrated exactly `ImplementationEvaluationAgent` then `FeedbackAgent`; preserved rubric, graph, feedback, recommendation, persistence, API, and `assessment-report-v2` behavior.
- Current verification: 59 pytest tests pass with 0 failures and 0 skips; compileall, `pip check`, `git diff --check`, and strict OpenSpec 1.14.1 validation pass.
- Execution remains blocked pending a concrete approved isolated engine and pinned image digest. Docker availability was not checked during this continuation. No submission source was executed and no host fallback exists.
- Empirical metrics remain unavailable: the multi-language candidate split is frozen but explicitly pending independent review.

## Artifact index

- [Repository audit](audit.md)
- [Proposal](proposal.md)
- [Technical design](design.md)
- [Actionable implementation tasks](tasks.md)
- [Assessment API specification](specs/assessment-api/spec.md)
- [Deterministic agents specification](specs/deterministic-agents/spec.md)
- [Program analysis specification](specs/program-analysis/spec.md)
- [Isolated execution specification](specs/isolated-execution/spec.md)
- [Rubric scoring specification](specs/rubric-scoring/spec.md)
- [Concept learning specification](specs/concept-learning/spec.md)
- [Assessment validation specification](specs/assessment-validation/spec.md)
- Additional specifications: `academic-workflow`, `backend-architecture`, `python-analysis`, `c-analysis`, `java-analysis`, `normalized-ir`, `agent-interfaces`, `concept-analysis-agent`, `syntax-analysis-agent`, `structural-comparison-agent`, `test-execution-agent`, `complexity-analysis-agent`, `evaluation-agent`, `feedback-agent`, `knowledge-graph`, `learning-recommendation-agent`, `persistence`, `observability`, and `frontend-contracts`.

## Repeat validation

With an available OpenSpec 1.14.1 CLI:

```powershell
openspec validate backend-core-audit --strict
openspec status --change backend-core-audit
```

This session used the cached CLI at `C:/Users/manth/AppData/Local/npm-cache/_npx/20f2b75ddc8bce88/node_modules/@fission-ai/openspec/bin/openspec.js` through `node`, with telemetry disabled. This cache path is machine-specific and is not a portable dependency guarantee. A future portable CLI installation can be project-local; any global installation requires confirmation.

## 2026-10-23 backend-completion amendment

The user supplied and approved the final project master instruction to complete the academic backend while retaining exactly two top-level agents and deferring frontend work until backend acceptance. The amendment adds `academic-workflow` and tasks 17.1-17.4. Implementation now requires a server-owned teacher invitation code, enforces assignment ownership for hidden reference/tests/rubrics and submissions, supports validated custom `core-v1` weights, and adds role-scoped history, analytics, and progress APIs.

Verification: 67 tests passed in 3.79 seconds with zero failures/skips; `compileall`, `pip check`, generated OpenAPI equality, and strict OpenSpec validation passed. No submission source was executed. The container-only worker entrypoint and fixed command protocol are implemented and unit-tested, but real containment is not established. Real isolated-worker acceptance and independent benchmark review remain open, so backend acceptance and frontend authorization remain gated.

## 2026-10-25 continuation audit

The 53 checked tasks were cross-checked against implementation and executable evidence; none was reopened. The 16 open tasks are catalogued verbatim with dependencies and blockers in `docs/backend/REMAINING_OPENSPEC_TASKS.md`. The worker adapter now has a strict bounded JSON protocol, fail-closed engine/cleanup handling, and unit-tested simulated Python/C/Java outcomes without host execution. Authoritative isolated compile failures now invalidate scoring instead of producing a static syntax score. Concurrent submission isolation and expanded benchmark/repeatability calculations are covered.

Full verification reports 82 passed, 0 failed, and 0 skipped in 3.53 seconds. The run exposed a non-canonical Base64URL authentication-token encoding accepted by the decoder; canonical encoding validation was added and the full suite then passed. `compileall`, `pip check`, `git diff --check`, generated API contract checks, and strict OpenSpec validation pass. No Docker/daemon availability check or submitted-source execution occurred.

No open task was marked complete: real Python/C11/Java17 execution, Linux isolation evidence, the documented Clang-versus-GCC approval, a registry/image digest and protected worker control plane, and independent benchmark review are still external gates. A formal gstack CSO run was not available because its trusted launcher is absent; the security assessment in `docs/backend/OPENSPEC_IMPLEMENTATION_AUDIT.md` is a manual static/OpenSpec review and is not represented as a formal audit.

## 2026-10-25 local-worker and Clang approval

The user explicitly approved Clang as the authoritative C11 compiler and selected a project-owned local isolated Linux worker for development and academic demonstration. The corresponding design uses rootless Podman owned by a separate worker control service, a project-owned local registry, and project-owned mutual TLS between FastAPI and the control service. This approval authorizes reproducible configuration and integration code but does not approve an invented image digest, generated private keys in source control, or execution before the worker image/toolchains and isolation controls are inspected. Benchmark labels remain pending independent review.

Implementation now includes the mTLS API-side engine, environment-gated runner configuration, separate non-root Linux control service, server-owned rootless-Podman command policy, immutable image/toolchain readiness checks, hash-pinned seccomp configuration, exact selected Debian package builds, reproducible build/certificate/verification scripts, and hidden expected-output separation. The candidate benchmark now has twelve correct/partial/incorrect/boundary programs across all three languages and remains pending review. Environment-independent verification reports 93 passed, 0 failed, and 0 skipped in 3.24 seconds. No container runtime was probed, no image digest was invented, and no submitted source was executed; the task ledger remains 53/69 because real-worker and independent-review acceptance criteria remain unmet.

## 2026-11-05 full-stack integration verification

The active specifications now have a versioned machine-readable scenario matrix with exact regression coverage. Each scenario maps to an executable test or a named real-worker/reviewer gate; blocked gates cannot be represented as passing. Tasks 9.1 and 14.1 are therefore complete, bringing the ledger to 55/69. The real-worker verifier was expanded for cancellation, descendant-process cleanup, crash-after-output, whitespace semantics, and existing resource/concurrency checks, but was not executed because no approved isolated worker was available.

The backend suite passes 99 tests with zero failures or skips; `compileall`, `pip check`, and strict validation pass for both active changes. The connected frontend passes 23 unit/component tests, 9 Playwright scenarios across desktop/tablet/mobile, strict TypeScript, ESLint, and production build. The assessment report now displays typed internal evaluation findings and functional-test outcomes while retaining exactly two top-level agents. Candidate syntax/runtime benchmark cases cover all three languages but remain pending independent review and unexecuted. Backend acceptance remains NOT ESTABLISHED.
