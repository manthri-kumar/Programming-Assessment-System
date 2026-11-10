# Two-agent verification

Evidence date: 2026-11-10

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

## Agent regression verification, 2026-11-10

The following command completed with **67 passed, 0 failed**:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_two_agent_end_to_end.py tests/test_scenario_matrix.py tests/test_scoring.py tests/test_agent_evidence_regressions.py tests/test_analysis_and_agents.py tests/test_agent_acceptance_outcomes.py tests/test_university_readiness_models.py -q
```

Confirmed defects corrected within the existing agent contracts:

- A normal call to a Python function previously counted as recursion. Complexity metric `complexity-static-v3` now checks cycles among direct named module-function calls. Nested function and method recursion remain explicitly unsupported; dynamic call resolution and runtime complexity are not inferred.
- Passing functional concept evidence plus static absence previously left a concept simultaneously weak and satisfied. Both evidence records are now retained as a contradiction, weak guidance is available for review, and the satisfied set excludes the conflicted concept.
- Worker-unavailable feedback previously dropped supported structural and complexity observations. It now retains those observations with evidence references and explicit provisional limitations while keeping the total null and functional outcomes absent.
- Functional feedback distinguishes wrong output, runtime errors, timeouts and resource limits using only the outcome category, without copying private output or diagnostics into the explanation.
- Python/C/Java AST node and depth bounds now apply before recursive IR conversion. Analysis-limit and unsupported cases keep unknown score components absent instead of assigning a zero syntax grade.
- Required assignment concepts are accepted separately from test labels by `AssessmentService`, included in request identity, and carried to the evaluation and feedback agents.
- Any worker outcome marked unavailable keeps the assessment incomplete instead of counting as a failed learner test.

The tests cover ordinary, direct-recursive and mutually recursive Python calls; nested/method limitations; contradictory concept evidence; source-dependent static feedback; required-concept handoff; all functional failure categories; deep AST limits for Python/C/Java; and unsupported dependency classification. Functional outcome tests use explicitly identified runner doubles and are contract evidence only. No submitted program was executed on the host, and real worker acceptance remains a separate gate.

The API lifecycle/privacy suite completed with **46 passed, 0 failed**:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_evaluation_recovery_and_privacy.py tests/test_api_and_persistence.py tests/test_two_agent_end_to_end.py -q
```

This verifies that assignment concepts reach both agents from the immutable submission snapshot after a teacher edit; unexpected analysis/persistence failures release the evaluation lease, expose a sanitized retry response, and stop at the configured attempt bound; recovery and replay preserve one canonical report. Student reports remove worker streams, hidden expected outputs/reference source, and nested teacher explanations at the response boundary while preserving canonical `input` concept evidence and teacher access to the original record.

