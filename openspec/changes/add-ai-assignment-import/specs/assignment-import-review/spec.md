# Spec Delta

## Purpose

Defines the accessible teacher review and confirmation workflow that converts a private imported draft into the existing validated assignment model without automatic publication.

## ADDED Requirements

### Requirement: Three assignment authoring modes
The Create Assignment experience SHALL offer Manual, Upload image or PDF, and Take photo modes without removing or degrading the existing manual form.

#### Scenario: Teacher chooses manual mode
- **WHEN** a teacher selects Manual
- **THEN** the existing assignment form remains usable without an extraction provider or uploaded document

#### Scenario: Teacher chooses upload mode
- **WHEN** a teacher selects Upload image or PDF
- **THEN** the interface offers an accessible file picker and drag-and-drop target for supported formats

#### Scenario: Teacher chooses photo mode
- **WHEN** a supported browser and device expose camera capture
- **THEN** the interface permits image capture only after user action and browser permission

#### Scenario: Camera is unavailable or denied
- **WHEN** camera capability is absent or permission is denied
- **THEN** the interface explains the limitation and preserves manual and file-upload alternatives

### Requirement: Import status and recoverable errors
The interface SHALL show distinct validating, extracting, review-ready, unavailable, failed, and expired states with safe recovery actions.

#### Scenario: Extraction is processing
- **WHEN** an accepted document is being extracted
- **THEN** the teacher sees progress status, can leave safely, and cannot publish incomplete results

#### Scenario: Provider is unavailable
- **WHEN** extraction reports unavailable
- **THEN** the teacher sees a specific message and may retry within policy, replace the document, or continue manually

#### Scenario: Input is invalid
- **WHEN** validation rejects size, type, signature, dimensions, pages, or malformed content
- **THEN** the interface displays the specific safe field error and does not show a false draft

### Requirement: Original-to-draft comparison
The review experience SHALL let the owning teacher preview the original document beside or near extracted fields and navigate available source references.

#### Scenario: Teacher reviews a populated field
- **WHEN** the teacher selects a field with source provenance
- **THEN** the interface identifies the supporting page or region and distinguishes extracted text from provider suggestions

#### Scenario: Small viewport
- **WHEN** the review is used on a mobile or narrow viewport
- **THEN** original and draft views remain keyboard-accessible without page-level horizontal overflow

### Requirement: Editable and rejectable suggestions
The teacher SHALL be able to edit every assignment field, accept or reject each provider suggestion, resolve missing fields, and inspect confidence warnings before confirmation.

#### Scenario: Teacher rejects a suggestion
- **WHEN** the teacher rejects a suggested rubric, concept, test, or reference source
- **THEN** the value is removed from the publishable draft while its rejection remains in private audit history

#### Scenario: Teacher corrects OCR
- **WHEN** the teacher edits incorrect extracted text
- **THEN** the corrected value becomes teacher-confirmed and is submitted through existing field validation

#### Scenario: Required ambiguity remains
- **WHEN** language, title, reference source, tests, concepts, or other required contract data remains invalid or unresolved
- **THEN** publication is blocked with field-level guidance

### Requirement: Canonical concept review
The review experience SHALL load the existing concept graph and use the existing searchable selector to submit only canonical graph identifiers.

#### Scenario: Teacher resolves unmatched concept
- **WHEN** extraction yields an unmatched concept label
- **THEN** the teacher can search readable graph names and select the exact canonical identifier

#### Scenario: Concept graph is unavailable
- **WHEN** the concept graph cannot be loaded
- **THEN** save or publication that could submit unvalidated concept identifiers fails closed

### Requirement: Test and reference review safeguards
The interface SHALL show origin and verification state for reference source, examples, and test cases and SHALL prevent unverified generated expected outputs from becoming hidden grading tests.

#### Scenario: Generated test is unverified
- **WHEN** a generated candidate has not been securely or manually verified
- **THEN** it remains outside the publishable hidden-test list and is visibly marked unverified

#### Scenario: Teacher verifies extracted test manually
- **WHEN** the teacher reviews and explicitly confirms an extracted case and expected output
- **THEN** the case may enter the existing hidden-test editor and remains subject to canonical validation

#### Scenario: Worker verifies candidate
- **WHEN** an approved isolated worker verifies a candidate against a teacher-confirmed reference source
- **THEN** the review records bounded verification evidence without exposing worker secrets or making a universal correctness claim

### Requirement: Save private import draft
The system SHALL allow the owning teacher to save an incomplete import draft without creating a student-visible assignment.

#### Scenario: Teacher saves review progress
- **WHEN** the teacher saves an incomplete import draft
- **THEN** its fields, provenance decisions, warnings, and owner are persisted privately and can be resumed by that teacher

#### Scenario: Application restarts
- **WHEN** the application restarts after a draft was transactionally saved
- **THEN** the owning teacher can resume the same draft without publishing it or duplicating an assignment

### Requirement: Explicit confirmation and existing validation
The system SHALL require explicit teacher confirmation and SHALL pass the confirmed payload through the existing strict assignment creation or update validation before publication.

#### Scenario: Teacher confirms valid draft
- **WHEN** the teacher confirms a complete draft whose canonical payload passes existing validation
- **THEN** exactly one assignment is persisted using the existing assignment model and ownership rules

#### Scenario: Existing validation rejects payload
- **WHEN** the confirmed payload contains invalid language, rubric, tests, reference source, deadline, or concept identifiers
- **THEN** publication fails with field-level errors and the private draft remains available for correction

#### Scenario: No confirmation
- **WHEN** extraction completes but the teacher does not confirm publication
- **THEN** no student-visible assignment is created

#### Scenario: Duplicate confirmation request
- **WHEN** a successful confirmation request is safely retried with the same idempotency key
- **THEN** the system returns the canonical assignment and does not create a duplicate

### Requirement: Imported assignment compatibility
An assignment created from an import SHALL behave like a manually created assignment in editing, visibility, submission, assessment, report, and dashboard workflows.

#### Scenario: Teacher edits imported assignment
- **WHEN** the owning teacher edits a published imported assignment
- **THEN** existing update validation, ownership, hidden-data protection, and historical submission snapshots apply unchanged

#### Scenario: Student completes imported assignment
- **WHEN** an eligible student submits code for the imported assignment
- **THEN** the existing `ImplementationEvaluationAgent` then `FeedbackAgent` workflow produces and persists report v3 subject to the same execution limitations as manual assignments

### Requirement: Private provenance and student redaction
The system SHALL retain bounded import provenance for teacher review and audit while excluding it from student-visible assignment, submission, report, and dashboard responses.

#### Scenario: Owning teacher views provenance
- **WHEN** the owning teacher opens an imported assignment's authorized provenance view
- **THEN** the system returns bounded field origins, decisions, provider/configuration identifiers, and source references without secrets

#### Scenario: Student views imported assignment
- **WHEN** a student views the assignment or report
- **THEN** the system returns only normal student-visible assignment and assessment fields

### Requirement: Accessible responsive review
The import and review controls SHALL meet the existing keyboard, focus, label, contrast, error-announcement, and responsive-layout expectations.

#### Scenario: Keyboard-only review
- **WHEN** a teacher completes import review using a keyboard
- **THEN** all modes, preview navigation, accept/reject actions, fields, errors, and confirmation are reachable with visible focus and meaningful labels

#### Scenario: Error announcement
- **WHEN** upload, extraction, or validation fails
- **THEN** the error is associated with the affected control and announced without exposing sensitive provider details

