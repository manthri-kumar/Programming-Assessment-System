# Tasks

## 1. Baseline, Dependencies, and Contracts

- [x] 1.1 Reconcile this change against `backend-core-audit`, `fix-assignment-creation-validation`, `implement-codeassess-frontend`, and `complete-codeassess-university-readiness`; document ownership of overlapping agent, report-v3, worker, security, and institutional gates and verify no task or completion claim is duplicated.
- [x] 1.2 Add pinned, permissively licensed multipart, image-decoding, and PDF-text dependencies plus provenance notes; verify installation, imports, license records, `pip check`, and dependency security checks without installing global or privileged tools.
- [x] 1.3 Define versioned bounded models for import lifecycle, detected document metadata, extraction segments/regions, confidence, warnings, field provenance, candidate tests, reference-source trust, teacher decisions, and canonical drafts; verify serialization rejects unknown, oversized, non-finite, or invalid state combinations.
- [x] 1.4 Define the provider protocol, embedded-PDF provider, disabled-by-default Tesseract-compatible adapter, provider/configuration hashing, and unavailable/failure categories; verify deterministic adapter contract tests and that no external provider or executable is enabled implicitly.
- [x] 1.5 Document configuration defaults and hard limits for bytes, pages, pixels, dimensions, wall time, concurrency, retention, storage root, feature flag, and provider selection; verify unsafe or path-escaping configuration fails startup safely.

## 2. Private Persistence and Secure Ingestion

- [x] 2.1 Add migration-safe `assignment_imports` and `assignment_import_events` persistence with owner, random public ID, state, hashes, opaque storage key, bounded JSON, expiry, and optional canonical assignment linkage; verify upgrade/restart preserves existing users, assignments, submissions, and reports.
- [ ] 2.2 Implement transactional repository operations for create, owner-scoped read/update/delete, state transition, event history, idempotency, expiry, and exactly-once assignment linkage; verify concurrent and replay tests cannot cross owners or create duplicate assignments.
- [ ] 2.3 Implement path-confined private source storage with streaming size/hash enforcement, temporary-file atomic rename, restrictive-permission attempts, and compensating cleanup; verify traversal, symlink/reparse-point, interrupted-write, restart, and deletion tests.
- [ ] 2.4 Implement magic/type/extension validation and safe PNG/JPEG/WebP decoding with byte, dimension, and decoded-pixel limits; verify valid fixtures plus spoofed, truncated, decompression-bomb, malformed, oversized, and unsupported inputs.
- [ ] 2.5 Implement bounded PDF validation, encryption/active-feature rejection policy, page-count enforcement, and embedded-text extraction without executing attachments, forms, JavaScript, macros, or scripts; verify text, scan-only, mixed, encrypted, malformed, active-content, and excessive-page fixtures.
- [x] 2.6 Add teacher-only create/get/delete and safe preview endpoints with no-store, nosniff, restrictive content policy, attachment-only original PDF handling, request IDs, and non-disclosing ownership failures; verify student, unauthenticated, owning-teacher, other-teacher, expired, and missing cases.
- [x] 2.7 Extend configurable rate limits and idempotency handling for upload and extraction; verify HTTP 429 retry metadata, conflicting idempotency rejection, identical replay, and absence of partial records.
- [ ] 2.8 Implement scheduled/on-access expiry and startup temporary-file reconciliation with bounded audit tombstones; verify cleanup after success, parser failure, provider failure, timeout, explicit deletion, expiry, and application restart.
- [ ] 2.9 Add secure ingestion audit/logging and retention documentation; verify automated redaction tests exclude bytes, extracted text, source/reference code, hidden tests, prompts, raw provider responses, paths, tokens, credentials, and secrets.

## 3. Extraction and Deterministic Draft Generation

- [ ] 3.1 Implement per-page extraction orchestration that prefers usable embedded PDF text and invokes the configured OCR adapter only for required pages/images under timeout and concurrency bounds; verify text-only, image-only, mixed-page, rotation metadata, provider-unavailable, failure, throttle, and timeout cases.
- [ ] 3.2 Implement strict provider-response parsing and prompt/data isolation so document text cannot alter policy, authorization, configuration, tools, or secrets; verify prompt-injection fixtures, unknown/action fields, malformed responses, and oversized output are rejected safely.
- [x] 3.3 Implement deterministic normalized extraction and canonical hashing with stable segment, provenance, warning, and page order; verify repeated normalization is byte-equivalent for identical provider response, graph version, and configuration.
- [ ] 3.4 Implement typed field extraction for title, description, requirements, language, input/output notes, constraints, examples, reference source, tests, rubric suggestion, and deadline while preserving missing/ambiguous states; verify no absent deadline, language, output, code, or rubric value is fabricated.
- [x] 3.5 Implement exact/alias canonical concept mapping against the current graph with ambiguity and unresolved states; verify readable labels map only to valid canonical IDs and graph-version changes fail closed at publication.
- [ ] 3.6 Implement extracted-example, generated-candidate, expected-output verification, and reference-source trust states; verify generated or uncertain outputs cannot enter the hidden-test payload without explicit permitted verification.
- [ ] 3.7 Add owner-scoped extraction, retry, draft-read, and draft-patch endpoints with stable lifecycle/error responses; verify duplicate requests, invalid transitions, expired imports, provider unavailability, and teacher-confirmed provenance history.
- [x] 3.8 Publish extraction-provider, data-handling, privacy, retention, and operational setup documentation; verify all examples preserve disabled-by-default providers and contain no real faculty content or secret.

