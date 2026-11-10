# Spec Delta

## Purpose

Defines deterministic educational feedback and Knowledge Graph recommendations grounded exclusively in traceable assessment evidence.

## ADDED Requirements

### Requirement: Structured feedback items
Every feedback item SHALL contain category, severity, explanation, evidence references, related canonical concept IDs, actionable guidance, and explicit confidence or limitation metadata.

#### Scenario: Verified functional issue
- **WHEN** isolated execution produces a failed outcome
- **THEN** feedback explains the observed behavior and impact without revealing hidden input or expected output

#### Scenario: Provisional static issue
- **WHEN** execution is unavailable but static evidence identifies a supported issue
- **THEN** feedback labels the issue provisional and distinguishes it from functional correctness

### Requirement: Overall explanation and strengths
Feedback SHALL summarize what the program appears to do, what was verified, what remains uncertain, and which implementation decisions have supporting positive evidence.

#### Scenario: Correct supported program
- **WHEN** syntax, structure, concepts, and isolated tests provide consistent positive evidence
- **THEN** feedback identifies demonstrated strengths and explains the evidence behind them

#### Scenario: Contradictory evidence
- **WHEN** analysis stages disagree
- **THEN** feedback retains the contradiction, lowers certainty, and avoids a stronger claim than the evidence supports

### Requirement: Root causes and source guidance
Feedback SHALL explain issue causes and effects and SHALL include source locations only when supplied by valid stage evidence.

#### Scenario: Located learner error
- **WHEN** a diagnostic includes a supported line and column
- **THEN** the feedback item links the location, cause, consequence, and a concrete correction step

#### Scenario: No reliable location
- **WHEN** evidence identifies an issue without a reliable location
- **THEN** guidance names the relevant construct or stage and leaves the location absent

### Requirement: Knowledge Graph reasoning
Recommendations SHALL use canonical graph nodes, task-scoped weak evidence, validated prerequisite traversal, stable ordering, and an explanation of why each concept was selected.

#### Scenario: Missing prerequisite
- **WHEN** weak evidence targets a concept with unmet prerequisites
- **THEN** recommendations list the necessary prerequisites before the target with graph paths and triggering evidence

#### Scenario: Unsupported weakness
- **WHEN** no evidence maps a failure to a graph concept
- **THEN** the system does not invent a weak concept or personalized path

### Requirement: Audience-specific explanations
The student view SHALL prioritize actionable learning guidance, while the teacher view SHALL additionally expose auditable reasoning, component evidence, limitations, and policy versions.

#### Scenario: Student feedback
- **WHEN** a student opens an authorized report
- **THEN** the response omits hidden tests, reference solutions, and confidential teacher configuration

#### Scenario: Teacher feedback
- **WHEN** the owning teacher opens the report
- **THEN** the response exposes the authorized evidence needed to review the assessment without altering the original agent result

### Requirement: Deterministic feedback
Equivalent normalized evaluation evidence, graph version, and feedback-template version SHALL produce equivalent feedback and recommendations.

#### Scenario: Repeat generation
- **WHEN** FeedbackAgent processes identical typed evidence twice
- **THEN** feedback content, ordering, concepts, and evidence links are identical apart from excluded operational metadata
