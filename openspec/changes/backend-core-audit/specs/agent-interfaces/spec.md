# Agent Interfaces

## Purpose and scope

Define the deterministic contract for exactly two top-level agents and the typed internal-service boundary beneath them.

## ADDED Requirements

### Requirement: Provide a common top-level agent contract
Both top-level agents SHALL expose a typed name, version, input contract, output contract, and deterministic `run` operation.

#### Scenario: Repeat invocation
- **GIVEN** identical context, evaluation evidence, and versions
- **WHEN** either top-level agent runs twice
- **THEN** normalized outputs and evidence IDs are identical

### Requirement: Register exactly two top-level agents
The system SHALL expose exactly `ImplementationEvaluationAgent` and `FeedbackAgent` through the deterministic agent registry. Internal analysis, execution, scoring, graph, recommendation, and reporting services SHALL NOT appear as independently executable agents.

#### Scenario: Registry startup
- **WHEN** the application starts
- **THEN** the registry contains exactly the two stable names in dependency order and both satisfy the BaseAgent contract

### Requirement: Use a typed two-agent handoff
`ImplementationEvaluationAgent` SHALL return one immutable typed evaluation result. `FeedbackAgent` SHALL require that result and return one immutable typed feedback result containing the final report.

#### Scenario: Complete handoff
- **GIVEN** Agent 1 completes or returns a bounded incomplete result
- **WHEN** Agent 2 runs
- **THEN** it consumes that exact result without rerunning analysis or execution

### Requirement: Forbid external model calls
The agents and internal services SHALL not require LLM APIs, network access, or model credentials.

#### Scenario: Network-disabled execution
- **GIVEN** an assessment context
- **WHEN** both agents run
- **THEN** the result is produced from local code, configuration, and evidence only

## Inputs and outputs

Input is immutable assessment context. Outputs are typed implementation-evaluation and feedback results carrying internal-stage evidence, diagnostics, versions, and lineage.

## Expected behavior

The two agents are sequential and deterministic. Internal-service failures are explicit and are never silently converted into scores.

## Edge cases and failure handling

Missing upstream evidence, cancellation, unsupported input, and unavailable infrastructure produce typed statuses. FeedbackAgent rejects a missing or incompatible evaluation handoff.

## Acceptance criteria

The registry contains exactly two entries, both satisfy BaseAgent, Agent 2 receives Agent 1's result, and repeated/no-network tests pass.

## Test scenarios

Contract conformance, exact registry membership/order, typed handoff, dependency failure propagation, cancellation, and no-network tests are mandatory.

## Dependencies

Depends on `backend-architecture`, `observability`, and `persistence`.