## 4. Canonical Confirmation and Assignment Integration

- [x] 4.1 Implement import confirmation through the existing strict assignment validation and repository path rather than a second assignment model; verify invalid language, rubric, reference source, tests, deadline, and concept IDs return canonical field errors while retaining the private draft.
- [ ] 4.2 Enforce exactly-once confirmation and link the import to one canonical assignment transactionally; verify concurrent confirmation and network retry return the same assignment without duplicate rows.
- [ ] 4.3 Preserve private provenance and source isolation across assignment list/detail, submission, report, dashboard, OpenAPI, logs, backup, and retention serializers; verify students and unrelated teachers cannot infer import existence or content.
- [x] 4.4 Verify imported assignments can be edited by their owner and follow existing visibility, immutable submission-snapshot, scoring, feedback, report-v3, and dashboard behavior without changing `core-v1` or adding an agent.

## 5. Teacher Authoring and Review Experience

- [x] 5.1 Add accessible Manual, Upload image/PDF, and Take photo modes to the existing Create Assignment page behind the import feature flag; verify manual creation remains behaviorally and visually compatible when import is disabled or unavailable.
- [x] 5.2 Add accessible file picker, drag/drop, upload progress, validation errors, retry/replace/delete actions, and camera capture progressive enhancement; verify denied/absent camera, track cleanup, supported formats, keyboard equivalence, and no upload before teacher action.
- [ ] 5.3 Add authorized image/PDF review presentation, page/source navigation, extraction status, confidence warnings, and original-to-field provenance links; verify desktop, tablet, mobile, loading, unavailable, failed, expired, and malformed-document states.
- [x] 5.4 Reuse the existing assignment form state and searchable graph selector for imported drafts; verify all fields remain editable and only current canonical concept IDs reach the payload.
- [ ] 5.5 Add accept/reject controls and trust badges for suggested fields, concepts, reference code, extracted examples, generated tests, and rubric suggestions; verify rejected values leave the publishable draft and unverified generated tests cannot enter hidden tests.
- [ ] 5.6 Add private save/resume and explicit publish confirmation flows with unsaved-change protection and field-level canonical errors; verify extraction alone never publishes and restart resumes the owning teacher's draft.
- [ ] 5.7 Add frontend API types/client methods, query invalidation, safe error mapping, and component tests for authorization, size/type/page/dimension limits, provider states, conflicts, expiry, and validation errors; verify TypeScript, lint, Vitest, and production build.

## 6. Integrated Verification and Documentation

- [ ] 6.1 Add backend API/security/regression coverage for ownership, malformed content, limits, injection, rate limiting, retention, cleanup, hidden-data redaction, idempotency, concurrency, restart, and migration; verify the complete backend suite passes with no host execution.
- [ ] 6.2 Add Playwright coverage for manual creation plus deterministic-adapter upload/photo review, correction, canonical concept selection, save/resume, publication, teacher edit, student visibility, and accessibility across desktop/tablet/mobile; label adapter-based browser evidence as non-provider verification.
- [x] 6.3 Run an imported-assignment workflow through student submission, `ImplementationEvaluationAgent`, `FeedbackAgent`, persistence, report v3, teacher/student redaction, recommendations, and dashboards; verify exactly two top-level agents and record worker-unavailable limitations without fabricating functional evidence.
- [x] 6.4 Refresh OpenAPI and update architecture, frontend, security, privacy, backup/recovery, agent verification, report-v3, and end-to-end documents with import behavior and exact test evidence; verify status uses VERIFIED, PARTIALLY VERIFIED, BLOCKED, and NOT IMPLEMENTED accurately.
- [ ] 6.5 Run backend tests, compilation, dependency checks, frontend tests, typecheck, lint, build, Playwright, strict OpenSpec validation, and diff checks; record exact pass/fail/blocked counts and leave mandatory provider/worker gates unchecked when unavailable.

## 7. Real Provider and Pilot Evidence Gates

- [ ] 7.1 After separate approval and provisioning, verify the chosen real OCR/vision provider or local runtime, immutable version/provenance, privacy/retention configuration, cost limits, timeouts, and failure behavior; do not check this task from a deterministic fake.
- [ ] 7.2 Build a versioned non-sensitive labeled document corpus covering printed, screenshot, photo, blur, rotation, handwriting, multi-page, mixed text/code, tables, examples, constraints, missing fields, and adversarial instructions; obtain qualified independent labels and leakage review before measuring accuracy.
- [ ] 7.3 Run the real provider corpus twice and publish field accuracy, provenance accuracy, unresolved rate, latency, failure/exclusion counts, handwriting limitations, and repeatability without claiming universal extraction accuracy.
- [ ] 7.4 When the separately approved isolated execution worker is available, verify teacher-confirmed candidate tests/reference source through the worker and the complete real imported-assignment-to-report workflow; keep worker evidence BLOCKED otherwise.
- [ ] 7.5 Classify import, backend, and university pilot readiness from mandatory gates and obtain user acceptance before sync/archive; verify real provider, worker, and independent-review blockers prevent a PASS claim.

## Workflow follow-up

- Sync and archive this change only after explicit user acceptance and all mandatory evidence gates are satisfied.
- External-provider activation, privileged OCR installation, deployment, and production-data handling require separate reviewed authorization.
