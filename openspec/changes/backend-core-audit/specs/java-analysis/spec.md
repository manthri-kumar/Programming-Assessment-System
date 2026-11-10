# Java Analysis

## Purpose and scope
Analyze Java 17 single-file `Main.java` programs using the standard library only.

## ADDED Requirements
### Requirement: Enforce Java project boundary
The analyzer SHALL accept only one `Main.java` with class `Main` and SHALL reject multi-file or external dependency layouts.
#### Scenario: Unsupported layout
- **GIVEN** multiple source files or a Maven dependency
- **WHEN** analysis runs
- **THEN** it returns an unsupported-layout diagnostic before compilation.

### Requirement: Return authoritative diagnostics
Java compiler exit status and bounded diagnostics SHALL determine syntax status.
#### Scenario: Valid Java
- **GIVEN** a valid Main.java program
- **WHEN** the pinned JDK is available in isolation
- **THEN** syntax succeeds and IR evidence is returned.

## Inputs and outputs
Input is bounded Java source and pinned JDK configuration. Output is diagnostics, IR and toolchain evidence.

## Expected behavior
No Java source is executed outside the isolated worker.

## Edge cases and failure handling
Missing JDK, compiler timeout, class-name mismatch and memory limits are explicit infrastructure or validation failures.

## Acceptance criteria
Valid, malformed, class-mismatch and unsupported-layout fixtures are reproducible.

## Test scenarios
Repeated parsing and compiler failure classification are deterministic.

## Dependencies
Depends on `program-analysis`, `normalized-ir`, `isolated-execution`.
