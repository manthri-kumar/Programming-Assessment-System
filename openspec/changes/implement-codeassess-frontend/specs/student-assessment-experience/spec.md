# Student Assessment Experience

## Purpose

Give authenticated students a complete workflow from discovering assigned work through secure submission, assessment evidence, feedback, progress, and learning follow-up.

## ADDED Requirements

### Requirement: Render a real-data student dashboard
The dashboard SHALL derive greeting, assignment counts, submission totals, valid completed-score average, solved count, unfinished work, deadlines, recent submissions, progress, and activity only from authenticated backend data. Every section SHALL support loading, empty, unavailable, and error states.

#### Scenario: Execution unavailable submissions
- **WHEN** recent evaluations are incomplete because the secure worker is unavailable
- **THEN** the dashboard excludes null totals from averages and labels those submissions unavailable rather than failed or accepted

#### Scenario: No activity contract
- **WHEN** the backend provides no persisted activity events
- **THEN** My Activity displays a truthful unavailable state without synthetic events or timestamps

### Requirement: Browse and inspect assignments
Students SHALL be able to list, search, and filter accessible assignments by real language, status, concept, and available metadata, open an assignment detail, and start or continue a submission.

#### Scenario: Missing difficulty metadata
- **WHEN** assignments do not expose difficulty
- **THEN** difficulty filtering and badges are omitted rather than inferred

### Requirement: Provide a secure coding workspace
The workspace SHALL support Python, C, and Java editing, assignment/test metadata, local draft recovery, submission confirmation, and backend submission/evaluation actions. It SHALL never execute source in the browser or invoke a host compiler.

#### Scenario: Worker unavailable
- **WHEN** evaluation returns the documented infrastructure-unavailable response
- **THEN** the workspace preserves the source, displays Execution Unavailable and limitations, and does not show fabricated passed tests or scores

#### Scenario: Draft recovery
- **WHEN** a student returns to an unfinished assignment with a persisted compatible draft
- **THEN** the editor restores it and clearly distinguishes unsent draft content from a submitted record

### Requirement: Present assessment reports faithfully
Result views SHALL render persisted submission metadata, status, nullable total/category, rubric components, syntax/static/structure/complexity findings, test outcomes, evidence, limitations, feedback, graph reasoning, and recommendations from `assessment-report-v2` without recomputation.

#### Scenario: Missing component evidence
- **WHEN** a report component is unavailable or null
- **THEN** the view explains its unavailable state and does not substitute zero or redistribute weights

### Requirement: Provide submissions and progress views
Students SHALL see only their own paginated submissions, sorting/filtering, report links, completed evaluations, valid score trends, status counts, and evidence-supported concept progress.

#### Scenario: Unauthorized submission URL
- **WHEN** a student requests another student's submission and the API returns 403 or 404
- **THEN** the client shows a non-disclosing access error and no cached protected record

### Requirement: Provide evidence-based learning follow-up
Learning Path and Recommended views SHALL use persisted feedback, graph paths, and recommendations. They SHALL distinguish task-scoped weak, satisfied, unknown, and contradictory evidence and SHALL NOT claim global mastery.

#### Scenario: No recommendation evidence
- **WHEN** no evaluated submission contains recommendations
- **THEN** the client presents an empty learning state rather than generic invented advice

### Requirement: Persist bookmarks only through an approved contract
Students SHALL add/remove/list assignment bookmarks through the authenticated backend contract. Until that contract is ready, bookmark controls SHALL be unavailable rather than browser-only data presented as durable server state.

#### Scenario: Bookmark mutation fails
- **WHEN** the bookmark API rejects or fails a mutation
- **THEN** the UI retains the confirmed server state and reports the failure

### Requirement: Use honest date and deadline handling
All timestamps SHALL be parsed as documented server values, rendered in the user's locale/timezone, and distinguish future, due-soon, overdue, and missing deadlines.

#### Scenario: Missing deadline
- **WHEN** an assignment has no deadline
- **THEN** the UI displays No deadline and does not calculate remaining time
