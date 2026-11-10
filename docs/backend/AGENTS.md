# Deterministic assessment agents

The backend exposes exactly two top-level agents. Both implement the runtime-checkable `BaseAgent` protocol with a stable name/version, immutable `AgentContext`, deterministic `run` operation, typed result, evidence, and limitations. Internal assessment capabilities are services and are not independently registered or orchestrated as agents.

| Main agent | Responsibility | Internal services |
| --- | --- | --- |
| `ImplementationEvaluationAgent` | Analyze and evaluate a submission, producing one typed `ImplementationEvaluationResult`. | Code preprocessing, Python/C/Java syntax analysis, concept detection, structural comparison, complexity analysis, secure test execution, rubric evaluation, evidence collection, limitation collection. |
| `FeedbackAgent` | Consume the exact Agent 1 result and produce one typed `FeedbackResult` with the final report. | Knowledge Graph reasoning, prerequisite traversal, strengths/weaknesses, error explanation, feedback templates, learning recommendations, `assessment-report-v2` composition. |

`AssessmentOrchestrator` invokes `ImplementationEvaluationAgent` and then `FeedbackAgent`. The `registered_agents()` result and top-level audit trace contain exactly `implementation-evaluation` and `feedback`. Internal service results remain visible in `report.stages` and API `analysis` for evidence inspection.

A pre-cancelled context or invalid policy stops before the execution runner. Syntax/preprocessing failure records an explicit skipped execution service. Runner unavailability produces an incomplete evaluation with null total/category; `FeedbackAgent` still composes a report from valid static evidence and records the limitation.

No component imports an LLM client or needs network access. Repeated-run tests compare decisions, evidence, feedback, recommendations, and reports. Fake-runner outcomes verify domain integration only; real execution evidence requires the approved isolated Linux worker.
