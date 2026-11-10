# Academic Assessment Workflow

## Purpose and scope
Provide the authenticated teacher/student resource lifecycle required to use the two-agent assessment backend while protecting reference solutions, hidden tests, rubrics, submissions, and reports.

## ADDED Requirements

### Requirement: Authenticate users without granting roles by assertion
The backend SHALL hash passwords, issue expiring signed tokens, derive authorization from the stored user record, and require a server-configured invitation code for teacher self-registration.

#### Scenario: Teacher registration authorization
- **GIVEN** teacher registration is configured
- **WHEN** a caller omits or supplies an incorrect invitation code
- **THEN** registration is rejected without creating a teacher account

#### Scenario: Expired or altered token
- **WHEN** a token is expired or its signature is altered
- **THEN** the API returns 401 and reveals no protected resource

### Requirement: Enforce assignment ownership and hidden-data policy
Teachers SHALL create and update only their assignments. Only the owning teacher SHALL receive a reference solution, hidden tests, or full rubric. Students SHALL receive public assignment fields only.

#### Scenario: Cross-teacher hidden-data access
- **GIVEN** two teacher accounts and an assignment owned by the first
- **WHEN** the second teacher reads, updates, evaluates, or lists submissions for it
- **THEN** the operation is rejected or returned data is public-only, and hidden fields are absent

### Requirement: Validate configurable rubrics and test cases
An assignment rubric SHALL use `core-v1` and may specify structure, syntax, tests, and originality weights that are finite, nonnegative, and sum to one. Test IDs SHALL be unique and all test cases SHALL satisfy assessment request limits.

#### Scenario: Custom rubric is evaluated
- **GIVEN** an owner stores a valid custom rubric
- **WHEN** an authorized submission is evaluated
- **THEN** the stored weights are passed to `ImplementationEvaluationAgent` and appear in score evidence

#### Scenario: Invalid rubric or duplicate tests
- **WHEN** a weight is nonfinite, negative, incomplete, does not sum to one, or test IDs repeat
- **THEN** the request returns 422 and no assignment mutation occurs

### Requirement: Provide role-scoped histories and reports
Students SHALL list and read only their submissions and persisted reports. Teachers SHALL list submissions and reports only for assignments they own. List endpoints SHALL enforce bounded pagination.

#### Scenario: Student history isolation
- **GIVEN** submissions from two students
- **WHEN** one student requests submission history
- **THEN** only that student's records are returned and no hidden assignment data is included

### Requirement: Derive analytics and progress from persisted evidence
Teacher analytics SHALL summarize submissions and completed scores only for owned assignments. Student progress SHALL summarize only the authenticated student's persisted evaluations, preserving null scores for incomplete assessments.

#### Scenario: Incomplete evaluations
- **WHEN** analytics include an evaluation with a null total
- **THEN** it contributes to status counts but not the average score

## Inputs and outputs
Inputs are bounded authentication, assignment, rubric, test, submission, and pagination values. Outputs are client-safe JSON resources, reports, and aggregate counts.

## Expected behavior
The API provides a complete backend workflow while the assessment itself continues through exactly `ImplementationEvaluationAgent` followed by `FeedbackAgent`.

## Edge cases and failure handling
Duplicate email, invalid credentials, stale tokens, unknown resources, cross-role access, cross-owner access, invalid weights, duplicate cases, and unavailable execution produce stable sanitized errors. Mutations are transactional.

## Acceptance criteria
API and repository tests cover teacher/student registration and login, assignment create/update/read, hidden-data isolation, custom rubric propagation, submission history, report access, analytics, progress, pagination bounds, and cross-user rejection.

## Test scenarios
Tests cover successful and rejected role flows, two-teacher isolation, two-student isolation, invalid rubric rollback, incomplete evaluation aggregation, expired tokens, and OpenAPI publication.

## Dependencies
Depends on `assessment-api`, `persistence`, `rubric-scoring`, `observability`, and the exactly-two-agent architecture.
