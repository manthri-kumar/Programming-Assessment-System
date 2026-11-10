# Python Analysis

## Purpose and scope
Analyze the supported Python subset using Python 3.11 standard-library syntax and AST evidence.

## ADDED Requirements
### Requirement: Parse Python safely
The analyzer SHALL parse Python source with `ast` and SHALL report locations for syntax errors without importing or executing the source.
#### Scenario: Malformed source
- **GIVEN** malformed Python
- **WHEN** syntax analysis runs
- **THEN** it returns a learner syntax diagnostic and performs no import or execution.

### Requirement: Bound Python support
The analyzer SHALL reject unsupported dependency and project layouts explicitly.
#### Scenario: External import
- **GIVEN** source requiring an unavailable external package
- **WHEN** analysis requests execution-dependent evidence
- **THEN** it reports unsupported dependency evidence rather than guessing.

## Inputs and outputs
Input is bounded UTF-8 source and language configuration. Output is syntax diagnostics and normalized IR candidates.

## Expected behavior
Comments and strings SHALL not become control-flow features.

## Edge cases and failure handling
AST size/time limits yield `analysis_limit`; encoding errors yield validation errors.

## Acceptance criteria
Fixtures cover functions, loops, branches, comments, strings, malformed syntax and unsupported imports.

## Test scenarios
Repeated analysis of identical source returns identical normalized evidence.

## Dependencies
Depends on `program-analysis`, `normalized-ir`, `observability`.
