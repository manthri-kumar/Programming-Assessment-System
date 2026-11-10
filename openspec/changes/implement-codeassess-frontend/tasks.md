# Tasks

## 1. Backend contract baseline

- [x] 1.1 Reconfirm generated OpenAPI, authentication, ownership, report, progress, and analytics schemas; add contract snapshots and verify existing backend tests still pass unchanged.
- [x] 1.2 Add bounded assignment presentation metadata and timezone-aware optional deadlines through a SQLite migration, repository, models, and existing assignment routes; verify owner/student visibility and validation tests.
- [x] 1.3 Add an authenticated client-safe `GET /concept-graph` contract; verify graph version/nodes/typed edges are returned without paths, secrets, source, or unrelated learner evidence.
- [x] 1.4 Add student-scoped idempotent bookmark list/add/remove persistence and routes; verify cross-student access, missing assignments, rollback, pagination, and redacted logs.
- [x] 1.5 Add student-scoped bounded assignment draft read/upsert/delete persistence and routes without runner invocation; verify ownership, size limits, replacement, deletion, and worker-unavailable behavior.
- [x] 1.6 Decide activity support from existing persisted events: implement real role-scoped activity writes/read if coherent, otherwise publish an explicit unavailable capability; verify no read-time sample events are generated.
- [x] 1.7 Regenerate OpenAPI and update backend API/security/persistence documentation; verify generated-contract equality and the complete Python regression suite.

## 2. Frontend foundation and quality gates

- [x] 2.1 Create one `frontend/` React/TypeScript/Vite project with pinned compatible dependencies and scripts; verify a clean project-local installation, strict TypeScript check, lint, unit-test discovery, and production build.
- [x] 2.2 Configure Tailwind/design tokens for the approved dark/gold palette, typography, spacing, surfaces, semantic colors, focus rings, and responsive breakpoints; verify token/component visual tests contain no runtime sample data.
- [x] 2.3 Implement shared buttons, cards, badges, forms, tables, tabs, dialogs, skeletons, empty/error/unavailable states, progress indicators, and page headers; verify keyboard/focus/ARIA component tests.
- [x] 2.4 Add Vitest, Testing Library, MSW, and Playwright configuration with explicit UI-fixture labeling; verify mocked UI tests cannot be reported as backend execution evidence.

## 3. Typed API, authentication, and application shell

- [x] 3.1 Build centralized OpenAPI-aligned TypeScript models, Axios transport, error mapping, request cancellation, and TanStack Query keys; verify 200/401/403/404/422/503/500 contract tests.
- [x] 3.2 Implement sessionStorage/in-memory bearer session, login, student/teacher registration, invitation input, `/auth/me`, logout, and password visibility/validation; verify session-expiry cleanup and no credential leakage.
- [x] 3.3 Implement protected role routes and student/teacher redirects; verify direct unauthorized URLs issue no forbidden mutation and clear protected cached data.
- [x] 3.4 Implement responsive sidebar/top bar, exact supported navigation, mobile drawer, profile menu, and Ctrl+K search; verify keyboard navigation and truthful unavailable contests/discuss/notifications/calendar states.

## 4. Student dashboard

- [x] 4.1 Implement the time-aware greeting and four real-data statistic cards; verify null/incomplete totals are excluded and loading/empty/error states render correctly.
- [x] 4.2 Implement Continue Solving from confirmed drafts/submissions, accurate metadata/deadline/status, and workspace navigation; verify absent test progress is not fabricated.
- [x] 4.3 Implement Recommended Problems tabs from assignments and evidence-backed recommendations only; verify filters omit unsupported difficulty/acceptance metadata and bookmarks persist through the API.
- [x] 4.4 Implement recent submissions, deadlines, learning progress, and real/unavailable activity sections in screenshot order; verify dates/timezones, report links, and no invented mastery/events.
- [x] 4.5 Match the supplied desktop screenshot and implement tablet/mobile reflow; verify screenshot comparisons at approved viewports plus keyboard and automated accessibility checks.

