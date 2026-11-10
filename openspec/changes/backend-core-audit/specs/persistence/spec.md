# Database Persistence

## Purpose and scope
Persist assessments, evidence, rubric versions, graph versions and benchmark metadata without coupling domain logic to one database.

## ADDED Requirements
### Requirement: Persist immutable assessment records
The persistence layer SHALL store request hash, result, versions, evidence lineage, timestamps and status with an immutable record identity.
#### Scenario: Replay record
- **GIVEN** a completed assessment record
- **WHEN** it is retrieved
- **THEN** its version metadata and evidence are sufficient for audit and replay.

### Requirement: Protect stored source and logs
Stored source, outputs and diagnostics SHALL follow configured retention and access controls and SHALL never include secrets.
#### Scenario: Retention expiry
- **GIVEN** a record past retention
- **WHEN** cleanup runs
- **THEN** source/output data is removed or irreversibly redacted while aggregate benchmark metadata remains policy-compliant.

## Inputs and outputs
Input is typed domain records; output is durable IDs, queries and migration status.

## Expected behavior
The initial implementation may use a local transactional database; repository interfaces remain portable.

## Edge cases and failure handling
Duplicate hashes, transaction failure, corruption and unavailable database produce explicit errors without losing in-flight safety state.

## Acceptance criteria
Round-trip, migration, rollback and redaction tests pass.

## Test scenarios
Concurrent IDs, failed transaction, replay and retention are tested.

## Dependencies
Depends on `backend-architecture`, `observability`, `assessment-api`.
