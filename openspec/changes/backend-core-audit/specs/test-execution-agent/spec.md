# Secure Test Execution Service

## Purpose and scope
Compile and run untrusted programs only through the approved isolated runner as an internal ImplementationEvaluationAgent service.

## ADDED Requirements
### Requirement: Fail closed without isolation
The service SHALL refuse all compilation and execution when the approved worker is unavailable and SHALL never fall back to host subprocesses.
#### Scenario: Worker unavailable
- **GIVEN** the Linux worker is not ready
- **WHEN** execution is requested
- **THEN** no compiler or program starts and infrastructure-unavailable evidence is returned.

### Requirement: Enforce server limits
The internal execution service SHALL require the approved isolated runner to enforce compile, test, job, memory, process, scratch and output limits from server configuration.
#### Scenario: Timeout with descendants
- **GIVEN** a test spawns a child and exceeds its deadline
- **WHEN** the limit fires
- **THEN** the full process tree is terminated and the workspace is cleaned.

## Inputs and outputs
Input is bounded source, language, reference and weighted tests; output is per-case statuses, bounded streams, exit codes and cleanup evidence.

## Expected behavior
A matching output with nonzero exit status is a runtime failure.

## Edge cases and failure handling
Network, filesystem, privilege, output, memory, process and stale-artifact attempts are isolated failures.

## Acceptance criteria
Fake tests pass without execution; real security tests require a running pinned worker and zero host fallback.

## Test scenarios
Compile failure, wrong output, crash, timeout, output flood and isolation attempts are covered.

## Dependencies
Depends on `isolated-execution`, `agent-interfaces`, `observability`.