## 5. Student assignment and coding workflow

- [x] 5.1 Implement assignment list/search/filter/detail routes using real language, concepts, status, deadline, and presentation metadata; verify unsupported filters are absent.
- [x] 5.2 Implement the split-screen Monaco workspace with language-safe templates, resizing, accessible fallback, and draft restore/save/delete; verify no source execution occurs in browser tests.
- [x] 5.3 Implement submission and evaluation mutations with confirmation, cancellation, status/output display, and 503 Execution Unavailable handling; verify no simulated success or passed-test count.
- [x] 5.4 Implement assessment result and FeedbackAgent views for report-v2 components, evidence, limitations, feedback, graph reasoning, and recommendations; verify null/unavailable evidence remains null and exactly two top-level agents are shown.

## 6. Student history and learning pages

- [x] 6.1 Implement My Submissions pagination, filtering, sorting, detail, evaluation, and report navigation; verify only authenticated-student data is cached/rendered.
- [x] 6.2 Implement Progress with real status counts, valid-score trends, assessment history, and evidence-supported concept summaries; verify insufficient data produces truthful empty states.
- [x] 6.3 Implement Bookmarks list/add/remove/navigation with rollback on mutation failure; verify persistence across reload and user-session isolation.
- [x] 6.4 Implement Recommended and Learning Path pages from persisted graph/recommendation evidence; verify prerequisite order, contradictions, unknown evidence, and no invented guidance.
- [x] 6.5 Implement Profile/Settings using supported account display plus clearly device-local editor/display preferences; verify unsupported password/profile mutations are unavailable.

## 7. Knowledge Graph visualization

- [x] 7.1 Implement lazy-loaded React Flow graph from `/concept-graph` with pan, zoom, selection, typed edges, version, and concept guidance; verify no hardcoded relationships.
- [x] 7.2 Overlay report-scoped weak/satisfied/unknown/contradictory evidence and paths; verify evidence links and backend recommendation ordering are preserved.
- [x] 7.3 Implement the synchronized accessible list/tree representation and responsive fallback; verify complete keyboard and screen-reader-oriented tests.

## 8. Teacher experience

- [x] 8.1 Implement teacher dashboard with owned assignment/submission/status/valid-score analytics; verify incomplete totals and cross-owner data are handled correctly.
- [x] 8.2 Implement create/edit/view assignment forms for presentation fields, language, deadline, reference, tests, concepts, policy, and rubric weights; verify accessible validation and hidden data separation.
- [x] 8.3 Implement owned-assignment submission list/review/evaluate/report workflows; verify 403/404 handling and exact two-agent report semantics.
- [x] 8.4 Verify teacher navigation exposes no global administration, worker controls, arbitrary compiler settings, or unsupported availability management.

## 9. Integrated verification and handoff

- [x] 9.1 Run TypeScript, ESLint, frontend unit/route/API/auth/form/filter/error tests and production build; fix all failures and record actual counts/versions.
- [x] 9.2 Run complete backend tests, compile checks, generated OpenAPI equality, dependency checks, and strict validation; fix regressions without weakening security.
- [x] 9.3 Start local backend/frontend and exercise every implemented student/teacher route at desktop, tablet, and mobile widths; verify navigation, console, requests, loading, empty, error, 401/403/422/503, and responsive behavior.
- [x] 9.4 Compare the student dashboard against the supplied reference and document intentional data-driven differences, unsupported features, accessibility findings, and remaining backend/worker blockers.
- [x] 9.5 Publish exact Windows PowerShell setup/run/test instructions and a page-by-page functional/partial/blocked matrix; verify no deployment, commit, or production-readiness claim occurred.

## Workflow follow-up

- Do not archive or deploy this change until human review and all mandatory checks pass.
- Backend real-worker acceptance and independent benchmark review remain tracked by `backend-core-audit`.
