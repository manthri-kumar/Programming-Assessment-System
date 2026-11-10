# Spec Delta

## Purpose

Defines incremental institutional ownership, enrollment, review, and reliability boundaries needed for university pilots after core grading acceptance.

## ADDED Requirements

### Requirement: Institution and course scoping
Institution, course, cohort, assignment, enrollment, submission, and report records SHALL carry explicit ownership scopes enforced on every authorized operation.

#### Scenario: Cross-institution request
- **WHEN** a user requests a resource outside their institution scope
- **THEN** access is denied without leaking protected resource data

#### Scenario: Course teacher creates assignment
- **WHEN** an authorized teacher creates an assignment within an assigned course
- **THEN** the assignment is owned by that course and visible only to permitted cohorts

### Requirement: Enrollment-based student access
Students SHALL discover and submit only to assignments available through active authorized enrollment and assignment availability rules.

#### Scenario: Enrolled student
- **WHEN** an enrolled student requests an available course assignment
- **THEN** the public assignment contract is returned without protected grading material

#### Scenario: Unenrolled student
- **WHEN** an otherwise authenticated student requests the assignment
- **THEN** access is denied

### Requirement: Audited human review
Authorized teacher review and grade adjustment SHALL preserve the immutable agent result separately from reviewer identity, reason, timestamp, and adjusted outcome.

#### Scenario: Teacher adjusts a grade
- **WHEN** the owning authorized teacher records an adjustment with a reason
- **THEN** the original score remains unchanged, the effective grade is distinguishable, and an audit event is persisted

#### Scenario: Unauthorized adjustment
- **WHEN** a student or non-owning teacher attempts an adjustment
- **THEN** the operation is denied and no grade state changes

### Requirement: Durable evaluation lifecycle
Evaluation requests SHALL have stable identities, explicit queued/running/completed/failed/cancelled states, bounded retry policy, and idempotent result persistence before institutional concurrency is claimed.

#### Scenario: Transient worker failure
- **WHEN** an eligible infrastructure failure occurs before execution evidence is accepted
- **THEN** the system applies bounded retry policy without duplicating a completed assessment

#### Scenario: Learner failure
- **WHEN** compilation, runtime, or test behavior is attributable to the submission
- **THEN** the job is not retried as infrastructure failure

### Requirement: Evidence-backed analytics
Teacher and institutional analytics SHALL use persisted authorized records, exclude null scores from score averages, and expose unavailable-assessment counts separately.

#### Scenario: Concept analytics
- **WHEN** sufficient canonical concept evidence exists for a permitted cohort
- **THEN** analytics report concept performance with counts, definitions, and limitations

#### Scenario: Insufficient evidence
- **WHEN** a metric lacks sufficient persisted evidence
- **THEN** the metric is unavailable rather than fabricated

### Requirement: Measured infrastructure decisions
PostgreSQL, durable queues, and deployment topology SHALL be selected only from documented workload, isolation, durability, and recovery requirements while local development remains supported.

#### Scenario: SQLite exceeds accepted workload
- **WHEN** reproducible load and concurrency tests violate defined acceptance thresholds
- **THEN** the architecture report records the evidence and an explicit migration decision
