# Assignment import implementation status

Evidence date: 2026-11-09

## Scope ownership

`add-ai-assignment-import` owns private teacher document ingestion, embedded PDF text extraction, the local OCR provider boundary, structured import drafts, provenance, review, and canonical assignment confirmation.

It does not duplicate these existing ledgers:

- `fix-assignment-creation-validation` owns canonical assignment validation and graph-backed concept IDs.
- `implement-codeassess-frontend` owns the base teacher/student interface and manual assignment workflow.
- `backend-core-audit` owns the two-agent assessment pipeline and real isolated Python/C/Java worker gates.
- `complete-codeassess-university-readiness` owns report v3, lifecycle reliability, institutional foundations, independent research review, and final readiness.

Imported assignments deliberately reuse those components. Their existing incomplete worker and independent-review tasks remain incomplete.

## Current status

| Capability | Status | Evidence / limit |
| --- | --- | --- |
| Manual assignment creation | VERIFIED | Existing canonical form and API remain available. |
| PNG/JPEG/WebP ingestion | VERIFIED for bounded parsing | Signature/type/extension, safe decode, dimension/pixel/byte limits, owner isolation, private storage, cleanup, and tests. |
| PDF ingestion and embedded text | VERIFIED for bounded fixtures | Signature, parser, encryption/active-feature/page limits and embedded text tests. No PDF rendering or scripts. |
| Local OCR abstraction | PARTIALLY VERIFIED | Strict disabled-by-default Tesseract-compatible adapter and deterministic test adapter exist. No real OCR executable is provisioned. |
| Structured draft and graph mapping | VERIFIED for deterministic fixtures | Missing fields remain missing; explicit language only; canonical exact graph mapping; provenance and stable normalization tests. |
| Teacher review and confirmation | VERIFIED for component/API fixtures | Manual/upload/photo controls, provenance, editing, private save/resume, explicit confirmation, and existing assignment validation integration. |
| Real photo/handwriting accuracy | BLOCKED | Requires separately approved OCR runtime/provider and independently labeled non-sensitive corpus. |
| Real student execution | BLOCKED | Approved isolated worker remains unavailable; assessment fails closed. |

No external OCR/cloud service is configured or contacted. No faculty document is sent outside the local application.
