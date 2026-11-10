# Spec Delta

## Purpose

Defines truthful extraction and structured assignment-draft behavior across embedded PDF text and configured OCR or vision providers while preserving provenance and uncertainty.

## ADDED Requirements

### Requirement: Provider-neutral extraction contract
The system SHALL expose a versioned provider-neutral extraction contract whose configured implementations return bounded text segments, page references, confidence, warnings, and provider status.

#### Scenario: Configured provider succeeds
- **WHEN** a configured extraction provider processes an accepted import
- **THEN** the system stores a normalized extraction result without coupling the assignment contract to provider-specific fields

#### Scenario: No provider is configured
- **WHEN** the document requires OCR or vision and no approved provider is configured
- **THEN** the system returns an explicit extraction-unavailable state while preserving the manual authoring path

#### Scenario: Provider fails or times out
- **WHEN** the provider rejects, fails, throttles, or times out
- **THEN** the system records a safe failure category, cleans transient payloads, and does not fabricate extracted fields

### Requirement: Embedded text before OCR
The system SHALL prefer bounded embedded PDF text extraction for pages with usable text and SHALL use OCR or vision only for pages or regions that require it.

#### Scenario: Text PDF
- **WHEN** a PDF page contains usable embedded text
- **THEN** the system extracts that text with page provenance without requiring OCR for that page

#### Scenario: Mixed PDF
- **WHEN** some pages contain usable text and others contain scanned content
- **THEN** the system records the extraction method per segment and invokes the configured provider only for the required pages or regions

### Requirement: Original text and page provenance
The system SHALL preserve bounded original extracted text and associate each derived draft value with one or more source page or region references where available.

#### Scenario: Field is directly extracted
- **WHEN** a draft value is copied or normalized from document content
- **THEN** the field provenance identifies it as extracted and links to the supporting page or region and text segment

#### Scenario: Source cannot be localized
- **WHEN** a provider returns content without a reliable location
- **THEN** the system marks the location unavailable rather than inventing a page or region

### Requirement: Typed import draft
The system SHALL produce a versioned draft compatible with the existing assignment payload and containing title, description, requirements, language, input notes, output notes, constraints, examples, concepts, reference source, candidate tests, rubric suggestion, and deadline states.

#### Scenario: Complete printed question
- **WHEN** extraction identifies supported assignment fields
- **THEN** the system populates typed draft fields within existing assignment limits and attaches per-field provenance and confidence

#### Scenario: Missing information
- **WHEN** a required or useful assignment field is absent
- **THEN** the field is marked missing and remains unconfirmed rather than receiving fabricated content

#### Scenario: Ambiguous language
- **WHEN** the source does not unambiguously identify Python, C, or Java
- **THEN** the language remains unresolved and publication is blocked until the teacher selects a supported language

#### Scenario: Deadline absent
- **WHEN** the source contains no explicit deadline
- **THEN** the draft deadline remains empty and no deadline is inferred

### Requirement: Provenance categories and uncertainty
Every populated draft field SHALL be classified as extracted, provider-suggested, or teacher-confirmed, and SHALL carry bounded confidence or an explicit unknown state plus warnings where applicable.

#### Scenario: Provider infers a field
- **WHEN** a provider proposes content not directly supported by a source segment
- **THEN** the system labels it provider-suggested and requires teacher acceptance before it becomes confirmed

#### Scenario: Low-confidence handwriting
- **WHEN** handwriting or image quality produces low-confidence text
- **THEN** the system highlights the affected field and source location for teacher correction without claiming successful recognition

#### Scenario: Teacher edits a field
- **WHEN** the teacher changes or accepts a draft field
- **THEN** the draft records teacher-confirmed status while retaining the earlier extracted or suggested provenance in its private audit history

### Requirement: Canonical Knowledge Graph mapping
The system SHALL resolve concept suggestions only against the current concept graph and SHALL keep unmatched or ambiguous suggestions unresolved.

#### Scenario: Exact canonical match
- **WHEN** an extracted concept maps unambiguously to a current graph node
- **THEN** the draft contains that canonical node identifier and supporting extraction provenance

#### Scenario: Ambiguous or unknown concept
- **WHEN** a concept string has no unique canonical match
- **THEN** the system presents it as unresolved and requires selection through the existing graph-backed concept selector

#### Scenario: Graph changes before publication
- **WHEN** a previously mapped identifier no longer exists at save or publish time
- **THEN** existing strict assignment validation rejects it and the teacher must select a current canonical identifier

### Requirement: Extracted examples and candidate tests
The system SHALL keep source examples separate from provider-generated candidate tests and SHALL track expected-output verification independently for every candidate.

#### Scenario: Source contains sample input and output
- **WHEN** an input/output pair is directly present in the source
- **THEN** the system preserves both values faithfully, labels the case extracted, and links it to source provenance

#### Scenario: Provider suggests boundary case
- **WHEN** a provider proposes an additional case
- **THEN** the system labels it generated and unverified until a teacher or approved secure verification process confirms it

#### Scenario: Expected output is uncertain
- **WHEN** an expected output lacks trustworthy source or verification evidence
- **THEN** the case cannot be published as a hidden grading test

#### Scenario: Secure worker unavailable
- **WHEN** reference-based candidate verification is requested but the approved isolated worker is unavailable
- **THEN** verification fails closed, the case remains unverified, and no host execution occurs

### Requirement: Reference source verification state
The system SHALL distinguish source-provided, provider-suggested, teacher-confirmed, and securely verified reference programs and SHALL never equate suggestion with correctness.

#### Scenario: Reference program appears in document
- **WHEN** a reference program is directly extracted
- **THEN** it is labeled source-provided with location provenance and remains unverified until teacher confirmation and applicable secure validation

#### Scenario: Provider generates a solution
- **WHEN** a provider suggests a reference program
- **THEN** it is visibly marked provider-suggested and cannot silently become verified or publishable hidden evidence

### Requirement: Extraction prompt and response isolation
The system SHALL treat document content as untrusted data and SHALL prevent it from changing provider configuration, system policy, authorization, or tool permissions.

#### Scenario: Document contains instruction-like text
- **WHEN** a document contains text attempting to override extraction instructions or request secrets
- **THEN** the content remains quoted source data and cannot modify policy, access credentials, or retrieve unrelated information

#### Scenario: Provider returns unsupported actions
- **WHEN** a provider response requests tool use, network access, or code execution
- **THEN** the system rejects those fields and accepts only the bounded extraction schema

### Requirement: Deterministic normalization
For a fixed normalized provider response, graph version, and configuration, the system SHALL produce byte-equivalent canonical draft data and a stable configuration hash.

#### Scenario: Repeated normalization
- **WHEN** the same normalized extraction is processed twice with identical configuration
- **THEN** field values, provenance order, warnings, concept candidates, and configuration hash are equal

