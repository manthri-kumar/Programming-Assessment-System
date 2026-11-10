# Error Handling, Logging and Orchestration

## Purpose and scope
Make agent execution diagnosable, bounded and safe while keeping client errors separate from internal details.

## ADDED Requirements
### Requirement: Use stable error taxonomy
The backend SHALL distinguish validation, unsupported, learner, limit, infrastructure and internal errors with stable codes.
#### Scenario: Sanitized internal error
- **GIVEN** an unexpected exception
- **WHEN** the API responds
- **THEN** the client receives a request ID and sanitized code while sensitive trace details remain server-side.

### Requirement: Correlate agent execution
Every stage SHALL log correlation ID, agent/version, status, duration and evidence IDs without source secrets or raw credentials.
#### Scenario: Agent timeout
- **GIVEN** an agent exceeds its budget
- **WHEN** orchestration cancels it
- **THEN** descendants are stopped, the stage is marked limited, and the correlation record is complete.

## Inputs and outputs
Input is stage context and configuration; output is structured logs, error responses and orchestration traces.

## Expected behavior
Logs are bounded, structured and deterministic apart from explicitly operational fields.

## Edge cases and failure handling
Logging failure must not expose source or prevent cleanup; orchestration cycles are rejected.

## Acceptance criteria
Error mapping, redaction, correlation and cancellation tests pass.

## Test scenarios
Validation, learner error, timeout, infrastructure failure and internal exception scenarios are mandatory.

## Dependencies
Depends on `agent-interfaces`, `evaluation-agent`, `persistence`, `assessment-api`.
