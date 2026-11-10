# Learning Visualization

## Purpose

Expose the versioned programming concept graph and assessment-linked learning evidence as an interactive, accessible visualization without inventing mastery or relationships.

## ADDED Requirements

### Requirement: Visualize the server-provided graph
The learning view SHALL render the current graph version, concept nodes, labels, guidance, and typed prerequisite relationships returned by the authenticated client-safe graph contract. Node and edge identifiers SHALL come from the server.

#### Scenario: Graph available
- **WHEN** the graph endpoint returns valid concept and prerequisite data
- **THEN** users can pan, zoom, select a node, inspect guidance, and follow prerequisite relationships

#### Scenario: Graph unavailable
- **WHEN** graph readiness or retrieval fails
- **THEN** the view shows a meaningful unavailable state and no hardcoded replacement relationships

### Requirement: Overlay only traceable learner evidence
Weak, satisfied, unknown, and contradictory indicators SHALL be derived from persisted assessment reports and SHALL link to the triggering evidence and graph version.

#### Scenario: Contradictory evidence
- **WHEN** a concept has both satisfied and weak evidence in the current report
- **THEN** the view preserves both evidence sets and emphasizes the weak state for current guidance without claiming global non-mastery

### Requirement: Present deterministic recommendation order
Recommendations SHALL preserve the backend's prerequisite-first ordering, concept IDs, paths, guidance, and evidence references. The client SHALL NOT reorder them by invented popularity or estimated mastery.

#### Scenario: Shared prerequisite
- **WHEN** multiple weak concepts share one prerequisite
- **THEN** the recommendation view displays the deduplicated prerequisite once before dependent concepts

### Requirement: Provide a non-canvas accessible representation
Every visual graph SHALL have an equivalent keyboard-accessible concept list showing relationships, status, guidance, and evidence links.

#### Scenario: Screen-reader navigation
- **WHEN** a user accesses the learning page without interacting with the graph canvas
- **THEN** all graph nodes and prerequisite relationships remain available through structured text controls
