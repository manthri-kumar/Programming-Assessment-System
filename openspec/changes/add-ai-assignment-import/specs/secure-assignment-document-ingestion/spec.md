# Spec Delta

## Purpose

Defines safe, private, teacher-only ingestion and preview of untrusted assignment images and PDFs before any extraction or publication occurs.

## ADDED Requirements

### Requirement: Teacher-only document ingestion
The system SHALL allow only an authenticated teacher to create, inspect, or delete an assignment-import document owned by that teacher.

#### Scenario: Teacher uploads a supported document
- **WHEN** an authenticated teacher uploads a valid supported document
- **THEN** the system creates a private import record owned by that teacher and returns a non-guessable identifier without exposing a storage path

#### Scenario: Student attempts upload
- **WHEN** a student or unauthenticated caller invokes an import-document endpoint
- **THEN** the system rejects the request without storing the document

#### Scenario: Different teacher requests an import
- **WHEN** a teacher requests another teacher's import identifier
- **THEN** the system returns a non-disclosing not-found or forbidden response and does not reveal metadata or content

### Requirement: Supported format and signature validation
The system SHALL accept PNG, JPEG, WebP, and PDF only when the declared media type, extension where supplied, detected signature, and safe decoder agree.

#### Scenario: Valid supported image
- **WHEN** a supported image passes signature and decoding validation
- **THEN** the system accepts it and records the detected media type, byte size, and image dimensions

#### Scenario: Valid PDF
- **WHEN** a PDF passes signature, structural parsing, and page-count validation
- **THEN** the system accepts it and records its byte size and page count

#### Scenario: Spoofed or malformed content
- **WHEN** a file extension or media type claims a supported format but its signature or safe decoding disagrees or fails
- **THEN** the system rejects it with a safe validation error and removes all temporary content

#### Scenario: Active or encrypted document feature
- **WHEN** a PDF requires a password or contains an unsupported active, embedded, or malformed feature
- **THEN** the system rejects or safely ignores the unsupported content without executing it

### Requirement: Bounded document resources
The system SHALL enforce configured limits for upload bytes, PDF pages, image dimensions, decoded pixels, processing time, and concurrent ingestion before extraction begins.

#### Scenario: Oversized upload
- **WHEN** an upload exceeds the configured byte limit
- **THEN** the system stops reading, returns a payload-too-large response, and removes partial content

#### Scenario: Excessive dimensions or pages
- **WHEN** an image exceeds dimension or decoded-pixel limits or a PDF exceeds the page limit
- **THEN** the system rejects it before extraction with the violated limit identified safely

#### Scenario: Processing limit exceeded
- **WHEN** validation or decoding exceeds its time or concurrency allowance
- **THEN** the system terminates processing, reports a bounded unavailable or timeout state, and cleans temporary resources

### Requirement: Upload rate limiting and idempotency
The system SHALL rate-limit import creation per authenticated teacher and SHALL avoid duplicate processing when a valid idempotency key is replayed for identical content.

#### Scenario: Rate limit reached
- **WHEN** a teacher exceeds the configured import rate
- **THEN** the system returns HTTP 429 with bounded retry metadata and does not create an import

#### Scenario: Identical idempotent retry
- **WHEN** a teacher repeats an identical upload using the same valid idempotency key
- **THEN** the system returns the canonical import record without duplicating stored content or extraction work

#### Scenario: Conflicting idempotency replay
- **WHEN** the same idempotency key is reused with different content
- **THEN** the system rejects the conflict without replacing the original import

### Requirement: Private retention and cleanup
The system SHALL minimize document retention, isolate content by owner, record lifecycle audit events, and delete source and temporary material according to configured expiry or explicit owner deletion.

#### Scenario: Temporary processing finishes
- **WHEN** validation or extraction succeeds or fails
- **THEN** the system removes transient decode artifacts and retains only the configured private source and bounded provenance needed for review

#### Scenario: Import expires
- **WHEN** an unpublished import reaches its retention deadline
- **THEN** the system deletes source content and provider payloads, retains only the permitted audit tombstone, and makes preview unavailable

#### Scenario: Teacher deletes import
- **WHEN** the owning teacher deletes an unpublished import
- **THEN** the system removes its private source, draft, and transient provider content without deleting unrelated assignments

### Requirement: Authorized safe preview
The system SHALL provide the owning teacher a bounded preview that does not execute document content and SHALL never expose source documents through student assignment APIs.

#### Scenario: Teacher previews image
- **WHEN** the owning teacher requests an accepted image preview
- **THEN** the system returns a safe, correctly typed representation with download hardening and no executable interpretation

#### Scenario: Teacher previews PDF
- **WHEN** the owning teacher requests an accepted PDF preview
- **THEN** the system serves the original or sanitized bounded document only through the authorized import route with non-inline execution protections

#### Scenario: Student reads published assignment
- **WHEN** a student reads an assignment created from an import
- **THEN** the response excludes the source document, provider data, private provenance, reference solution, and hidden tests

### Requirement: Secure ingestion logging
The system SHALL log bounded identifiers, result categories, sizes, and timings without logging document bytes, extracted faculty content, credentials, tokens, or provider secrets.

#### Scenario: Rejected document is logged
- **WHEN** ingestion rejects a document
- **THEN** the audit record contains the owner, import identifier if allocated, safe reason code, and request identifier but no document content or secret

