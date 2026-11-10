# Design

## Context

See `proposal.md` for motivation. The repository already has a FastAPI/SQLite backend, a strict canonical assignment contract, teacher ownership checks, a graph-backed concept selector, a React assignment form, and exactly two assessment agents. It has no multipart upload, document parser, image decoder, OCR provider, private import persistence, or import review UI. Real student execution and independent benchmark review remain blocked and must not be conflated with document extraction.

The import surface handles private faculty material and adversarial files. It must be additive, disabled safely when extraction is not configured, and must never turn an extracted or generated value into trusted grading evidence without teacher confirmation and existing validation.

## Goals / Non-Goals

**Goals:**

- Integrate secure image/PDF import into the existing assignment form and payload.
- Preserve per-field source provenance, uncertainty, teacher decisions, and private ownership.
- Provide a deterministic normalization layer around provider-specific extraction.
- Prefer local, low-data-exposure processing and permit future approved providers through one bounded interface.
- Ensure imported assignments enter the same persistence, visibility, submission, two-agent, report-v3, and dashboard flows as manual assignments.
- Make provider, worker, and independent-review limitations visible and testable.

**Non-Goals:**

- Creating another top-level agent or using document extraction to grade students.
- Automatically publishing assignments, hidden tests, reference solutions, deadlines, or unresolved concepts.
- Claiming handwriting/OCR accuracy without a real approved-provider evaluation corpus.
- Installing Tesseract, system PDF tools, GPU runtimes, privileged packages, or external credentials under this change's approval.
- Replacing the canonical assignment API, `core-v1`, report v3, or secure worker architecture.
- Completing the open institutional, worker, or human-review tasks from `complete-codeassess-university-readiness` inside this change.

## Decisions

### 1. Add a private import aggregate rather than extending assignments with untrusted workflow state

Add `assignment_imports` and `assignment_import_events` persistence with a random public identifier, teacher owner, lifecycle state, detected media metadata, content hash, storage reference, normalized extraction JSON, draft JSON, configuration hash, expiry, optional resulting assignment ID, and timestamps. The import remains private and can exist without an assignment. Confirmation calls the existing assignment creation service transactionally and links exactly one resulting assignment.

This avoids exposing provider and provenance data through current assignment serializers. Storing all import state directly on `assignments` was rejected because incomplete imports are not assignments and student-list compatibility would be harder to audit.

### 2. Keep source bytes outside the web root with database-owned metadata

Validated source bytes live under a configurable project-owned private directory using random filenames and restrictive permissions where supported. The database stores the digest and opaque storage key, never a caller path. Writes use a temporary file, size-bounded streaming hash, safe validation, atomic rename, and compensating cleanup. Expiry and owner deletion remove source and derived preview artifacts; startup reconciliation removes stale temporary files.

SQLite BLOB storage was considered but rejected because large images inflate transactions and every database backup. Object storage is deferred until institutional deployment requirements justify it.

### 3. Use layered validation with conservative initial limits

The API streams multipart data and enforces configurable limits, initially proposed as 10 MiB per upload, 20 PDF pages, 12,000 pixels per image side, 40 megapixels decoded, 30 seconds extraction wall time, and a small per-teacher concurrent-job limit. Exact defaults are configuration, documented and tested; they do not replace hard parser bounds.

Validation checks authentication before reading bodies, declared type, magic signature, file-name extension when present, safe decoder/parser results, dimensions/pages, encryption, and malformed/trailing structure. Pillow is the proposed pinned image decoder with decompression-bomb errors treated as rejection. `pypdf` is the proposed permissively licensed embedded-text parser. Neither renders or executes macros, scripts, attachments, forms, or JavaScript.

Original PDFs are never embedded inline. Review uses extracted page text and, only if an approved safe renderer is later configured, derived raster previews; the original can be downloaded by its owner as an attachment. Images are served through an authorized endpoint with `nosniff`, restrictive CSP, no-store caching, and a verified image media type.

