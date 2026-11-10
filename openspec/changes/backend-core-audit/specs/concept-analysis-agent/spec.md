# Concept Analysis Service

## Purpose and scope
Map observed syntax and task metadata to graph concepts without claiming mastery. This is an internal ImplementationEvaluationAgent service, not a top-level agent.

## ADDED Requirements
### Requirement: Emit evidence-linked concepts
The service SHALL emit only configured concept IDs justified by diagnostics, test labels or explicit parser rules.
#### Scenario: Unlabeled failure
- **GIVEN** a failure without a concept mapping
- **WHEN** concept analysis runs
- **THEN** it emits no invented concept.

## Inputs and outputs
Input is analysis evidence and graph version; output is concept evidence with reason and confidence category, not unsupported numeric certainty.

## Expected behavior
Task-level evidence remains scoped to the observed assignment.

## Edge cases and failure handling
Unknown graph IDs and missing graph data produce unavailable output.

## Acceptance criteria
Zero-division guard, loop and function fixtures map reproducibly.

## Test scenarios
Mapped failure, unmapped failure and repeated ordering are covered.

## Dependencies
Depends on `knowledge-graph`, `agent-interfaces`, `program-analysis`.
