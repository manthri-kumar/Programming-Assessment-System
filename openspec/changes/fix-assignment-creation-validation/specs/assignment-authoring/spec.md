# Spec Delta

## Purpose

Defines reliable, schema-aligned assignment authoring for teachers while preserving ownership, hidden-test confidentiality, and actionable validation feedback.

## ADDED Requirements

### Requirement: Schema-aligned assignment creation
The system SHALL submit assignment data using the authoritative backend contract and SHALL preserve the existing endpoint and response compatibility.

#### Scenario: Valid assignment is created
- **WHEN** an authenticated teacher submits a title, supported language, nonblank reference program, valid rubric, valid tests, graph-known concepts, and an optional timezone-aware deadline
- **THEN** the backend returns HTTP 201 with the created assignment and persists its teacher ownership and complete private test configuration

#### Scenario: Required title is missing
- **WHEN** a teacher attempts to submit an assignment without a title
- **THEN** the form identifies the title field as required and the backend independently rejects any such request with HTTP 422

#### Scenario: Language is unsupported
- **WHEN** a request supplies a language other than Python, C, or Java
- **THEN** the backend rejects the request with HTTP 422 and the user receives a language-specific validation message

#### Scenario: Reference program is blank
- **WHEN** a teacher attempts to submit an empty or whitespace-only reference program
- **THEN** the assignment is not created and the reference-program field receives a specific validation message

### Requirement: Rubric and test validation
The system SHALL validate rubric weights and test definitions before creation, and the backend SHALL remain the final authority for the same constraints.

#### Scenario: Rubric total is invalid
- **WHEN** rubric weights are negative, non-finite, or do not total 1 within the documented tolerance
- **THEN** assignment creation is rejected and the rubric error identifies the violated constraint

#### Scenario: Test definition is invalid
- **WHEN** a test has a missing or duplicate identifier, a non-positive or non-finite weight, an oversized field, or an invalid concept identifier
- **THEN** assignment creation is rejected and the affected test field receives an actionable validation message

#### Scenario: Hidden test is valid
- **WHEN** a teacher creates an assignment containing a valid hidden test
- **THEN** the hidden test is persisted for assessment but its input, expected output, and private configuration are omitted from student-facing responses

### Requirement: Knowledge Graph-backed concepts
The assignment form SHALL use concept identifiers supplied by the backend Knowledge Graph and SHALL NOT maintain a separate hardcoded concept allowlist.

#### Scenario: Known concepts are selected
- **WHEN** the teacher selects concepts returned by the concept-graph endpoint
- **THEN** the submitted assignment uses the exact stable concept identifiers and can be created when all other fields are valid

#### Scenario: Concept becomes unknown
- **WHEN** a submitted assignment contains a concept identifier that is not present in the current graph
- **THEN** the backend returns HTTP 422 naming the unknown identifier and the form displays a safe concept-specific error without discarding other entered values

### Requirement: Safe actionable errors
The frontend SHALL translate assignment-creation failures into safe, specific messages and SHALL retain the backend's structured validation detail without exposing secrets or internal stack information.

#### Scenario: FastAPI field validation fails
- **WHEN** the backend returns HTTP 422 with structured field locations and messages
- **THEN** the form associates each safe message with the relevant input and provides an accessible summary

#### Scenario: Authorization fails
- **WHEN** an unauthenticated user or a student attempts assignment creation
- **THEN** the request is rejected with HTTP 401 or 403 and no validation workaround or role escalation occurs

#### Scenario: Backend is unavailable
- **WHEN** the assignment request cannot reach the backend
- **THEN** the form reports that the server is unavailable and does not claim that an assignment was created

### Requirement: Assignment visibility and ownership
The system SHALL preserve teacher ownership while making a successfully created available assignment visible through the authorized teacher and student workflows.

#### Scenario: Teacher sees persisted assignment
- **WHEN** creation succeeds and the teacher reloads or revisits assignment management
- **THEN** the assignment is loaded from persistence and remains editable only by its owning teacher

#### Scenario: Student opens available assignment
- **WHEN** an authenticated student lists and opens an available assignment
- **THEN** the student receives the public assignment content and workspace contract without hidden tests or reference source

#### Scenario: Student submits to assignment
- **WHEN** a student submits supported source code for the available assignment
- **THEN** the two-agent assessment workflow processes and persists the report, explicitly retaining execution-unavailable limitations when an approved secure runner is unavailable

