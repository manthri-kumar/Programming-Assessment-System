# Teacher Assessment Experience

## Purpose

Provide teachers with an ownership-safe interface for creating assignments, configuring supported assessment inputs, reviewing submissions, and understanding real class-level results.

## ADDED Requirements

### Requirement: Render teacher-owned dashboard metrics
The teacher dashboard SHALL display only API-provided aggregates for assignments owned by the authenticated teacher, including assignment count, submission participation, status counts, and valid-score summaries.

#### Scenario: Incomplete evaluations
- **WHEN** owned submissions include incomplete evaluations with null totals
- **THEN** the dashboard retains their status counts but excludes them from score averages

### Requirement: Manage assignments through validated forms
Teachers SHALL create, view, and edit owned assignments with title, supported language, reference source, tests, concept IDs, policy version, valid rubric weights, and available descriptive/deadline metadata. Hidden fields SHALL never appear in student views.

#### Scenario: Invalid rubric total
- **WHEN** entered component weights are nonfinite, negative, or do not sum to one
- **THEN** the form blocks submission with accessible field errors consistent with backend validation

#### Scenario: Cross-owner edit
- **WHEN** the API denies editing an assignment owned by another teacher
- **THEN** the client shows a non-disclosing authorization error and does not retain protected assignment data

### Requirement: Review owned submissions and reports
Teachers SHALL list submissions only for owned assignments, inspect source and persisted evaluations, invoke evaluation where permitted, and view the same evidence-linked report without altering agent output.

#### Scenario: Evaluation infrastructure unavailable
- **WHEN** a teacher evaluates a submission while the worker is unavailable
- **THEN** the review page displays the persisted incomplete report and limitation without a fabricated score

### Requirement: Preserve two-agent semantics
Teacher-facing reports SHALL identify only ImplementationEvaluationAgent and FeedbackAgent as top-level agents. Internal analysis stages MAY be displayed as evidence sections but SHALL NOT be described as additional agents.

#### Scenario: Report stage display
- **WHEN** a teacher opens a complete report
- **THEN** top-level orchestration contains exactly two agents while internal syntax, structure, complexity, testing, graph, and reporting data remain labeled as stages or services

### Requirement: Avoid unsupported administration
The teacher client SHALL NOT expose user administration, global assignment access, production controls, worker controls, arbitrary compiler settings, or other privileges absent from the backend contract.

#### Scenario: Unsupported management feature
- **WHEN** no availability-management endpoint exists
- **THEN** assignment availability controls are omitted or labeled unavailable rather than stored only in client state
