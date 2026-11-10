# Spec Delta

## Purpose

Defines verifiable security and privacy protections for academic identities, grading material, student submissions, isolated execution, and operational evidence.

## ADDED Requirements

### Requirement: Authentication and authorization assurance
Every protected operation SHALL authenticate the caller and enforce role, ownership, enrollment, institution, and assignment scope as applicable.

#### Scenario: Expired session
- **WHEN** a request uses an expired or altered credential
- **THEN** access is denied without performing the protected mutation

#### Scenario: Horizontal access attempt
- **WHEN** a user requests another user's protected submission or report
- **THEN** access is denied and confidential content is not returned

### Requirement: Grading-material confidentiality
Hidden tests, expected outputs, reference source, worker secrets, and private rubric configuration SHALL remain server-side and SHALL be filtered from unauthorized responses, logs, containers, and diagnostics.

#### Scenario: Student receives feedback
- **WHEN** a student receives a failed-test explanation
- **THEN** it describes the observed category without revealing hidden input, expected output, or reference implementation

### Requirement: Verified isolation claims
The system SHALL treat network, filesystem, process, resource, cleanup, and concurrency isolation as unverified until the approved real-worker security suite passes on the recorded image and policy digests.

#### Scenario: Security suite has not run
- **WHEN** only fake-engine or contract tests exist
- **THEN** documentation and readiness state remain BLOCKED for real execution acceptance

#### Scenario: Security control fails
- **WHEN** any mandatory containment, limit, authentication, or cleanup check fails
- **THEN** worker readiness fails closed and no weaker fallback is enabled

### Requirement: Secrets and log minimization
The application SHALL NOT log passwords, bearer tokens, private keys, full student source, reference source, hidden expected outputs, or unbounded worker output.

#### Scenario: Unexpected exception
- **WHEN** a request fails internally
- **THEN** the client receives a correlated sanitized error and logs contain only allowlisted metadata

### Requirement: Abuse controls
Authentication and assessment endpoints SHALL enforce documented request bounds and role-appropriate rate limits without changing valid authorization decisions.

#### Scenario: Rate limit exceeded
- **WHEN** a caller exceeds the configured bounded request rate
- **THEN** the request is rejected with a stable retryable error and no assessment job is created

### Requirement: Retention and privacy controls
Retention periods, redaction, deletion authority, backup scope, and recovery procedures SHALL be documented and testable for student, submission, report, audit, and worker metadata.

#### Scenario: Retention expires
- **WHEN** an authorized retention job processes eligible records
- **THEN** configured sensitive content is redacted or deleted while required audit metadata remains bounded and policy-compliant

### Requirement: Security review evidence
Security documentation SHALL distinguish code inspection, automated contract tests, real containment tests, dependency scanning, and unresolved risks.

#### Scenario: Readiness report
- **WHEN** university readiness is assessed
- **THEN** each security claim links to dated reproducible evidence or is marked PARTIALLY VERIFIED, BLOCKED, or NOT IMPLEMENTED
