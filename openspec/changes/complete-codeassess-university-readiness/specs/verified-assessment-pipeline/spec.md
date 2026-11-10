# Spec Delta

## Purpose

Defines the observable evidence, reliability, and safety guarantees for a complete two-agent assessment from submission through persisted report.

## ADDED Requirements

### Requirement: Exactly two top-level agents
The system SHALL execute ImplementationEvaluationAgent followed by FeedbackAgent and SHALL expose internal analysis components only as services or stages.

#### Scenario: Successful orchestration
- **WHEN** an authorized assessment is requested
- **THEN** the trace contains exactly `implementation-evaluation` followed by `feedback`, and Agent 2 consumes Agent 1's typed result

#### Scenario: Agent 1 fails safely
- **WHEN** Agent 1 cannot complete a required stage
- **THEN** Agent 2 receives the incomplete evidence, explains the limitation, and does not invent missing findings or scores

### Requirement: Structured stage evidence
Each assessment stage SHALL report a stable identifier, status, diagnostics, evidence references, supported source locations, duration metadata, limitations, and failure classification.

#### Scenario: Syntax error has a location
- **WHEN** a supported parser reports a source location for a syntax error
- **THEN** the result preserves the bounded location and links it to the syntax evidence

#### Scenario: Location is unsupported
- **WHEN** a stage cannot establish a source location
- **THEN** the location remains absent and the result does not guess one

### Requirement: Functional correctness requires isolated execution
The system SHALL claim functional-test outcomes only from the approved isolated worker and SHALL fail closed when verified execution is unavailable.

#### Scenario: Worker completes a supported job
- **WHEN** the approved worker returns authenticated, policy-matching outcomes
- **THEN** Agent 1 incorporates the bounded outcomes into test evidence and rubric scoring

#### Scenario: Worker is unavailable
- **WHEN** worker configuration, authentication, toolchains, or readiness is unavailable
- **THEN** test evidence and total remain unavailable, static feedback remains provisional, and no host fallback occurs

### Requirement: Idempotent evaluation and persistence
Equivalent repeated evaluation requests SHALL return one consistent persisted assessment decision and SHALL not create conflicting reports.

#### Scenario: Duplicate request
- **WHEN** the same authorized submission and immutable assessment configuration are evaluated more than once
- **THEN** the system returns the same deterministic decision and references a single canonical evaluation record

#### Scenario: Configuration changes
- **WHEN** a teacher changes an assignment after a submission
- **THEN** the submission evaluation uses the immutable configuration version captured for that assessment or reports that versioning is unavailable

### Requirement: Core-v1 scoring compatibility
The system SHALL preserve `core-v1` structure, syntax, tests, and originality semantics, evidence, null handling, policy version, and configured weights.

#### Scenario: Criterion evidence is unavailable
- **WHEN** a required criterion cannot be measured
- **THEN** its score and total remain null and weights are not redistributed

#### Scenario: Originality is reported
- **WHEN** the similarity heuristic produces an originality component
- **THEN** the report labels it as a limited heuristic and never asserts plagiarism or misconduct

### Requirement: Authorized operational readiness
The backend SHALL expose bounded worker and evaluation readiness to authorized operators without leaking credentials, host paths, hidden tests, or reference source.

#### Scenario: Operator reads status
- **WHEN** an authorized operator requests operational status
- **THEN** the response reports readiness, policy/image/toolchain versions, queue state, and sanitized failure categories

#### Scenario: Student requests status
- **WHEN** a student requests privileged worker details
- **THEN** access is denied and no sensitive configuration is disclosed
