# Backend Architecture

## Purpose and scope
Define a backend-first service boundary that keeps HTTP, domain assessment, agents, persistence and execution replaceable.

## ADDED Requirements
### Requirement: Separate service layers
The backend SHALL separate API validation, orchestration, analysis, execution, scoring, graph access and persistence behind typed interfaces.
#### Scenario: Domain isolation
- **GIVEN** an assessment request
- **WHEN** the HTTP adapter invokes the domain pipeline
- **THEN** the pipeline can be tested without an HTTP server or frontend.

### Requirement: Use explicit versioned contracts
Every result SHALL identify API, parser, policy, graph and corpus versions.
#### Scenario: Version traceability
- **GIVEN** a stored assessment result
- **WHEN** it is replayed
- **THEN** the exact contract versions needed to interpret it are present.

## Inputs and outputs
Inputs are validated API commands and configuration. Outputs are typed assessment results and health/readiness reports.

## Expected behavior
The service SHALL be local-first and deterministic, with no external LLM dependency.

## Edge cases and failure handling
Missing dependencies, invalid configuration and unsupported languages SHALL produce explicit readiness or validation failures.

## Acceptance criteria
Layer contracts import without side effects; domain tests run without FastAPI, Docker or external services.

## Test scenarios
Contract tests SHALL cover dependency injection, version propagation, invalid configuration and clean shutdown.

## Dependencies
Depends on `assessment-api`, `agent-interfaces`, `persistence`, `observability` and `isolated-execution`.
