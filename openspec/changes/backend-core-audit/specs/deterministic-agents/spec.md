# Deterministic Agents

## Purpose

Coordinate assessment and learning feedback through repeatable evidence-based components without external model services.

## ADDED Requirements

### Requirement: Repeat assessments without model services
The system SHALL produce identical assessment decisions, score values, diagnostic ordering and recommendation ordering for identical inputs, versions and execution outcomes. No assessment stage SHALL call external LLM APIs or require model credentials. Operational timing and request IDs are excluded from equality.

#### Scenario: Repeated assessment
- **WHEN** the same supported submission is assessed twice with identical versions and execution outcomes
- **THEN** the normalized assessment payloads match exactly without model credentials or LLM network calls

### Requirement: Preserve evidence across agent responsibilities
Evaluation and feedback components SHALL cooperate through typed results carrying stable evidence identifiers. Feedback SHALL reference actual evaluation evidence and distinguish student errors, unsupported analysis and infrastructure failures.

#### Scenario: Runtime failure feedback
- **WHEN** a test crashes with an evidence identifier
- **THEN** feedback references that test and outcome without claiming a syntax error or fabricating a diagnosis

#### Scenario: Internal stage failure
- **WHEN** a required evaluation stage fails operationally
- **THEN** downstream feedback reports the unavailable evidence and does not invent scores or completion

### Requirement: Generate actionable bounded feedback
The system SHALL provide deterministic, actionable guidance from versioned rules and available diagnostics. Text dissimilarity alone SHALL NOT produce a definitive plagiarism or misconduct verdict.

#### Scenario: Identical reference text
- **WHEN** source matches the reference exactly
- **THEN** feedback labels the similarity heuristic and its limitation without declaring misconduct

## Inputs and outputs
Inputs are immutable assessment context and upstream evidence; outputs are typed agent results and feedback.

## Expected behavior
Identical context and execution outcomes produce identical normalized decisions and evidence.

## Edge cases and failure handling
Missing evidence, cancellation and unavailable dependencies propagate explicit statuses.

## Acceptance criteria
Both top-level agents pass repeated-run equality and no-network tests, the registry exposes exactly those two agents, and internal services remain absent from the agent registry.

## Dependencies
Depends on `agent-interfaces`, `evaluation-agent`, `feedback-agent`, `observability`.
