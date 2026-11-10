# Knowledge Graph Reasoning Service

## Purpose and scope

Turn typed evaluation evidence into deterministic, task-scoped graph reasoning inside FeedbackAgent. This internal service does not infer global learner mastery and is not exposed or orchestrated as a top-level agent.

## ADDED Requirements

### Requirement: Produce typed graph reasoning evidence
The internal service SHALL validate the configured graph and classify task concepts as `weak`, `satisfied`, or `unknown` only from explicit evaluation evidence. Its result SHALL contain the graph version, stable evidence identifiers, prerequisite paths, and deterministic prerequisite-first ordering.

#### Scenario: Labelled functional evidence
- **GIVEN** passed and failed tests explicitly labelled with known concepts
- **WHEN** FeedbackAgent invokes graph reasoning
- **THEN** the service returns task-scoped satisfied and weak evidence with unmet prerequisites before target concepts

### Requirement: Keep uncertain and contradictory evidence explicit
The service SHALL preserve unknown mastery when evidence is absent and SHALL report contradictory evidence when the same concept has both satisfied and weak evidence. Weak evidence SHALL take precedence for recommendations while both evidence sets remain traceable.

#### Scenario: Contradictory concept evidence
- **GIVEN** one labelled test passes and another labelled test fails for the same concept
- **WHEN** graph reasoning runs
- **THEN** both evidence identifiers are retained and the concept is weak for current-assessment recommendations

### Requirement: Fail safely when graph reasoning is unavailable
The service SHALL return an explicit unavailable result when graph data is missing, malformed, cyclic, or references unknown concepts. It SHALL NOT invent recommendations or alter rubric scores.

#### Scenario: Invalid graph
- **GIVEN** a graph with a dangling prerequisite or cycle
- **WHEN** FeedbackAgent invokes graph reasoning
- **THEN** the result is unavailable with a sanitized diagnostic while Agent 1 scoring remains unchanged

### Requirement: Remain internal to FeedbackAgent
FeedbackAgent SHALL invoke graph reasoning after receiving Agent 1's result. The top-level orchestrator and registry SHALL not invoke or expose this service independently.

#### Scenario: Agent discovery
- **WHEN** registered agents are inspected
- **THEN** graph reasoning is absent while its structured output remains in the FeedbackAgent result and API report

## Inputs and outputs

Input is immutable context plus typed evaluation evidence. Output is an internal typed result containing graph version, weak/satisfied/unknown concepts, contradictions, paths, evidence, and task-scoped limitations.

## Expected behavior

Identical graph, context, and evaluation evidence produce identical output. Graph reasoning informs feedback and recommendations but does not mutate the approved rubric.

## Edge cases and failure handling

Unknown IDs, unlabelled tests, shared prerequisites, empty concepts, conflicting evidence, missing graph data, and invalid graphs are explicit and deterministic.

## Acceptance criteria

The graph reasoner is absent from the top-level registry; unit tests cover passed, failed, contradictory, unlabelled, invalid-graph, and shared-prerequisite evidence; FeedbackAgent integration propagates it to persistence and API output.

## Test scenarios

Prerequisite recommendations, satisfied omission, contradiction, execution unavailable, invalid graph, unknown concept, and complete report serialization are mandatory.

## Dependencies

Depends on `concept-analysis-agent`, `test-execution-agent`, `knowledge-graph`, `learning-recommendation-agent`, `feedback-agent`, `persistence`, and `assessment-api`.
