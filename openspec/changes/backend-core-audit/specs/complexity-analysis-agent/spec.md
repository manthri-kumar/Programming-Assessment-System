# Complexity Analysis Service

## Purpose and scope
Estimate bounded static and observed complexity inside ImplementationEvaluationAgent without presenting it as a universal performance proof.

## ADDED Requirements
### Requirement: Report explainable complexity evidence
The service SHALL report configured static indicators such as loop nesting, recursion and IR size with metric version and source evidence.
#### Scenario: Nested loops
- **GIVEN** a program with nested loops
- **WHEN** complexity analysis runs
- **THEN** nesting evidence is reported deterministically with locations.

## Inputs and outputs
Input is normalized IR and optional bounded test telemetry; output is indicators, warnings and evidence.

## Expected behavior
Complexity is a separate component and does not silently alter correctness scores.

## Edge cases and failure handling
Dynamic behavior unavailable, oversized IR and instrumentation failure are explicit limitations.

## Acceptance criteria
Static indicators are stable and documented as estimates.

## Test scenarios
Linear, nested-loop, recursive and unknown-construct fixtures are tested.

## Dependencies
Depends on `normalized-ir`, `test-execution-agent`, `agent-interfaces`.
