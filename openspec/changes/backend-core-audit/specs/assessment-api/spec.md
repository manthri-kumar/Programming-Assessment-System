# Assessment API

## Purpose

Provide a bounded, documented backend interface for program assessment with explicit evidence and failure outcomes.

## ADDED Requirements

### Requirement: Validate assessment requests
The backend SHALL accept only documented Python, C and Java assessment requests containing source, reference, a supported policy and nonempty uniquely identified tests with positive finite weights. It SHALL reject unsupported inputs before submission execution.

#### Scenario: Invalid payload
- **WHEN** language or policy is unsupported, tests are empty, IDs repeat, a concept is unknown, or a weight is zero, negative or nonfinite
- **THEN** POST /assessments returns 422 with field-level errors and executes no submission

#### Scenario: Payload bounds
- **WHEN** either source exceeds 64 KiB UTF-8, test count exceeds 50, a test input/expected output exceeds 64 KiB, or body exceeds 8 MiB
- **THEN** the request is rejected with a documented validation error before execution

### Requirement: Return traceable assessment outcomes
The backend SHALL return versioned structured results including component statuses and nullable scores, per-test outcomes, evidence, policy arithmetic, feedback and recommendations. Student-caused syntax or test failures SHALL be represented as assessment outcomes rather than internal server errors.

#### Scenario: Gradable submission
- **WHEN** a supported request completes all required assessment stages
- **THEN** POST /assessments returns 200 with total, category, component scores, per-test outcomes and evidence provenance

#### Scenario: Invalid student syntax
- **WHEN** a supported submission fails syntax validation
- **THEN** the response is 200 with invalid_submission status, diagnostics, syntax score zero, null total/category and explicit unavailable stages

### Requirement: Expose operational readiness and contract
The backend SHALL publish its API schema and support matrix, distinguish GET /health liveness from GET /ready operational readiness, and return sanitized 503 or 500 errors for unavailable dependencies or unexpected internal failures respectively.

#### Scenario: Missing execution backend
- **WHEN** isolation or a required toolchain is unavailable
- **THEN** /health remains live, /ready returns 503 with the dependency reason, and assessment returns 503 without host execution

#### Scenario: Contract conformance
- **WHEN** a client reads the published schema
- **THEN** supported languages, limits, response fields, statuses and error examples agree with executable API contract tests

## Inputs and outputs
Inputs are bounded JSON requests; outputs are versioned assessment results, readiness reports and stable error envelopes.

## Expected behavior
Valid requests produce traceable outcomes; student failures are results and infrastructure failures are explicit service errors.

## Edge cases and failure handling
Oversize, duplicate, unsupported and unavailable requests are rejected before execution with sanitized details.

## Acceptance criteria
OpenAPI contract tests cover all endpoints, status codes, bounds and response schemas.

## Dependencies
Depends on `backend-architecture`, `agent-interfaces`, `evaluation-agent`, `observability`.
