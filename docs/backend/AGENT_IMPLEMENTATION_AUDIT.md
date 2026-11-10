# Agent implementation audit

Date: 2026-11-07  
OpenSpec change: `backend-core-audit`  
Architectural decision: the user approved exactly two top-level agents. Former agent-named capabilities are preserved as typed internal services.

## Top-level agent matrix

| Main agent | Typed input/output | Implemented logic and influence | Integration and traceability | Failure behavior | Verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `ImplementationEvaluationAgent` | Immutable `AgentContext` to immutable `ImplementationEvaluationResult`, including stage map, rubric result, evidence, limitations, and version. | Coordinates preprocessing, language-aware syntax, concept detection, IR structure comparison, static complexity, secure execution delegation, and core-v1/legacy-v1 rubric composition. Its score and status directly control the assessment result. | First and only first-stage top-level invocation. It emits one `agent_complete` event; each internal result emits `stage_trace`. Evidence lineage is carried into Agent 2 and `assessment-report-v2`. | Cancellation/invalid policy stop before execution. Syntax failure skips execution. Missing approved runner returns incomplete with null total/category. Contradictory evidence returns `invalid_evidence`. | Registry, protocol, typed handoff, ordering, cancellation, policy, syntax, score, contradiction, fail-closed, deterministic, and no-network tests. | **Implemented and integrated. Real isolated execution remains unverified.** |
| `FeedbackAgent` | Exact `ImplementationEvaluationResult` to immutable `FeedbackResult`, including graph reasoning, strengths, weaknesses, feedback, recommendations, report, evidence, and limitations. | Explains evidenced errors, identifies strengths/weaknesses, reasons over the versioned graph, traverses prerequisites, generates deterministic recommendations and composes the final report. It does not rerun parsing, scoring, or execution. | Invoked exactly once after Agent 1. It emits the second `agent_complete` event. Its report is persisted and returned by FastAPI; the trace is exactly `implementation-evaluation`, `feedback`. | Missing/invalid graph is explicit and yields no invented recommendations. Unavailable execution is reported as a limitation while the null score is preserved. A non-Agent-1 handoff is rejected. | Typed-handoff, evidence linkage, graph paths/order, contradictions, feedback, report v2, persistence, API, deterministic, and no-network tests. | **Implemented and integrated for environment-independent behavior.** |

`BaseAgent` is the common protocol rather than a third agent. Only the two classes above satisfy it and appear in `registered_agents()`.

## Internal service matrix

| Owner | Internal service | Preserved behavior | Current limitation |
| --- | --- | --- | --- |
| Agent 1 | `CodePreprocessingService` | Bounded Python/C/Java parsing, normalized IR and canonical evidence hash. | Static parser support boundary applies. |
| Agent 1 | `SyntaxAnalysisService` | CPython AST and tree-sitter C/Java diagnostics; learner/unsupported/infrastructure states remain distinct. | C11/JDK compiler authority awaits the isolated worker. |
| Agent 1 | `ConceptAnalysisService` | Task-scoped present/absent/unmapped findings, including Python input and guarded-division detection. | Conservative static inference is reported. |
| Agent 1 | `StructuralComparisonService` | Bounded normalized IR edit score and explicit analysis limit. | Structural similarity is a rubric heuristic, not behavioral equivalence. |
| Agent 1 | `ComplexityAnalysisService` | IR size, loop nesting/locations, structural estimate and Python direct recursion. | C/Java recursion and data-dependent bounds remain unknown. |
| Agent 1 | `SecureTestExecutionService` | Delegates only to `SubmissionRunner`; returns per-case evidence; has no subprocess or host fallback. | Real containment, compilers, resource limits and cleanup await a concrete approved worker. |
| Agent 1 | `RubricEvaluationService` | Preserves 20/40/20/20 scoring, category boundaries, null totals for missing evidence and no weight redistribution. | Functional totals require genuine approved-runner evidence in production. |
| Agent 2 | `KnowledgeGraphReasoningService` | Versioned graph validation; weak/satisfied/unknown/contradictory task-scoped evidence; stable paths. | Candidate benchmark labels await independent review. |
| Agent 2 | `FeedbackCompositionService` | Versioned evidence-linked messages for syntax, tests, similarity, graph and infrastructure states. | It cannot diagnose causes beyond available evidence. |
| Agent 2 | `LearningRecommendationService` | Stable prerequisite-first recommendations with evidence, path and graph version. | No valid graph/evidence yields no recommendation. |
| Agent 2 | `ReportCompositionService` | Deterministic `assessment-report-v2` with both agents, internal stages, versions, lineage and limitations. | Execution fields remain explicitly unavailable without the worker. |

## Effective workflow

```text
Submission
  -> ImplementationEvaluationAgent
       -> preprocessing -> syntax -> concepts -> structure -> complexity
       -> approved secure runner -> rubric -> typed evaluation result
  -> FeedbackAgent
       -> graph reasoning -> strengths/weaknesses -> feedback
       -> prerequisite recommendations -> assessment-report-v2
  -> SQLite persistence -> FastAPI response
```

The former twelve-agent design is historical. The amendment changes ownership and public discovery without deleting its tested parsing, scoring, graph, feedback, recommendation, or report behavior. API `agents` and report `trace` now expose exactly two agents; detailed service evidence remains available under `analysis` and `report.stages`.

## Verification boundary

The consolidated end-to-end regression in `tests/test_two_agent_end_to_end.py` covers correct/incorrect Python, correct/incorrect C, correct/incorrect Java, partial Python, syntax failure, a structurally different valid algorithm, and a missing required concept. It verifies normalized IR, every Agent 1 internal stage, rubric evidence, the typed Agent 1→Agent 2 handoff, graph recommendations, non-contradictory feedback, exactly two `agent_complete` events, SQLite persistence across repository reopen, student access, owning-teacher access, and cross-owner rejection.

Verification on 2026-11-07: targeted agent/API/persistence tests **37 passed**; the complete backend suite **109 passed**; frontend unit/component tests **38 passed**; and disposable-backend Playwright integration **12 passed** across desktop, tablet, and mobile. TypeScript, ESLint, and the production build passed. Browser verification retrieved persisted reports and displayed both top-level agents plus the explicit fail-closed execution limitation.

`FakeRunner` verifies scoring and orchestration using controlled supplied outcomes; it is not represented as real student-code execution. `FailClosedRunner` verifies explicit unavailability. No student program was run on the host, and Docker availability was not checked.

Real Linux containment, C11/JDK compiler authority, resource enforcement, process-tree cleanup, and independently reviewed held-out accuracy remain open. The backend can still produce a complete structured report describing an incomplete evaluation, with null total/category and explicit execution limitations.
