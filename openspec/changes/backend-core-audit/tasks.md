# Tasks

The change is approved and application is in progress. Execute groups in dependency order; each group includes its own tests and documentation. Capability names map to `specs/<name>/spec.md`. As verified on 2026-11-05, **55 of 69 tasks are complete** and the full environment-independent suite passes **99 tests**. The 14 open tasks remain unchecked because they require independently reviewed labels, a built/inspected real worker and security evidence, or acceptance gates that depend on those inputs.

## 1. Review gate

- [x] 1.1 Obtain explicit user approval of proposal, design, seven specifications and proposed policy/fixture changes; verify the approving message is recorded in review.md before application-code edits.
- [x] 1.2 Record approved support matrix, limits and rubric policy in docs/backend/support.md; verify it agrees with the approved specs and identifies remaining unsupported behavior.

## 2. Reproducible baseline and contracts

- [x] 2.1 Add pinned Python development/runtime dependency manifests and documented setup; verify clean-environment installation and test discovery without importing main.py.
- [x] 2.2 Characterize sbcam, sedm, stcam, feedback, weighting and classification through fixed fixtures and mocked subprocess results; verify legacy-v1 golden results including zero-reference counts, error counts and feedback boundaries without host execution.
- [ ] 2.3 Add versioned task/corpus schema, source hashes and corrected arithmetic fixtures; verify teacher-output labels are independently reviewed, the zero-divisor correction is logged, and corpus validation rejects inconsistent metadata.
- [x] 2.4 Freeze a development/held-out split before metric tuning; verify disjoint case IDs/hashes and preserve label-review provenance in dataset documentation.
- [x] 2.5 Add typed request, evidence, component, case and assessment models; verify size, enum, ID, finite weight, null/status and version invariants with model tests and documented examples (assessment-api).

## 3. Isolation foundation

- [x] 3.1 Define runner protocol and deterministic fake runner; verify fake outcomes cover success, syntax failure, runtime error, timeout and unavailable infrastructure without launching submissions (isolated-execution).
- [ ] 3.2 Add pinned Linux worker/container definitions and dedicated runner configuration; verify toolchain versions/image digests, unprivileged user, disabled network, dropped privileges, read-only root, no host mounts/secrets and protected control channel using real-runner checks.
- [ ] 3.3 Implement unique workspace transfer, bounded compilation/analysis/execution and streamed capture limits; verify compile hang, loop, flood, memory, process and scratch-limit outcomes with real-runner fixtures.
- [ ] 3.4 Implement full process-tree cleanup on success/failure/cancellation and stale-artifact prevention; verify repeated and overlapping jobs cannot share outputs and leave no workspaces or descendants.
- [x] 3.5 Implement fail-closed readiness for missing worker/toolchains; verify no host compiler/submission fallback and document Windows Linux-worker setup plus security limitations.

## 4. Program analysis and behavior tests

- [x] 4.6 Document parser normalization, supported constructs and diagnostic meanings; verify every example is backed by a fixture for its supported language.

## 5. Versioned rubric scoring

- [x] 5.1 Extract legacy-v1 characterization policy and core-v1 component composition; verify 20/40/20/20 weighting, original category boundaries and explicit changed component semantics against goldens (rubric-scoring).
- [x] 5.2 Enforce finite [0,100] components, unrounded classification and final display rounding; verify total 74 for 80/100/50/40 and boundaries 49.999/50/74.999/75.
- [x] 5.3 Implement invalid_submission/incomplete/null-total behavior without weight redistribution; verify learner syntax failure, analysis_limit and missing infrastructure remain distinguishable.
- [x] 5.4 Document policy differences and similarity limitations; verify before/after sample results expose versions and never claim text similarity proves misconduct.

## 6. Concept graph and recommendations

- [x] 6.1 Add versioned concept JSON, typed adjacency and validation; verify unique nodes, endpoint integrity, prerequisite-cycle rejection and readiness failure for invalid/missing graphs (concept-learning).
- [x] 6.2 Define evidence-to-concept associations and task-scoped satisfaction rules; verify zero-division evidence maps correctly, unlabeled failures do not invent concepts and unknown mastery stays explicit.
- [x] 6.3 Add prerequisite traversal, deduplication and stable ordering; verify shared ancestors precede dependents, satisfied ancestors are omitted and each recommendation includes evidence/path/version.
- [x] 6.4 Document graph schema, edge direction and recommendation examples; verify examples against graph fixtures and goldens.

## 7. Deterministic agent pipeline

