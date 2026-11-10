# Concept Learning

## Purpose

Connect assessment evidence to an actual concept and prerequisite graph to provide reproducible, explainable learning recommendations.

## ADDED Requirements

### Requirement: Validate a versioned concept graph
The system SHALL load a versioned graph with unique concept IDs, labels, learning guidance and typed requires/related-to edges. Edge endpoints SHALL exist and the requires subgraph SHALL be acyclic. Invalid graph data SHALL prevent ready status.

#### Scenario: Cycle or dangling edge
- **WHEN** graph loading finds a prerequisite cycle, duplicate ID or unknown edge endpoint
- **THEN** validation reports the offending IDs and the backend is not ready to assess

### Requirement: Link recommendations to observed evidence
Recommendations SHALL reference triggering diagnostics or failed tests, known concept IDs, graph version and traversed prerequisite paths. A test-to-concept association SHALL NOT by itself be presented as proof of overall learner mastery or lack of mastery.

#### Scenario: Zero-division test failure
- **WHEN** a failed test is labeled with the zero-division-guard concept
- **THEN** guidance references that test and concept, explains relevant prerequisite paths and limits the conclusion to the observed task

#### Scenario: No concept evidence
- **WHEN** a failure has no justified concept association
- **THEN** feedback reports the failure without inventing a concept diagnosis

### Requirement: Order guidance through prerequisite traversal
The system SHALL recommend evidenced weak concepts and their unmet prerequisite ancestors in prerequisite-first order, deduplicated with ties resolved by concept ID. Unknown prerequisite mastery SHALL be explicit, and only documented successful evidence SHALL mark a prerequisite satisfied.

#### Scenario: Shared prerequisite
- **WHEN** two weak concepts share an unmet prerequisite
- **THEN** the prerequisite appears once before both concepts with evidence paths preserved

#### Scenario: Stable order and satisfied prerequisite
- **WHEN** identical evidence is processed twice and one prerequisite has sufficient successful evidence
- **THEN** the same ordered recommendations are returned both times and that satisfied prerequisite is not recommended as unmet

## Inputs and outputs
Inputs are graph data, evidence and mastery observations; outputs are validated paths and recommendations.

## Expected behavior
Recommendations are deterministic, prerequisite-first and limited to observed task evidence.

## Edge cases and failure handling
Unknown concepts, cycles, dangling edges and missing graph data prevent invented guidance.

## Acceptance criteria
Graph integrity, path ordering and evidence linkage fixtures pass.

## Dependencies
Depends on `knowledge-graph`, `concept-analysis-agent`, `learning-recommendation-agent`.
