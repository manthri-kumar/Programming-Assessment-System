# CodeAssess frontend

The frontend is a React 19, strict TypeScript, Vite, and Tailwind application in `frontend/`. It uses the supplied near-black and golden-yellow visual direction and consumes authenticated FastAPI data. Runtime code contains no sample assignments, scores, activity, mastery, or execution outcomes.

## Run locally on Windows PowerShell

Terminal 1:

```powershell
cd "C:\Users\manth\OneDrive\Documents\final project\Automated-Code-Assessment-System"
$env:ASSESSMENT_SECRET = "replace-with-a-long-local-secret"
$env:ASSESSMENT_TEACHER_REGISTRATION_CODE = "replace-with-a-local-invitation"
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2:

```powershell
cd "C:\Users\manth\OneDrive\Documents\final project\Automated-Code-Assessment-System\frontend"
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to the local FastAPI process. Tokens remain in memory and `sessionStorage`; logout or HTTP 401 clears protected query data.

Teacher registration uses the exact private value configured in `ASSESSMENT_TEACHER_REGISTRATION_CODE`. Invalid, duplicate, unconfigured, validation, network, and server failures are displayed with distinct safe messages; arbitrary backend details are not rendered.

If OneDrive Files On-Demand marks native package binaries with an unsupported file type (`EFTYPE`), make the repository folder always available locally or copy the project to a non-OneDrive development directory before `npm install`. Do not bypass antivirus or execution policy.

## Checks

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run test
npm.cmd run build
npm.cmd run test:e2e
```

The Playwright suite requires the disposable local backend to be running with `ASSESSMENT_TEACHER_REGISTRATION_CODE=browser-teacher-code`. It creates uniquely named local test users, assignments, and submissions. To use installed system Chrome instead of downloading a Playwright browser:

```powershell
$env:PW_USE_SYSTEM_CHROME = "1"
npm.cmd run test:e2e
```

Browser fixtures, MSW tests, and screenshots verify presentation and API integration only; they are not evidence of secure student-code execution.

For an isolated verification run that must not reuse existing development ports, set `E2E_API_URL`, `VITE_API_PROXY_TARGET`, `E2E_WEB_PORT`, and `VITE_DEV_PORT` to matching disposable backend/frontend ports before `npm.cmd run test:e2e`.

## Page status

| Area | Status | Notes |
|---|---|---|
| Login and student/teacher registration | Functional | Teacher registration remains invitation-gated. |
| Student dashboard | Functional | Uses assignments, submissions, progress, bookmarks, activity, and deadlines. |
| Assignments and coding workspace | Functional | Monaco editor, server draft persistence, submit/evaluate; no browser Run action. |
| Submissions and reports | Functional | Displays persisted `assessment-report-v3` evidence, feedback, limitations, and recommendations while retaining v2 replay compatibility; bounded execution output and exactly two top-level agents are preserved. |
| Progress, bookmarks, recommendations | Functional | Null totals and missing recommendation evidence stay unavailable/empty. |
| Knowledge Graph | Functional | Server graph, React Flow view, and equivalent accessible concept list. |
| Teacher dashboard and assignment forms | Functional | Manual, Upload Image/PDF, and Take Photo modes; private provenance review, canonical concepts, hidden-test safeguards, explicit confirmation, owner-scoped analytics, and editing. Embedded PDF text works locally; image OCR reports unavailable unless an approved local executable is configured. |
| Contests, discussions, notifications, calendar | Unavailable | No approved backend contracts; no fake records or active controls. |
| Profile/password mutation | Unavailable | Account remains read-only; editor preferences are explicitly device-local. |
| Real isolated execution | Blocked externally | Backend continues to fail closed until the approved Linux worker is verified. |

## Visual and accessibility notes

The desktop hierarchy follows the supplied reference: fixed sidebar, search top bar, greeting, four statistics, a wide work column, a right progress/activity rail, yellow primary actions, and semantic green/red/blue statuses. Tablet moves the right rail below the main column. Mobile replaces the sidebar with a focusable drawer and stacks cards without page-level horizontal overflow. Unsupported screenshot features are omitted rather than presented as operational.
