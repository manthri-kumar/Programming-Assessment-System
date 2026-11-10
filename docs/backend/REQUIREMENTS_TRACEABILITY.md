# Backend requirements traceability

Verified: 2026-11-07  
OpenSpec change: `backend-core-audit`  
Machine-readable scenario source: `data/validation/scenario-matrix-v1.json`

Status meanings: **verified** means the implementation and its environment-independent acceptance evidence passed; **partial** means the safe implementation exists but authoritative worker evidence is absent; **blocked** means completion needs an approved isolated worker or independent reviewer.

| OpenSpec capability | Implementation | Executable evidence | Status |
| --- | --- | --- | --- |
| `academic-workflow` | `backend/api.py`, `backend/auth.py`, `backend/persistence.py` | `tests/test_api_and_persistence.py`, Playwright teacher/student workflow | Verified |
| `agent-interfaces` | Typed `AgentContext`, `ImplementationEvaluationResult`, `FeedbackResult`, and `BaseAgent` in `backend/agents.py` | `tests/test_analysis_and_agents.py`, `tests/test_two_agent_end_to_end.py` | Verified |
| `assessment-api` | Bounded FastAPI requests, stable errors, readiness, assessment and academic routes | `tests/test_models_and_runner.py`, `tests/test_api_and_persistence.py`, generated OpenAPI equality | Verified except real isolated example |
| `assessment-validation` | Candidate corpora, review gate, scenario matrix, metric/repeatability calculator | `tests/test_benchmark.py`, `tests/test_scenario_matrix.py` | Blocked by independent review and real predictions |
| `backend-architecture` | HTTP/domain/repository/runner separation and dependency injection | agent, API and persistence suites | Verified |
| `c-analysis` | Language-aware static parser plus fixed Clang worker command | parser tests and worker protocol tests | Partial; authoritative Clang run blocked |
| `complexity-analysis-agent` | Internal bounded static complexity service | cross-language agent tests | Verified |
| `concept-analysis-agent` | Internal evidence-scoped concept service | mapped, unmapped and missing-concept tests | Verified |
| `concept-learning` | Versioned graph, validation, traversal and evidence paths | graph and recommendation tests | Verified; empirical quality unmeasured |
| `deterministic-agents` | Exactly two top-level agents with deterministic internal services | repeatability, no-network and acceptance-outcome tests | Verified |
| `evaluation-agent` | `ImplementationEvaluationAgent` stage coordination and rubric result | two-agent, syntax-skip and unavailable-execution tests | Verified; real execution stage blocked |
| `feedback-agent` | `FeedbackAgent` graph reasoning, feedback, recommendation and report composition | agent, acceptance and report-view tests | Verified |
| `frontend-contracts` | Client-safe schemas and role-scoped routes | API authorization tests and 12 Playwright scenarios | Verified |
| `isolated-execution` | Fail-closed adapter, mTLS client, rootless-Podman control service and bounded entrypoint | contract/protocol/configuration tests | Blocked pending built, pinned Linux worker |
| `java-analysis` | Static Java boundary parser plus Java 17 worker command | parser/layout and worker protocol tests | Partial; authoritative `javac` run blocked |
| `knowledge-graph-agent` | Internal graph reasoning owned by `FeedbackAgent` | contradiction, invalid-graph and discovery tests | Verified |
| `knowledge-graph` | `data/concepts/concept-v1.json`, graph loader and validator | cycle, dangling-edge and traversal tests | Verified |
| `learning-recommendation-agent` | Prerequisite-first deterministic recommendations | zero-division and shared-prerequisite tests | Verified; empirical quality unmeasured |
| `normalized-ir` | Canonical IR, serialization, hashes and bounded comparison | normalization/edit-comparison tests | Verified for documented static subset |
| `observability` | Correlation IDs, redacted audit events and stable error taxonomy | sanitized-error, cancellation and audit tests | Verified |
| `persistence` | Transactional SQLite users, assignments, submissions, evaluations, activity and replay records | round-trip, rollback, concurrency, retention and repository-reopen tests | Verified |
| `program-analysis` | Python/C/Java static adapters and shared structural evidence | language and alternative-algorithm tests | Verified for static subset; compiler authority blocked for C/Java |
| `python-analysis` | Python 3.11 AST parsing without import/execution | malformed, normalized and unsupported-import tests | Verified for static analysis |
| `rubric-scoring` | `legacy-v1` characterization and configurable `core-v1` arithmetic | `tests/test_legacy_characterization.py`, `tests/test_scoring.py` | Verified for controlled evidence |
| `structural-comparison-agent` | Internal bounded structural comparison service | equivalent/different/limit tests | Verified |
| `syntax-analysis-agent` | Internal cross-language syntax/static classification service | valid, malformed, unsupported and unavailable tests | Verified statically; worker compiler checks blocked |
| `test-execution-agent` | Internal secure-execution service over `SubmissionRunner` only | fake/fail-closed protocol tests | Blocked for real containment evidence |

Every specification scenario is enumerated in `data/validation/scenario-matrix-v1.json`. `tests/test_scenario_matrix.py` rejects missing or extra scenario mappings and requires blocked real-worker/reviewer scenarios to remain explicit.

## Score interpretation

- `tests: 0.0` is emitted only when actual supplied execution evidence says no weighted test passed.
- Unavailable execution produces `status: incomplete`, `total: null`, `category: null`, and no fabricated test component.
- `originality: 0.0` means the submitted and reference text are identical under the documented text-dissimilarity heuristic. It is not a misconduct finding.
- A structurally different program can retain passing functional outcomes; structural similarity is never used as semantic equivalence.

