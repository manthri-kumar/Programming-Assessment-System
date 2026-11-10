# Assignment document import

CodeAssess supports private teacher-owned assignment imports for PNG, JPEG, WebP, and PDF documents. Manual assignment creation remains available and is the fallback whenever extraction is unavailable.

## Dependencies and provenance

- `python-multipart==0.0.20` provides bounded FastAPI multipart parsing (Apache-2.0).
- `Pillow==11.1.0` provides image signature, decoding, dimension, and decompression-bomb validation (HPND).
- `pypdf==5.3.0` provides non-rendering embedded PDF text extraction (BSD-3-Clause).

These are project-local Python dependencies. They do not install privileged software. No cloud OCR provider is configured or contacted.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `CODEASSESS_IMPORT_ENABLED` | `1` | Enables teacher import endpoints and UI capability response. |
| `CODEASSESS_IMPORT_ROOT` | `data/private-imports` | Private source directory, which must stay below the project data directory. |
| `CODEASSESS_IMPORT_MAX_BYTES` | `10485760` | Maximum source bytes. |
| `CODEASSESS_IMPORT_MAX_PAGES` | `20` | Maximum PDF pages. |
| `CODEASSESS_IMPORT_MAX_DIMENSION` | `12000` | Maximum image width or height. |
| `CODEASSESS_IMPORT_MAX_PIXELS` | `40000000` | Maximum decoded pixels. |
| `CODEASSESS_IMPORT_RETENTION_HOURS` | `72` | Unpublished source retention. |
| `CODEASSESS_IMPORT_AUDIT_RETENTION_DAYS` | `30` | Content-free deletion/expiry tombstone retention. |
| `CODEASSESS_TESSERACT_PATH` | unset | Optional absolute local Tesseract-compatible executable. Unset means OCR unavailable. |
| `CODEASSESS_TESSERACT_SHA256` | unset | Required approved SHA-256 pin whenever the executable path is set. |
| `CODEASSESS_IMPORT_OCR_CONCURRENCY` | `2` | Maximum concurrent local OCR processes (1–8). |

Unsafe, relative, or out-of-root storage configuration fails closed. Original PDFs are returned as attachments only. Images use authenticated, no-store preview responses.

## Data handling

Uploads are treated as untrusted. The backend validates authorization, declared type, extension, magic signature, decoder/parser result, bytes, dimensions, pixels, pages, encryption, and unsupported active PDF features. Source files use random storage keys outside the web root. Temporary files are removed after success or failure. Expired unpublished imports are deleted on access/startup cleanup.

Logs and API responses exclude document bytes, extracted faculty text, absolute storage paths, secrets, reference programs, and hidden tests. Students and unrelated teachers cannot access imports or provenance. Confirmation removes the private source file while retaining bounded owner-only provenance. Explicit deletion and expiry retain only a content-free tombstone (random import ID, owner ID, reason, media type, byte size, and timestamps) for the configured audit period.

Audit events contain only bounded request/import identifiers, owner identifiers, byte counts, timings, lifecycle categories, and safe reason codes. The shared structured logger redacts document content, extracted text, prompts, provider responses, filesystem paths and storage keys, source/reference code, hidden tests, credentials, tokens, cookies, and secrets recursively before serialization.

## Extraction providers

Embedded PDF text extraction is built in. Images and scan-only pages require the local OCR adapter. The adapter is disabled unless `CODEASSESS_TESSERACT_PATH` names an approved absolute executable. This repository does not install Tesseract and never falls back to a cloud service. Handwriting accuracy is not claimed.

The local adapter rejects relative executable paths before resolution and requires the configured SHA-256 pin. Each OCR stdout/stderr stream is bounded to 64,000 bytes during capture; overflow kills the process and returns `ocr_output_exceeded`, rather than silently accepting a truncated draft. Timeout/start failures use sanitized categories; raw stderr is discarded. Portable adapter tests intercept process creation and verify these controls without invoking OCR. They do not verify a real decoder, Windows process isolation, OCR accuracy, or process-tree behavior of any future provider that launches descendants; runtime activation still requires the separate approved-provider verification gate.

### Windows provisioning gate

No Tesseract executable was found on this Windows host on 2026-11-09. The current WinGet entry `UB-Mannheim.TesseractOCR` exposes version `5.4.0.20240606` with installer SHA-256 `c885fff6998e0608ba4bb8ab51436e1c6775c2bafc2559a19b423e18678b60c9`; it is **not approved for this project** because upstream 5.5.4 contains later security fixes. Tesseract's upstream project currently lists 5.5.4 as the latest release and the official documentation notes that modern Windows installers may be third-party distributions. A reviewed 5.5.4-or-newer Windows build, its publisher/source, exact installer hash, installed executable hash, and English model provenance therefore require separate approval before activation.

After an approved runtime is installed, verify it without changing machine configuration:

```powershell
.\scripts\ocr\verify-windows-tesseract.ps1 `
  -TesseractPath 'C:\Program Files\Tesseract-OCR\tesseract.exe' `
  -ExpectedSha256 '<approved-installed-executable-sha256>'
```

Set the two environment values printed by that script for the backend process, restart it, and check `/assignment-imports/capabilities`. The existing Take Photo flow then uploads an authenticated private image, invokes the pinned local executable with a fixed argument list and bounded timeout, and populates the same teacher-review form used by embedded PDF import. Deterministic browser-adapter tests verify that UI path; they are not real OCR accuracy evidence. Scan-only PDF OCR remains unavailable until a separately reviewed bounded PDF renderer is provisioned; the adapter does not pass PDFs directly to Tesseract.

Document text is handled only as data. Extraction cannot invoke assessment agents, the secure execution worker, network tools, or arbitrary commands.

## Publication safeguards

Extraction creates a private draft; it never publishes automatically. The teacher must review and confirm the canonical assignment payload. Missing or ambiguous language/deadline fields remain empty. Only canonical Knowledge Graph IDs are submitted. Generated expected outputs remain unverified and cannot become hidden grading tests automatically.
