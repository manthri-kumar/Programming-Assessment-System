# End-to-end acceptance evidence

Evidence date: 2026-11-10

## Environment-independent application acceptance

- Backend: 222 tests passed after assignment import, reliability, report-v3, security, backup, worker-contract, and migration additions; Python compilation and dependency checks also passed.
- Frontend: 61 Vitest tests passed; TypeScript, ESLint, and production build passed.
- Browser: 21 Playwright scenarios passed in 58.7 seconds using an isolated temporary SQLite database, disposable local FastAPI server, and installed system Chrome across desktop, tablet, and mobile projects.
- Browser coverage includes registration/login/session/logout, manual assignment create/edit, embedded-text PDF import and explicit review/confirmation, imported assignment student visibility, submission, fail-closed assessment, exactly two agents, report-v3, provisional execution messaging, student teacher-detail redaction, owning-teacher evidence, routes, responsive shell, accessibility checks, authorization failures, loading/empty/not-found/API-error/expired-session states.

The initial historical Playwright attempt could not find the bundled Chromium executable and was not counted. The current accepted system-Chrome run is 21/21, including embedded-PDF import and deterministic photo-adapter review across desktop, tablet, and mobile. Adapter scenarios verify presentation and integration, not real OCR accuracy.

## Mandatory blocked acceptance

Real Python 3.11, C11/Clang, and Java 17 compilation/execution is **BLOCKED**. WSL2 Ubuntu exists, but rootless Podman, Clang, and Java are not installed and privileged provisioning was not authorized. No student source was executed on the Windows host.

Independent held-out grading/feedback review is **BLOCKED** because candidate labels remain `pending-independent-review`. Fake-runner results are excluded from accuracy claims.

Real image OCR and handwriting acceptance are **BLOCKED** because no local Tesseract-compatible executable or approved external provider is configured. Embedded PDF text extraction is verified; deterministic OCR adapters are contract evidence only.

Therefore this document verifies the environment-independent UI/API/two-agent/persistence workflow only. Full backend and pilot readiness remain **BLOCKED**.

