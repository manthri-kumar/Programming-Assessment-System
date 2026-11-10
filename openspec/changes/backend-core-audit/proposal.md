# Proposal

## Why

The repository is a C assessment prototype, not yet the FastAPI, multi-language, multi-agent system described by the project title. Its useful scoring and feedback logic needs reproducible tests, reliable parsing, and isolated execution before it can underpin a defensible backend.

## What Changes

- Establish the evidence-based inventory in `audit.md`; distinguish existing behavior from missing components.
- Introduce a validated backend assessment contract and deterministic evaluation/feedback orchestration, reusing the existing modules through adapters where their behavior remains appropriate.
- Add bounded Python, C, and Java parsing and syntax validation, structural evidence, and an isolated compiler/test runner.
- Preserve legacy weights and category thresholds in a named policy; introduce reviewed improvements with explicit versioning and explainable component results.
- Add a real versioned concept graph, evidence-based learning recommendations, and reproducible labeled evaluation.
- **BREAKING**: the future safe assessment path will refuse host execution; unavailable sandbox/toolchains produce explicit incomplete results rather than silent scores. The standalone legacy script will become an explicit compatibility entry point rather than executing on import.
- The original proposal was planning-only. Application work is now proceeding under the approval recorded in `review.md`; verified completion and remaining blockers are tracked in `tasks.md`. No frontend work is authorized by this change.

## Capabilities

### New Capabilities

- `assessment-api`, `backend-architecture`: validated FastAPI contracts and service boundaries.
- `program-analysis`, `python-analysis`, `c-analysis`, `java-analysis`, `normalized-ir`: bounded parsing and normalized intermediate representation.
- `agent-interfaces`, `evaluation-agent`, `feedback-agent`: exactly two deterministic top-level agents and their typed handoff. The existing concept, syntax, structure, complexity, execution, graph, recommendation, and reporting capabilities remain internal services.
- `isolated-execution`, `rubric-scoring`: secure execution and versioned scoring.
- `knowledge-graph`, `persistence`, `observability`: concept relationships, durable data, errors, logs and orchestration state.
- `assessment-validation`, `frontend-contracts`: reproducible accuracy/testing and future teacher/student integration contracts.
- `academic-workflow`: authenticated teacher/student assignment, rubric, hidden-test, submission-history, report, analytics, and progress APIs needed for backend acceptance.

### Modified Capabilities

None. There are no pre-existing OpenSpec specifications; existing code behavior is documented in the audit and adopted selectively into these new contracts.

## Impact

Existing `main.py`, `modules/sedm.py`, `modules/sbcam.py`, `modules/stcam.py`, `modules/feedback.py`, `testcases.py`, and README will receive targeted changes only after approval. Proposed additions include a FastAPI service, agent/language/runner adapters, graph data, tests, dependency locks, and backend documentation. No frontend, cloud service, external LLM, or remote data store is required. No global installation or destructive cleanup is part of this change.

## Approved two-agent architecture correction

The user approved a correction on 2026-10-19: the system SHALL expose exactly two top-level agents, `ImplementationEvaluationAgent` followed by `FeedbackAgent`. Previously named preprocessing, syntax, concept, structure, complexity, execution, graph, evaluation, recommendation, and report-generation agents become deterministic internal services. Their tested behavior, evidence schemas, rubric arithmetic, Knowledge Graph traversal, fail-closed execution, persistence, and `assessment-report-v2` contract are preserved. This correction changes architectural ownership and public agent discovery; it does not remove capabilities or authorize frontend work, host execution, external LLMs, or unreviewed accuracy claims.

## Approved backend-completion amendment

The user's final project completion instruction on 2026-10-23 authorizes the backend academic workflow before any frontend work. Teacher-owned reference solutions and hidden tests SHALL be visible only to their owner; students SHALL see only their own submissions and reports; teacher analytics SHALL be limited to submissions for owned assignments. Assignment rubrics may override `core-v1` component weights only when all four finite nonnegative weights sum to one. Public self-registration of a teacher account requires a server-configured invitation code. This amendment preserves the two-agent assessment contract and does not relax isolated execution.

## Approved local-worker and Clang amendment

The user approved Clang as the authoritative C11 compiler and selected a project-owned local isolated Linux worker for development and academic demonstration. The worker SHALL run on a dedicated Linux boundary, use a project-controlled rootless container runtime and registry, authenticate its control channel with project-owned mutual TLS, and execute only a reviewed immutable image digest under server-owned limits. FastAPI SHALL never receive the runtime socket or credentials capable of selecting commands, mounts, images, or limits. Exact base/final image digests and observed toolchain versions remain verification outputs and SHALL NOT be invented or treated as approved until a build and inspection record exists.
