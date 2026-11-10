# Syntax Analysis Service

## Purpose and scope
Coordinate language-specific syntax parsers and diagnostics inside ImplementationEvaluationAgent.

## ADDED Requirements
### Requirement: Classify syntax and infrastructure separately
The service SHALL distinguish valid syntax, learner syntax failure, unsupported input, toolchain absence and timeout.
#### Scenario: Missing compiler
- **GIVEN** a required toolchain is unavailable
- **WHEN** syntax analysis runs
- **THEN** it returns infrastructure unavailable, never learner failure.

## Inputs and outputs
Input is language source and parser configuration; output is status, bounded diagnostics and optional IR.

## Expected behavior
No syntax result triggers source execution.

## Edge cases and failure handling
Encoding, size, parser and diagnostic-output limits are explicit.

## Acceptance criteria
Cross-language status mappings are covered by fixtures.

## Test scenarios
Valid, malformed, unsupported and unavailable toolchain cases pass.

## Dependencies
Depends on `python-analysis`, `c-analysis`, `java-analysis`, `agent-interfaces`.
