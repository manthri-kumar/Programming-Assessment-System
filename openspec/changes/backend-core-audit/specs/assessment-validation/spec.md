# Assessment Validation

## Purpose

Establish reproducible regression and empirical evaluation evidence with explicit support boundaries and honest accuracy claims.

## ADDED Requirements

### Requirement: Version independently reviewed labeled fixtures
The project SHALL maintain labeled fixtures across all supported languages with source hashes, task contracts, expected syntax/structure/test/score/concept outcomes and corpus version. Labels SHALL be reviewed independently of grader output. Held-out cases SHALL be frozen before tuning and excluded from tuning.

#### Scenario: Contradictory teacher fixture
- **WHEN** the arithmetic zero-divisor fixture is reviewed
- **THEN** the expected full output for input 5 0 is reconciled with the task and teacher source before being used as ground truth, and the correction is versioned

#### Scenario: Held-out label correction
- **WHEN** a reviewed label is found incorrect after freeze
- **THEN** the correction creates a new corpus version with rationale and does not silently rewrite a published evaluation

### Requirement: Map supported behaviors to executable tests
Every accepted specification scenario SHALL map to an automated test or explicit reproducible security check. Mandatory suites SHALL cover policy arithmetic, language parsing, API contracts, agent determinism, graph traversal, runner isolation and supported failure outcomes.

#### Scenario: Required backend acceptance
- **WHEN** backend completion is proposed
- **THEN** every mandatory supported-behavior check passes, required isolation checks run against the real runner, and skips or missing prerequisites prevent a full acceptance claim

### Requirement: Publish scoped reproducible measurements
Evaluation SHALL report exact commands, environment/toolchain/image/policy/graph/corpus versions, source hashes, case counts, failures and exclusions. It SHALL distinguish regression pass rate from empirical syntax, test, score, category and recommendation accuracy, including per-language breakdowns.

#### Scenario: Repeat benchmark
- **WHEN** evaluation runs twice on identical frozen inputs and environment
- **THEN** decisions and aggregate metrics match, excluding timing, and result artifacts identify the inputs and versions

#### Scenario: Bounded accuracy claim
- **WHEN** all mandatory supported-behavior tests pass
- **THEN** documentation states that scoped test result, publishes held-out measured outcomes separately and makes no universal grading-accuracy claim

### Requirement: Document a reproducible backend workflow
Documentation SHALL provide dependency setup, support matrix, safe runner configuration, API examples, exact test/evaluation commands and known limitations. Frontend development SHALL remain deferred until backend acceptance is recorded.

#### Scenario: Fresh environment verification
- **WHEN** a reviewer follows backend setup and verification instructions in a supported environment
- **THEN** they can reproduce the mandatory checks and labeled evaluation without external LLM credentials or frontend components

## Inputs and outputs
Inputs are frozen corpus cases and environment manifests; outputs are machine-readable metrics and human-readable limitations.

## Expected behavior
Regression pass rate and empirical accuracy are reported separately with reproducible provenance.

## Edge cases and failure handling
Missing tools, skipped cases, label changes and nondeterministic results invalidate a full acceptance claim.

## Acceptance criteria
All mandatory supported-behavior tests pass and held-out metrics are reported without universal accuracy claims.

## Dependencies
Depends on every capability spec and the pinned execution/toolchain environment.