### 4. Use a versioned extraction provider boundary

Define a provider protocol accepting bounded page/image inputs and returning schema-validated segments, regions, confidence, warnings, and typed suggestions. Provider-specific data is converted immediately to `assignment-import-extraction-v1`; unknown fields and action/tool requests are rejected.

The initial stack is:

1. Built-in embedded PDF text extraction for usable text pages.
2. A project adapter for a local Tesseract-compatible OCR executable for printed images/scans, disabled unless its absolute executable path and supported version are explicitly configured and verified.
3. No default external vision/LLM provider. A future cloud or local vision adapter requires reviewed privacy, retention, cost, credentials, version, and accuracy evidence before activation.

This local-first choice minimizes faculty-data disclosure and recurring cost. It does not promise handwriting accuracy; handwriting remains supported only when a configured provider returns sufficient confidence. Coupling directly to one cloud API was rejected because it would force vendor credentials and data transfer into the core contract. Bundling a heavyweight OCR model now was rejected because no model license, immutable provenance, resource profile, or quality benchmark has been approved.

### 5. Treat document text as data, not instructions

Provider requests use a fixed schema and fixed system policy. Document text is passed only in a delimited data field. Providers receive no database, worker, filesystem, network-tool, secret, or authorization capabilities. Responses are parsed as data into bounded models; free-form instructions cannot trigger operations. External provider payload retention is disabled or minimized where the provider supports it and must be documented before activation.

### 6. Separate extraction from deterministic draft normalization

The normalization service maps provider segments into bounded fields and preserves four states: missing, extracted, provider-suggested, and teacher-confirmed. It never supplies an absent deadline or silently chooses a language. Concept mapping uses current graph IDs plus normalized exact label/alias matching only; ambiguous matches stay unresolved. The provider may suggest candidates but cannot emit arbitrary publishable IDs.

Normalization is deterministic for the same provider result, graph version, and configuration. Canonical JSON and SHA-256 identify extraction and draft versions. This keeps the existing two assessment agents deterministic and untouched.

### 7. Model tests and reference programs with explicit trust states

Examples directly supported by source segments are stored separately from generated candidates. Each test candidate records origin, input/output provenance, verification state, and teacher decision. Only teacher-confirmed extracted cases or cases verified by the approved isolated worker can be copied into the existing hidden-test editor. Provider-generated expected outputs remain excluded until confirmed; worker unavailability is a hard verification failure, never a host fallback.

Reference code similarly records source-provided, provider-suggested, teacher-confirmed, and securely-verified states. Confirmation is necessary but does not make a program universally correct.

### 8. Add additive import endpoints and keep assignment publication canonical

Proposed API surface:

- `POST /assignment-imports` — teacher-only multipart create with idempotency key.
- `GET /assignment-imports/{id}` — owner-only state, draft, warnings, and provenance.
- `GET /assignment-imports/{id}/preview` — owner-only safe image or derived page preview.
- `POST /assignment-imports/{id}/extract` — idempotent extraction request or retry.
- `PATCH /assignment-imports/{id}/draft` — owner-only bounded teacher decisions and edits.
- `POST /assignment-imports/{id}/confirm` — owner-only explicit confirmation; calls canonical assignment validation/create and returns the one linked assignment.
- `DELETE /assignment-imports/{id}` — owner-only deletion for unpublished imports.

Extraction can run synchronously within strict bounds for the local milestone, while lifecycle states make a later queue additive. HTTP responses distinguish validation, rate limit, provider unavailable, provider failure, expiry, conflict, and canonical assignment validation. The existing `/assignments` contract stays unchanged.

### 9. Reuse `AssignmentFormPage` through an import review controller

The Create page gains mode tabs. Upload and camera capture create an import, then populate the existing form state only through an explicit review controller. Provenance badges, confidence warnings, source references, suggestion accept/reject, and candidate-test states are additive. Final confirmation sends the canonical payload through the import confirm endpoint; manual mode keeps the current direct create call.

