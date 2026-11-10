# Two-agent verification

Evidence date: 2026-11-09

Only `ImplementationEvaluationAgent` and `FeedbackAgent` are registered and traced as top-level agents. Parser, concept, structure, complexity, execution, rubric, graph, recommendation, feedback, and report components remain internal services.

## Verified handoff and evidence behavior

- Agent 1 consumes the actual submitted source and immutable assessment configuration, emits bounded `stage-evidence-v1` metadata, preserves `core-v1`, and returns one typed `ImplementationEvaluationResult`.
- Agent 2 rejects any non-`ImplementationEvaluationResult` input. It consumes the exact Agent 1 object, emits evidence-linked `feedback-v3`, traverses only canonical graph nodes, and composes `assessment-report-v3`.
- Identical source/configuration/evidence produces identical immutable report content. Operational duration is retained in stage/audit telemetry but excluded from the academic report so it cannot change replay equality.
- Syntax, functional failure, structural difference, nested complexity, weak concepts, contradictory concepts, and unavailable execution have distinct deterministic feedback paths.
- Execution-unavailable reports keep total/category null, state that static feedback is provisional, and never fabricate test evidence.
- Syntax guidance includes a source location only when the parser supplied one. Missing locations remain absent.
- Recommendations are prerequisite-first, deduplicated, canonically identified, evidence-linked, and include a selection rationale. No graph/evidence means no invented recommendation.

## Verification boundary

Backend automated tests exercise correct, partial, incorrect, syntax, alternate-algorithm, missing-concept, contradiction, cancellation, unavailable-runner, persistence/restart, and API ownership behavior across Python, C, and Java. Fake-runner outcomes verify deterministic domain logic only; they are not real execution evidence. Real Linux isolation and independently reviewed accuracy remain BLOCKED.

An imported-assignment integration test now uploads a private question image through a deterministic extraction adapter, confirms the canonical assignment, submits actual Python source, invokes the real `ImplementationEvaluationAgent` then `FeedbackAgent`, persists `assessment-report-v3`, verifies student/teacher redaction, and updates teacher analytics. It uses `FailClosedRunner`, so static analysis and both-agent handoff are genuine while functional execution remains explicitly unavailable; no fake functional outcome is introduced.

