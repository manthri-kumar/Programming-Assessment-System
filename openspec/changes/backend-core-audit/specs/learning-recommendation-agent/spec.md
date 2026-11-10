# Learning Recommendation Service

## Purpose and scope
Generate prerequisite-aware, evidence-linked learning recommendations inside FeedbackAgent.

## ADDED Requirements
### Requirement: Recommend only evidenced concepts
The service SHALL recommend observed weak concepts and unmet ancestors with triggering evidence, path and graph version.
#### Scenario: Zero-division guard
- **GIVEN** the reviewed `5 0` task fails due to missing guard behavior
- **WHEN** recommendations run
- **THEN** the guard concept and unmet prerequisites are ordered with the failed test evidence.

## Inputs and outputs
Input is concept evidence, mastery evidence and graph; output is stable ordered recommendations.

## Expected behavior
Recommendations are task-scoped and do not claim universal learner mastery.

## Edge cases and failure handling
No evidence produces no recommendation; invalid graph produces unavailable output.

## Acceptance criteria
Shared ancestors deduplicate and satisfied prerequisites are omitted.

## Test scenarios
Mapped failure, unknown mastery, shared prerequisites and repeated ordering are tested.

## Dependencies
Depends on `knowledge-graph`, `concept-analysis-agent`, `feedback-agent`.
