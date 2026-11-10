# Future Teacher and Student Frontend Contracts

## Purpose and scope
Define future client-facing contracts without implementing frontend functionality in this change.

## ADDED Requirements
### Requirement: Expose stable client-safe API schemas
Future teacher and student clients SHALL consume versioned request/result schemas, pagination and error codes without accessing internal agents or source paths.
#### Scenario: Student result view
- **GIVEN** a completed assessment
- **WHEN** a student client requests its result
- **THEN** it receives scores, evidence-linked feedback and recommendations allowed by policy, without secrets or internal traces.

### Requirement: Separate teacher capabilities
Teacher operations SHALL be explicitly authorized and separate from student result access, including task/rubric/graph management.
#### Scenario: Unauthorized rubric change
- **GIVEN** a student credential
- **WHEN** it attempts to change a rubric
- **THEN** the API rejects it without disclosing policy internals.

## Inputs and outputs
Input is future authenticated client traffic; output is documented JSON schemas and stable error codes.

## Expected behavior
No frontend or authentication implementation is part of `backend-core-audit`.

## Edge cases and failure handling
Schema version mismatch, stale result, pagination bounds and unavailable assessment are explicit errors.

## Acceptance criteria
Contract examples and compatibility rules are documented and tested at the API boundary before frontend work begins.

## Test scenarios
Student read, teacher management, unauthorized action and version mismatch are contract tests.

## Dependencies
Depends on `assessment-api`, `persistence`, `observability`; implementation requires a later approved frontend/authentication change.
