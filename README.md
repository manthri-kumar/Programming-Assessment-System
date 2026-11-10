# CodeAssess

## Knowledge Graph-Driven Multi-Agent Framework for Intelligent Programming Assessment

CodeAssess is a deterministic programming-assessment platform for Python, C, and Java. It combines static program analysis, versioned rubric scoring, a programming-concept Knowledge Graph, evidence-linked feedback, teacher/student workflows, and a responsive React application.

The project intentionally uses **exactly two top-level agents** and does not call an external LLM API:

1. **`ImplementationEvaluationAgent`** coordinates preprocessing, language parsing, syntax analysis, concept detection, structural comparison, complexity analysis, secure-runner delegation, rubric scoring, evidence collection, and assessment limitations.
2. **`FeedbackAgent`** consumes the first agent's typed result, identifies strengths and weaknesses, traverses Knowledge Graph prerequisites, produces learning recommendations, and composes the final report.

Supporting parsers, analysis services, the Knowledge Graph, the execution adapter, persistence, and report composition are internal modules—not additional agents.

> [!IMPORTANT]
> Static analysis and the application workflows are implemented and tested. Real student-code compilation and execution remain fail-closed until the approved project-owned Linux worker is built and verified. The project does not run untrusted submissions directly on the Windows host.

## Features

### Teacher portal

- Invitation-gated teacher registration and role-based authorization.
- Assignment creation, editing, ownership validation, deadlines, canonical concepts, versioned rubrics, reference solutions, and protected tests.
- Private assignment import from PNG, JPEG, WebP, and PDF.
- Embedded PDF-text extraction, provenance/confidence review, canonical concept mapping, and explicit confirmation before publication.
- Optional local Tesseract adapter that is disabled unless an approved executable and SHA-256 pin are configured.
- Submission review, evidence-rich assessment reports, analytics, and student progress visibility.

### Student portal

- Server-backed assignment discovery and assignment details.
- Monaco-based coding workspace with private draft persistence.
- Submission history, bookmarks, activity, progress, and recommendations.
- Student-safe assessment reports with scores, stage evidence, limitations, feedback, and Knowledge Graph learning paths.
- Responsive desktop, tablet, and mobile layouts using the project's black-and-yellow visual system.

### Deterministic assessment

- Python parsing with CPython AST.
- C and Java static parsing with pinned Tree-sitter grammars.
- Normalized intermediate representation and structural comparison.
- Syntax, concept, and supported complexity analysis.
- Configurable `core-v1` rubric with evidence-linked component scores.
- Explicit incomplete/unavailable results when required execution evidence is absent.
- Additive `assessment-report-v3` output with `assessment-report-v2` replay compatibility.

### Knowledge Graph and feedback

- Versioned programming concepts and prerequisite relationships.
- Deterministic concept matching and prerequisite traversal.
- Evidence-linked weakness detection and recommendations.
- Separate student feedback and teacher-visible explanations.

## Architecture

```text
Teacher assignment / import
            │
            ▼
Student submission
            │
            ▼
ImplementationEvaluationAgent
  ├─ preprocessing and normalized IR
  ├─ Python / C / Java static parsing
  ├─ syntax, concepts, structure, complexity
  ├─ isolated execution delegation (fail-closed)
  └─ core-v1 scoring, evidence, limitations
            │ typed evaluation result
            ▼
FeedbackAgent
  ├─ strengths, weaknesses, and explanations
  ├─ Knowledge Graph prerequisite traversal
  ├─ personalized learning recommendations
  └─ assessment-report-v3 composition
            │
            ▼
SQLite persistence → FastAPI → Student / Teacher portals
```

| Component | Responsibility |
| --- | --- |
| React frontend | Authenticated teacher/student workflows and report presentation |
| FastAPI backend | Validation, authorization, orchestration, APIs, and error handling |
| `ImplementationEvaluationAgent` | Typed program analysis and deterministic evaluation |
| `FeedbackAgent` | Evidence-grounded explanations, graph reasoning, and final reports |
| Knowledge Graph | Canonical concepts, prerequisites, guidance, and traversal |
| SQLite repository | Users, assignments, imports, submissions, jobs, reports, analytics, and history |
| Isolated worker boundary | Protected compilation/execution for Python 3.11, C11, and Java 17; not yet provisioned |

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19, TypeScript 5.9, Vite 7, TanStack Query, React Router, Monaco Editor, React Flow |
| Backend | Python 3.11, FastAPI, Pydantic 2, Uvicorn |
| Persistence | SQLite with migration-safe schema initialization and transactions |
| Python analysis | CPython AST |
| C analysis | `tree-sitter-c`; authoritative Clang C11 compilation is worker-gated |
| Java analysis | `tree-sitter-java`; authoritative Java 17 compilation is worker-gated |
| Document import | Pillow, pypdf, multipart upload, optional hash-pinned local Tesseract |
| Testing | Pytest, Vitest, Testing Library, MSW, Playwright |
| Specifications | OpenSpec 1.14.1 |

## Repository structure

```text
Automated-Code-Assessment-System/
├── backend/          # API, agents, analysis, scoring, persistence, worker client
├── frontend/         # React/TypeScript teacher and student application
├── worker/           # Isolated Linux worker entrypoint and control service
├── modules/          # Characterized legacy C-assessment modules
├── data/             # Versioned concepts, fixtures, and benchmark candidates
├── tests/            # Backend, agent, security, API, and contract tests
├── scripts/          # OpenAPI, OCR-verification, and worker scripts
├── docs/             # Setup, architecture, security, API, and status documents
├── openspec/         # Approved changes, specifications, designs, and task ledgers
├── main.py           # Guarded compatibility CLI
└── README.md
```

