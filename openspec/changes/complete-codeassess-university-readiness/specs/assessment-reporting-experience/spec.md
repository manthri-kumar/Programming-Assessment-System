# Spec Delta

## Purpose

Defines accessible student and teacher assessment reports that turn structured evidence into useful explanations without exposing confidential grading data.

## ADDED Requirements

### Requirement: Action-oriented report hierarchy
Reports SHALL present overview, score status, rubric, agent summary, strengths, issues, causes, graph insights, improvements, learning path, submitted code, and expandable technical evidence when data exists.

#### Scenario: Complete assessment
- **WHEN** a complete assessment report is loaded
- **THEN** populated sections appear in the defined learning-oriented order and link findings to evidence

#### Scenario: Section has no evidence
- **WHEN** a report has no content for an optional section
- **THEN** the interface omits the empty panel or presents a concise meaningful unavailable state

### Requirement: Honest incomplete reports
An incomplete report SHALL distinguish verified static findings from unavailable functional evidence and SHALL not display a fabricated score, test pass, or success status.

#### Scenario: Execution unavailable
- **WHEN** isolated execution did not occur
- **THEN** the report shows a prominent unavailable status, null score, static findings, limitations, and recovery guidance

### Requirement: Human-readable evidence
The primary report SHALL use readable diagnostics and explanations, while hashes, raw payloads, versions, and internal traces remain in labeled expandable technical details.

#### Scenario: Student reviews an issue
- **WHEN** a student opens an issue card
- **THEN** the card shows severity, explanation, source location if supported, related concepts, and a next action before internal identifiers

### Requirement: Confidentiality by role
Report APIs and views SHALL enforce assignment ownership and submission ownership and SHALL filter hidden tests, expected outputs, and reference source by audience.

#### Scenario: Unauthorized report access
- **WHEN** a different student or non-owning teacher requests a report
- **THEN** access is denied without disclosing whether confidential evidence exists

### Requirement: Responsive and accessible interaction
Report content SHALL support keyboard navigation, semantic headings, status text independent of color, reduced motion, and usable desktop, tablet, and mobile layouts.

#### Scenario: Keyboard-only review
- **WHEN** a user navigates the report without a pointing device
- **THEN** every interactive disclosure and graph-equivalent control is reachable, labeled, and operable

#### Scenario: Narrow viewport
- **WHEN** the report is displayed on a supported mobile viewport
- **THEN** content remains readable without horizontal page overflow or hidden essential actions

### Requirement: Persisted report consistency
Student and teacher dashboards SHALL derive report status, valid scores, recommendations, and progress summaries from persisted authorized assessment data.

#### Scenario: Application restart
- **WHEN** the backend restarts after an assessment was persisted
- **THEN** both authorized views reload the same report decision and evidence without regeneration drift
