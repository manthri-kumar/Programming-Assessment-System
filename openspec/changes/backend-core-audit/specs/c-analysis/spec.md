# C Analysis

## Purpose and scope
Analyze one C11 translation unit with standard headers and authoritative Clang diagnostics inside the approved worker.

## ADDED Requirements
### Requirement: Analyze C without lexical guessing
The analyzer SHALL use a bounded parser/compiler result and SHALL not treat comment or string keywords as syntax structure.
#### Scenario: Keyword text
- **GIVEN** a comment containing `for` and `if`
- **WHEN** structural analysis runs
- **THEN** no control-flow nodes are created from that text.

### Requirement: Report compiler outcomes
The pinned Clang compiler's nonzero exit status SHALL be a syntax or toolchain result independent of diagnostic wording. The exact Clang build and image digest SHALL be reported from the inspected worker image.
#### Scenario: Missing error token
- **GIVEN** compiler failure without lowercase `error`
- **WHEN** analysis completes
- **THEN** syntax is failed, not scored as valid.

#### Scenario: Unverified Clang worker
- **GIVEN** no inspected immutable worker image with the approved Clang toolchain
- **WHEN** authoritative C11 compilation is requested
- **THEN** compiler authority is unavailable and no host compiler is invoked

## Inputs and outputs
Input is bounded C source and pinned C11 toolchain configuration. Output is diagnostics, IR and toolchain evidence.

## Expected behavior
The existing C rubric remains characterizable while the new analyzer uses structured evidence.

## Edge cases and failure handling
Preprocessor abuse, unsupported headers, compiler timeout and parser limits yield explicit statuses.

## Acceptance criteria
Teacher and student fixtures plus alternate formatting and malformed fixtures pass deterministic tests without host execution.

## Test scenarios
Compile failure, valid standard headers, comments, strings and stale artifact prevention are covered.

## Dependencies
Depends on `program-analysis`, `normalized-ir`, `test-execution-agent`, `isolated-execution`.
