# Frontend Support Contracts

## Purpose

Define minimal additive, authenticated backend contracts required for truthful frontend behavior while preserving existing authorization, assessment, and fail-closed execution semantics.

## ADDED Requirements

### Requirement: Expose client-safe concept graph data
The backend SHALL provide an authenticated read contract containing graph version, concept IDs, labels, guidance, and typed relationships without local paths, raw configuration, or unrelated learner evidence.

#### Scenario: Student reads concept graph
- **WHEN** an authenticated student requests the graph
- **THEN** the API returns the validated public graph representation and no source code, secrets, or other students' evidence

### Requirement: Support assignment presentation metadata
Assignment contracts SHALL support bounded optional description, requirements, input/output notes, examples, constraints, concept tags, and timezone-aware deadline fields while retaining language, ownership, hidden reference/tests, and rubric rules.

#### Scenario: Student assignment detail
- **WHEN** a student reads an accessible assignment
- **THEN** presentation metadata and deadline are returned but reference source, hidden expected outputs, and rubric internals forbidden by policy remain absent

### Requirement: Persist student bookmarks safely
The backend SHALL provide authenticated idempotent list/add/remove bookmark operations scoped to the current student and existing accessible assignments.

#### Scenario: Cross-student bookmark access
- **WHEN** one student attempts to address another student's bookmark state
- **THEN** the API rejects or ignores the request without disclosing the other student's data

### Requirement: Persist bounded drafts without execution
The backend SHALL provide authenticated upsert/read/delete operations for one bounded source draft per student and assignment. Draft persistence SHALL NOT compile, evaluate, or expose source to teachers before submission.

#### Scenario: Save draft while worker unavailable
- **WHEN** a student saves a valid bounded draft and isolation is unavailable
- **THEN** the draft is stored without invoking the runner and can be restored only by that student

### Requirement: Expose truthful student activity
If activity is implemented, the backend SHALL return persisted role-scoped events generated from real assignment, submission, evaluation, report-view, draft, or bookmark actions with stable IDs and timestamps. It SHALL NOT synthesize events at read time.

#### Scenario: No events
- **WHEN** a student has no persisted activity
- **THEN** the endpoint returns an empty collection rather than sample events

### Requirement: Preserve API compatibility and error safety
Additive endpoints and fields SHALL use existing bearer authentication, stable validation/error envelopes, bounded pagination, ownership checks, redacted logging, and SQLite transactions. Existing routes and `assessment-report-v2` SHALL remain compatible.

#### Scenario: Invalid metadata
- **WHEN** a client submits oversized text, malformed deadline, unknown concept, or invalid pagination
- **THEN** the API returns a stable 4xx response without mutation or sensitive diagnostics

### Requirement: Keep unsupported domains absent
The backend SHALL NOT add contests, discussion forums, social authentication, notifications, or calendar systems solely to reproduce screenshot labels.

#### Scenario: Unsupported navigation
- **WHEN** the frontend asks whether these domains are available
- **THEN** it derives an unavailable state from documented capability configuration rather than fabricated records