- [x] 7.1 Add BaseAgent typed contract, EvaluationAgent and orchestrator using language/runner/scoring adapters; verify cooperation, evidence lineage and propagation of student versus infrastructure outcomes (deterministic-agents).
- [x] 7.2 Add FeedbackAgent consuming evaluation and graph results with versioned templates; verify actionable diagnostic-linked feedback and no invented scores, concepts or plagiarism verdicts.
- [x] 7.3 Verify normalized repeated-run equality with fixed inputs/outcomes/versions and network calls blocked; document agent responsibilities and exclude timing/request IDs from equality.

## 8. FastAPI backend and compatibility entry point

- [x] 8.1 Add GET /health and /ready with dependency checks; verify liveness remains available while invalid graph or missing sandbox/toolchain returns readiness 503 (assessment-api).
- [x] 8.2 Add bounded POST /assessments and sanitized 422/503/500 handlers; verify success, learner syntax failure, unsupported payloads and unavailable infrastructure using API contract tests.
- [ ] 8.3 Publish generated OpenAPI and backend request/result examples; verify documented fields/statuses/limits agree with the generated contract and examples execute against the isolated backend.
- [x] 8.4 Guard main.py and route the explicit CLI through the approved pipeline with opt-in plotting; verify import causes no compiler/process/GUI effects and CLI output preserves policy transparency.

## 9. Backend acceptance and empirical evaluation

- [x] 9.1 Add a scenario-to-test matrix covering all seven specs; verify every scenario has a passing executable test or reproducible real-runner security check (assessment-validation).
- [x] 9.2 Implement the frozen-corpus evaluation command and machine-readable report; verify hand-computable syntax confusion/F1, test agreement, score MAE, category agreement and recommendation precision/recall calculations with per-language counts.
- [ ] 9.3 Run mandatory characterization/unit/API/integration/real-runner security suites on the pinned environment; verify 100% pass on supported behaviors with zero skipped mandatory checks and publish actual results.
- [ ] 9.4 Run held-out evaluation twice; verify stable decisions/metrics and record exact commands, corpus hashes, versions, failures, exclusions and empirical limits without universal-accuracy claims.
- [ ] 9.5 Reproduce documented backend setup from a clean environment and record backend acceptance in review.md; verify no LLM credentials or frontend are needed and no frontend development starts before acceptance.

## Workflow follow-up

- After user acceptance, sync the accepted specs and archive this change using OpenSpec; artifact completeness alone does not authorize archive.
- Frontend requires a later separately reviewed OpenSpec change after backend acceptance.

## 10. Language adapters and normalized IR

- [x] 10.1 Implement the Python 3.11 AST adapter and its syntax/unsupported-import fixtures; verify no source import or execution occurs (python-analysis).
- [ ] 10.2 Implement the C11 parser/compiler adapter and diagnostic fixtures; verify comments/strings and nonzero exit status are handled structurally (c-analysis).
- [ ] 10.3 Implement the Java 17 Main.java adapter and layout/toolchain fixtures; verify multi-file and external dependency requests are rejected (java-analysis).
- [x] 10.4 Define canonical normalized IR schema, serialization and evidence hashes; verify equivalent formatting/renaming is byte-stable (normalized-ir).
- [x] 10.5 Implement bounded IR comparison and complexity indicators; verify alternate algorithms remain behaviorally separate from structure and limits return explicit statuses (structural-comparison-agent, complexity-analysis-agent).

## 11. Agent contracts and orchestration

- [x] 11.1 Define BaseAgent typed protocol, immutable context, evidence lineage and version discovery; verify all registered agents satisfy contract conformance (agent-interfaces).
- [x] 11.2 Implement ConceptAnalysisAgent and SyntaxAnalysisAgent; verify mapped/unmapped concepts and learner/infrastructure status separation (concept-analysis-agent, syntax-analysis-agent).
- [x] 11.3 Implement StructuralComparisonAgent and ComplexityAnalysisAgent; verify bounded evidence and no hidden score mutation (structural-comparison-agent, complexity-analysis-agent).
- [x] 11.4 Implement Secure TestExecutionAgent over the approved runner; verify all execution requests fail closed when the worker is unavailable (test-execution-agent).
- [x] 11.5 Implement EvaluationAgent stage order, cancellation and policy composition; verify syntax failure skips execution and missing evidence yields null total (evaluation-agent).
- [x] 11.6 Implement FeedbackAgent and LearningRecommendationAgent; verify every message/recommendation links to evidence, graph version and prerequisite path (feedback-agent, learning-recommendation-agent).

## 12. Knowledge graph and persistence