## Local setup

### Prerequisites

- Python 3.11
- Node.js and npm
- Git
- Windows PowerShell for the commands below

The application can run without the isolated worker, but functional execution and complete scoring remain unavailable.

### Clone

```powershell
git clone https://github.com/manthri-kumar/Programming-Assessment-System.git
cd Programming-Assessment-System
```

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

$env:ASSESSMENT_SECRET = "replace-with-a-long-random-local-secret"
$env:ASSESSMENT_TEACHER_REGISTRATION_CODE = "replace-with-a-private-local-invitation"

.\.venv\Scripts\python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

The default database is `assessment.db`. Do not commit it. `GET /health` reports process health; `GET /ready` remains unavailable while the secure worker is not configured.

### Frontend

In a second terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open <http://127.0.0.1:5173>. Vite proxies `/api` to the backend at `http://127.0.0.1:8000` by default.

Teacher registration requires the exact private value configured in `ASSESSMENT_TEACHER_REGISTRATION_CODE`.

## Verification

Backend:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q backend worker tests scripts main.py
.\.venv\Scripts\python.exe -m pip check
```

Frontend:

```powershell
cd frontend
npm.cmd run test
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

Browser tests require a disposable local backend configured with the same teacher invitation code used by the suite. An already-installed Chrome can be used without downloading a Playwright browser:

```powershell
$env:PW_USE_SYSTEM_CHROME = "1"
$env:E2E_TEACHER_REGISTRATION_CODE = $env:ASSESSMENT_TEACHER_REGISTRATION_CODE
npm.cmd run test:e2e
```

Deterministic fake-runner and fake-OCR tests verify contracts only. They are not evidence of real isolated execution or real OCR accuracy.

## Security model

- Authentication, teacher/student roles, ownership checks, and audience-specific report redaction.
- Reference solutions, hidden tests, private imports, provider details, and teacher explanations are excluded from student responses.
- Bounded upload, parser, image, PDF, OCR, request, and output contracts.
- Private random import storage keys, expiry, cleanup, no-store previews, restrictive response headers, and content-free audit events.
- No external LLM or cloud OCR provider is enabled.
- No host fallback for student-code execution.
- The planned worker uses a separate protected control service, rootless Podman, an immutable image digest, mTLS, no network, dropped capabilities, a read-only root, resource limits, and mandatory cleanup evidence.

See [Security](docs/backend/SECURITY.md), [Assignment Import](docs/backend/ASSIGNMENT_IMPORT.md), and [Worker Approval](docs/backend/WORKER_APPROVAL.md).

## Current status and limitations

### Verified for defined environment-independent behavior

- Exactly two top-level agents and deterministic orchestration.
- FastAPI authentication, assignment, submission, evaluation, progress, analytics, draft, bookmark, import, and report APIs.
- SQLite persistence and transactional assessment lifecycle.
- Python/C/Java static analysis and normalized structural evidence.
- `core-v1` scoring, Knowledge Graph traversal, recommendations, and report-v3 persistence/replay.
- Teacher/student frontend workflows, responsive layouts, and fail-closed presentation.
- Embedded-text PDF import and deterministic adapter behavior.

### Blocked or pending

- **Real isolated execution:** WSL2 currently lacks the approved rootless Podman, pinned image/digest, certificates, Clang, and Java worker runtime. Python/C11/Java17 student execution has not been verified.
- **Real OCR evidence:** no approved Tesseract 5.5.4-or-newer Windows runtime and executable hash are provisioned. Image OCR remains unavailable; embedded PDF text continues to work.
- **Accuracy measurement:** benchmark and document labels remain pending qualified independent review. No universal grading or OCR accuracy claim is made.
- **Pilot readiness:** real worker containment, cleanup/resource tests, real-provider evaluation, independent labels, and final acceptance remain mandatory.

Detailed status is maintained in [Implementation Status](docs/product/IMPLEMENTATION_STATUS.md), [Backend Results](docs/BACKEND_FINAL_RESULTS.md), and the active OpenSpec task ledgers.

## Additional documentation

- [Backend setup](docs/backend/SETUP.md)
- [Frontend setup](docs/FRONTEND.md)
- [API contracts](docs/backend/API.md)
- [Architecture](docs/product/ARCHITECTURE.md)
- [Agent verification](docs/product/AGENT_VERIFICATION.md)
- [Knowledge Graph](docs/backend/KNOWLEDGE_GRAPH.md)
- [Local Linux worker](docs/backend/LOCAL_LINUX_WORKER.md)
- [Research evaluation plan](docs/RESEARCH_EVALUATION_PLAN.md)

## Project objective

This B.Tech Computer Science and Engineering final-year project investigates whether deterministic program analysis, versioned rubric scoring, Knowledge Graph reasoning, and evidence-grounded feedback can provide a more explainable assessment than output-only grading. Results are reported only for explicitly supported and reproducibly tested behavior.

**Repository:** <https://github.com/manthri-kumar/Programming-Assessment-System>
**Status:** Active development; core application implemented, real execution/OCR/independent validation pending.
