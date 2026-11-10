# Structural Comparison Service

## Purpose and scope
Compare normalized IR inside ImplementationEvaluationAgent while keeping structure distinct from behavioral correctness.

## ADDED Requirements
### Requirement: Produce bounded structural evidence
The service SHALL use versioned normalized IR and bounded edit comparison, returning a score only when limits and required IR are available.
#### Scenario: Alternate correct algorithm
- **GIVEN** different IR with passing behavior tests
- **WHEN** comparison runs
- **THEN** behavior remains passing and structural evidence is reported separately.

## Inputs and outputs
Input is two IR trees; output is relation, bounded score, differences and evidence IDs.

## Expected behavior
Identifier-only renaming and formatting do not reduce the score.

## Edge cases and failure handling
Missing IR, unsupported nodes and comparison limits return unavailable/limit statuses.

## Acceptance criteria
Equivalent, different and oversized IR fixtures produce stable results.

## Test scenarios
Canonical equality, insert/delete/rename and limit exhaustion are tested.

## Dependencies
Depends on `normalized-ir`, `agent-interfaces`, `rubric-scoring`.
