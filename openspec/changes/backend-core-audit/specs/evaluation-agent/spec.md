# ImplementationEvaluationAgent

## Purpose and scope

Coordinate internal code-analysis, secure-execution, and scoring services and produce one typed evaluation result for FeedbackAgent.

## ADDED Requirements

### Requirement: Orchestrate internal evaluation services in dependency order
The ImplementationEvaluationAgent SHALL run preprocessing, syntax, concept detection, structure, complexity, secure execution, and scoring services in a declared order with immutable evidence lineage. These services SHALL not be registered as top-level agents.

#### Scenario: Syntax failure
- **GIVEN** learner syntax failure
- **WHEN** Agent 1 runs
- **THEN** dependent internal stages are skipped, syntax is zero, secure execution is not invoked, and total/category are null

### Requirement: Produce one typed evaluation result
The agent SHALL return evaluation status, rubric components, nullable total/category, test outcomes, concept findings, structural and complexity evidence, internal-stage results, versions, lineage, and limitations in one immutable result.

#### Scenario: Evaluation completion
- **GIVEN** all mandatory evidence is available
- **WHEN** scoring completes
- **THEN** the single result contains every input FeedbackAgent needs without rerunning an internal stage

### Requirement: Use versioned configurable rubrics
The agent SHALL load approved rubric weights and SHALL reject unknown or invalid policies without silently renormalizing missing components.

#### Scenario: Missing component evidence
- **GIVEN** a required component is unavailable
- **WHEN** scoring composes the result
- **THEN** total/category are null and the limitation remains traceable

## Inputs and outputs

Input is immutable assessment context plus internal service dependencies. Output is one typed traceable implementation-evaluation result.

## Expected behavior

Student failures remain gradable outcomes; infrastructure failures remain incomplete outcomes. Static concept/complexity evidence does not silently alter rubric weights.

## Edge cases and failure handling

Cancellation, contradictory evidence, duplicate evidence, timeouts, analysis limits, policy errors, and unavailable isolation are explicit.

## Acceptance criteria

Internal-stage order, failure propagation, policy arithmetic, one-result completeness, fail-closed execution, and repeated-run equality pass.

## Test scenarios

Complete, syntax-failed, test-failed, partially correct, unavailable-runner, alternate algorithm, complexity-limit, contradiction, and cancellation cases are covered.

## Dependencies

Depends on language analysis, normalized IR, structural comparison, complexity analysis, isolated execution, rubric scoring, persistence, and observability capabilities.
