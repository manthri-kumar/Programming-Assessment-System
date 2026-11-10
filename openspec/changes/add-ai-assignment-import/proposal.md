# Proposal

## Why

Teachers currently enter every assignment field manually even when the source already exists as a scan, photograph, screenshot, or PDF. A secure, review-first import flow can reduce that effort while retaining the existing strict assignment contract, canonical Knowledge Graph identifiers, teacher ownership, and prohibition on unverified grading evidence.

## What Changes

- Add a teacher-only document-ingestion API for PNG, JPEG, WebP, and PDF sources with signature validation, bounded resources, rate limits, private retention, cleanup, and safe failure behavior.
- Add a provider-neutral extraction pipeline that prefers embedded PDF text, supports configured OCR/vision providers, preserves source-page provenance, and reports unavailable, ambiguous, low-confidence, or malformed input without fabricating content.
- Convert extracted material into a typed assignment-import draft compatible with the existing assignment payload while distinguishing extracted, suggested, missing, and teacher-confirmed values.
- Map concept suggestions only to canonical identifiers loaded from the existing concept graph; unmatched concepts remain unresolved for teacher selection.
- Keep extracted examples separate from generated candidate tests. Unverified generated expected outputs cannot become hidden grading tests, and reference solutions are never treated as verified merely because a provider suggested them.
- Extend the existing Create Assignment experience with Manual, Upload image/PDF, and Take photo entry modes; add preview, provenance, warnings, editing, accept/reject controls, save-draft, and explicit publish confirmation.
- Persist private import provenance and audit state separately from student-visible assignment fields, and allow imported assignments to use the existing edit workflow.
- Add unit, API, frontend, security, browser, cleanup, restart, concurrency, and provider-contract tests. Real provider acceptance remains BLOCKED unless an approved provider and credentials/runtime are available.
- Preserve exactly two top-level assessment agents, `core-v1` grading, report-v3 behavior, and fail-closed secure execution. Document import is supporting assignment-authoring infrastructure, not a third assessment agent.

## Capabilities

### New Capabilities

- `secure-assignment-document-ingestion`: Teacher-only upload, validation, storage lifetime, privacy, rate-limit, cleanup, and document-preview behavior for untrusted image/PDF sources.
- `assignment-content-extraction`: Provider-neutral text/OCR extraction, page provenance, confidence, ambiguity, structured draft generation, canonical concept mapping, and candidate-test verification state.
- `assignment-import-review`: Manual/upload/camera authoring modes, teacher comparison and correction workflow, explicit confirmation, existing assignment-contract integration, private audit provenance, and end-to-end publication behavior.

### Modified Capabilities

None. The repository has no synchronized main capability specifications; related in-flight changes remain authoritative for existing assignment validation, assessment agents, report v3, security, and university-readiness behavior and are not duplicated here.

## Impact

- Backend: additive teacher-only import endpoints, upload/extraction services, provider adapters, bounded document processing, private draft/provenance persistence, migration, audit events, rate limits, retention, and OpenAPI updates.
- Frontend: additive authoring-mode controls and an import review state integrated into the current `AssignmentFormPage`, existing concept selector, validation mapping, and black/yellow responsive design.
- Dependencies: a PDF parser and safe image decoder will require pinned project dependencies. OCR/vision remains provider-configured; no external service, credential, global tool, or privileged package is silently installed or enabled.
- Compatibility: existing manual assignment creation and assignment payloads remain supported. Student APIs never expose source documents, provider prompts/responses, hidden tests, reference solutions, or private provenance.
- Acceptance: deterministic unit tests may use provider fakes only at adapter boundaries. Claims about handwriting, OCR quality, real provider behavior, or generated-test correctness require an approved real provider and recorded evidence.
