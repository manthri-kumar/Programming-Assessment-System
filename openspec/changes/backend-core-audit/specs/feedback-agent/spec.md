# FeedbackAgent

## Purpose and scope

Consume the typed ImplementationEvaluationAgent result and coordinate explanation, Knowledge Graph reasoning, recommendations, and final report composition.

## ADDED Requirements

### Requirement: Require the typed Agent 1 result
FeedbackAgent SHALL consume the exact ImplementationEvaluationAgent result and SHALL NOT rerun parsing, scoring, or student-code execution.

#### Scenario: Evaluation handoff
- **GIVEN** a typed evaluation result from Agent 1
- **WHEN** FeedbackAgent runs
- **THEN** graph findings, feedback, recommendations, and report reference the supplied evidence lineage

### Requirement: Own the complete feedback workflow
FeedbackAgent SHALL coordinate error explanation, strength/weakness identification, Knowledge Graph reasoning, prerequisite traversal, personalized recommendations, versioned feedback templates, and `assessment-report-v2` composition.

#### Scenario: Failed labelled test
- **GIVEN** Agent 1 reports a failed test with concept labels
- **WHEN** Agent 2 runs
- **THEN** it explains the failure, records weak concepts, traverses unmet prerequisites, and emits evidence-linked recommendations in the final report

### Requirement: Reference observed evidence
Feedback SHALL cite diagnostics, failed tests, concept findings, or component evidence and SHALL not invent concepts, scores, functional success, or misconduct findings.

#### Scenario: Similarity heuristic
- **GIVEN** identical source and reference text
- **WHEN** feedback is generated
- **THEN** it labels similarity as a heuristic and gives no plagiarism verdict

### Requirement: Preserve incomplete evaluation honestly
When secure execution is unavailable, FeedbackAgent SHALL produce a complete feedback/report result describing the incomplete evaluation while leaving total/category null and functional evidence unavailable.

#### Scenario: Runner unavailable
- **GIVEN** Agent 1 returns incomplete because isolation is unavailable
- **WHEN** Agent 2 runs
- **THEN** `assessment-report-v2` contains static evidence, the unavailable limitation, and no fabricated execution outcome

## Inputs and outputs

Input is immutable context plus the typed Agent 1 result. Output is one typed feedback result containing graph reasoning, strengths, weaknesses, feedback items, recommendations, and final report.

## Expected behavior

Feedback and reports are stable, bounded, evidence-linked, and suitable for API and future UI clients.

## Edge cases and failure handling

Missing evidence yields a limitation message; unavailable graph yields no invented recommendation; contradictory concept evidence remains visible and failed evidence takes precedence for current-assessment guidance.

## Acceptance criteria

Every feedback item resolves to real evidence, the report preserves Agent 1 values, FeedbackAgent never invokes the runner, and repeated inputs produce identical output.

## Test scenarios

Syntax, runtime, structural, complexity, similarity, graph prerequisite, contradiction, infrastructure failure, and deterministic-report cases are covered.

## Dependencies

Depends on `evaluation-agent`, `knowledge-graph`, `concept-learning`, `learning-recommendation-agent`, `persistence`, and `agent-interfaces`.
