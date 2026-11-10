# Knowledge Graph

## Purpose and scope
Represent programming concepts, prerequisites, relationships and learning guidance as versioned local data.

## ADDED Requirements
### Requirement: Validate graph integrity
The graph SHALL enforce unique nodes, valid endpoints, typed edges and an acyclic `requires` subgraph.
#### Scenario: Cycle
- **GIVEN** prerequisite edges form a cycle
- **WHEN** the graph loads
- **THEN** readiness fails with the offending path.

### Requirement: Support deterministic traversal
Prerequisite-first traversal SHALL be stable, deduplicated and tie-broken by concept ID.
#### Scenario: Shared prerequisite
- **GIVEN** two concepts share an unmet prerequisite
- **WHEN** recommendations traverse the graph
- **THEN** the prerequisite appears once before dependents.

## Inputs and outputs
Input is versioned graph data; output is validated nodes, edges, paths and graph metadata.

## Expected behavior
Unknown mastery remains unknown unless an approved evidence rule marks it satisfied.

## Edge cases and failure handling
Missing, malformed, cyclic or dangling data prevents readiness.

## Acceptance criteria
Graph fixtures validate and reject all listed integrity failures.

## Test scenarios
Load, cycle, dangling edge, traversal and version stability tests are mandatory.

## Dependencies
Depends on `persistence`, `concept-analysis-agent`, `learning-recommendation-agent`.