Camera uses a normal file input with `accept="image/*"` and `capture` as the broad baseline; an optional `getUserMedia` preview is progressive enhancement, starts only after user action, stops tracks on cancel/unmount, and never uploads until confirmation. Drag/drop and all controls have equivalent keyboard paths.

### 10. Apply defense-in-depth rate limits, retention, and observability

Extend the existing configurable limiter with import-create and extraction buckets keyed by authenticated teacher. Log request ID, user ID, import ID, state transition, safe reason, sizes, page count, provider/config version, and timings. Never log bytes, extracted text, prompts, provider raw responses, source/reference code, hidden tests, tokens, or secrets.

Retention cleanup is explicit, testable, and safe across success, failure, restart, deletion, and expiry. Published assignments do not require retaining the original document; the default policy should expire it unless institutional policy explicitly requires a reviewed retention period.

### 11. Verification separates adapter tests from real-provider evidence

Unit and API tests use deterministic in-process provider fakes only to prove contracts, authorization, normalization, failure handling, and UI behavior. Parser tests use small versioned non-sensitive fixtures. Browser tests cover the complete teacher review and existing student/two-agent flow with a deterministic test adapter, clearly labeled non-provider evidence.

Real OCR/handwriting acceptance requires an approved provider/runtime, non-sensitive labeled documents, version/provenance recording, and measured results. Real candidate execution requires the separately approved isolated worker. Neither gate can be marked complete from mocks.

## Risks / Trade-offs

- [OCR quality varies by lighting, rotation, handwriting, and layout] → Preserve confidence and source comparison, require teacher confirmation, and publish measured provider-specific results only.
- [PDF/image parsers have a large attack surface] → Pin versions, reject active/encrypted/malformed features, bound resources, isolate parsing where feasible, and maintain dependency/security tests.
- [Local Tesseract is not currently provisioned and has limited handwriting quality] → Keep it disabled until separately installed and verified; manual and embedded-text flows remain available; evaluate a vision adapter only through a later reviewed decision.
- [Private faculty documents increase breach impact] → Owner isolation, no student serializers, minimal retention, private storage, content-free logs, explicit deletion, and backup documentation.
- [Synchronous extraction can occupy API workers] → Strict timeout/concurrency controls and lifecycle states; move to a durable worker only after measured demand.
- [Suggested expected outputs can silently corrupt grades] → Keep generated candidates outside hidden tests until explicit verification; preserve origin and decisions.
- [Provider output may be nondeterministic] → Persist raw normalized results, version/configuration hashes, and deterministic downstream normalization; never use extraction variability as grading evidence.
- [OneDrive or Windows filesystem semantics may weaken permission guarantees] → Document the development limitation, avoid web-root storage, verify path confinement, and require Linux deployment permission evidence for pilot readiness.

## Migration Plan

1. Add migration-safe import/event tables and private storage configuration without changing existing assignment rows.
2. Add disabled-by-default extraction configuration, parser/decoder dependencies, provider contract, and bounded ingestion endpoints.
3. Add deterministic normalization, graph mapping, draft persistence, and confirmation through existing assignment validation.
4. Add frontend modes and review UX behind an import feature flag; manual creation remains the rollback path.
5. Run backend/frontend/security/browser suites and inspect generated OpenAPI.
6. Enable embedded PDF text extraction first. Enable local OCR only after its executable/version/provenance is approved and verified.

Rollback disables the feature flag and extraction providers, expires unpublished imports, and leaves existing manual/imported assignments intact. Schema additions are retained to avoid destructive rollback.

## Open Questions

- Which qualified reviewer and non-sensitive document corpus will be used for real OCR/handwriting acceptance?
- If local Tesseract does not meet measured photo/handwriting targets, which institution-approved vision provider and data-processing terms may be evaluated in a later change?
- What institution-specific source-document retention duration is required beyond the proposed short unpublished-import default?