- [x] 12.1 Define versioned concept/edge data and graph validator; verify cycles, dangling edges and duplicate IDs prevent readiness (knowledge-graph).
- [x] 12.2 Add prerequisite traversal and evidence-based mastery rules; verify stable deduplicated recommendation order and task-scoped claims (learning-recommendation-agent).
- [x] 12.3 Define repository interfaces and transactional persistence schema; verify assessment replay, migration, retention and redaction behavior (persistence).
- [x] 12.4 Add structured redacted logs, correlation IDs, error taxonomy and cancellation tracing; verify secrets/source are not emitted (observability).

## 13. API and future client contracts

- [x] 13.1 Implement FastAPI health/readiness endpoints from the approved schema; verify readiness reports graph/toolchain/worker dependencies without executing submissions (backend-architecture, assessment-api).
- [x] 13.2 Implement POST /assessments through EvaluationAgent with bounded validation and stable errors; verify student and infrastructure failures map to distinct responses (assessment-api).
- [x] 13.3 Publish generated OpenAPI examples and version compatibility rules for future teacher/student clients; verify no frontend code or internal paths are exposed (frontend-contracts).
- [x] 13.4 Guard the compatibility CLI and remove import-time side effects while preserving opt-in plotting; verify importing main.py performs no compilation, execution or GUI activity.

## 14. Benchmarking and acceptance

- [x] 14.1 Create a scenario-to-test matrix for all active capability specifications; verify each requirement has an executable or explicitly reproducible security check (assessment-validation).
- [ ] 14.2 Add independent labeled corpus review workflow and corrected zero-division fixture version; verify development/held-out hashes are disjoint (assessment-validation).
- [ ] 14.3 Run unit, contract, integration and real-worker security suites; verify all defined supported behaviors pass and no mandatory checks are skipped.
- [ ] 14.4 Run held-out benchmark twice and publish per-language syntax/test/score/category/recommendation metrics, failures and limitations; verify repeatability without universal accuracy claims.
- [ ] 14.5 Record backend acceptance and environment/toolchain/image/policy/graph/corpus versions; verify frontend work remains deferred to a separate approved change.

## 15. Complete agent integration amendment

- [x] 15.1 Audit all twelve required agents against implementation, typed contracts, orchestration, evidence influence, failure behavior, determinism and tests; publish the verified matrix in `docs/backend/AGENT_IMPLEMENTATION_AUDIT.md` (agent-interfaces, deterministic-agents).
- [x] 15.2 Implement typed stage payload contracts and KnowledgeGraphAgent reasoning for weak, satisfied, unknown and contradictory task-scoped evidence; verify graph validation, stable paths, registration and repeatability (knowledge-graph-agent).
- [x] 15.3 Refactor orchestration to execute every stage once in the approved dependency order, skip unsafe/dependent stages explicitly, generate the complete report, persist it, and expose it through the API; verify all twelve agents affect the report where applicable (evaluation-agent, feedback-agent, assessment-api, persistence).
- [x] 15.4 Add independent expected-outcome fixtures and unit, integration, API, security and regression scenarios for correct, incorrect, partial, syntax, concept, alternate algorithm, structure, complexity, prerequisite, contradiction and unavailable-execution cases; record candidate-label review status without publishing unreviewed accuracy (assessment-validation).

## 16. Two-agent architecture correction

- [x] 16.1 Record the approved exactly-two-agent boundary in proposal, design, review, and affected capability specifications; verify strict OpenSpec validation passes before application refactoring.
- [x] 16.2 Refactor preprocessing, syntax, concept, structure, complexity, secure execution, rubric, graph, recommendation, and report components into typed internal services; verify no working behavior or fail-closed boundary is removed.
- [x] 16.3 Implement `ImplementationEvaluationAgent` followed by `FeedbackAgent` as the only registered/orchestrated agents; verify a typed handoff, two-agent traces, API compatibility, persistence, and `assessment-report-v2`.
- [x] 16.4 Add two-agent contract and regression tests for scores, findings, evidence, feedback, recommendations, unavailable execution, and deterministic reports; update implementation/audit/result documentation with actual verification.

## 17. Authenticated academic workflow amendment

- [x] 17.1 Record the approved backend-completion scope in proposal, design, and `academic-workflow`; verify strict OpenSpec validation before implementation.
- [x] 17.2 Add transactional assignment update, role-scoped submission/history queries, evaluation summaries, and bounded pagination; verify repository ownership inputs and aggregate handling.
- [x] 17.3 Complete teacher/student API authorization, teacher invitation registration, rubric/test management, submission/report history, teacher analytics, and student progress; verify hidden data and cross-owner access are rejected.
- [x] 17.4 Publish the updated OpenAPI and backend workflow examples; run unit, integration, API, regression, compilation, and strict OpenSpec validation and record actual evidence.
