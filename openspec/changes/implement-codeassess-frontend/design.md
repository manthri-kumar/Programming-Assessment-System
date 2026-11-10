# Design

## Context

See `proposal.md` for motivation. The repository currently has no frontend or JavaScript manifest. FastAPI exposes bearer authentication, assignments, submissions/evaluation, student progress, and teacher analytics; it does not expose deadlines/presentation metadata, graph reads, bookmarks, drafts, activity, notifications, contests, or discussions. The backend intentionally fails closed when the isolated worker is unavailable, and backend acceptance remains blocked on real-worker evidence and independent benchmark review. The user has explicitly authorized this separate frontend change while those limitations remain visible.

## Goals / Non-Goals

**Goals:**

- Build one maintainable React/TypeScript application that closely reproduces the approved student dashboard and provides complete supported student/teacher workflows.
- Consume generated backend contracts through a centralized typed client with consistent auth, cancellation, error, loading, empty, and unavailable behavior.
- Add only minimal backend contracts required for truthful frontend features, preserving ownership and hidden-test boundaries.
- Verify responsive/accessibility behavior and prevent static demo data from being presented as real state.

**Non-Goals:**

- Production deployment, public hosting, social authentication, payment, multi-tenancy, contests, forums, notifications, calendar integration, or arbitrary administration.
- Browser/host code execution, a third top-level agent, score recomputation, fabricated recommendations/mastery, or claiming backend production readiness.
- Replacing the existing FastAPI, SQLite, report, rubric, Knowledge Graph, or agent orchestration.

## Decisions

### 1. Create one `frontend/` React/TypeScript/Vite application

Use React, strict TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Axios, Monaco Editor, React Flow, Recharts, and Lucide React. This matches the requested stack and avoids a second client application. Project-local versions will be pinned in the lockfile during apply. Alternatives such as Next.js add server/runtime behavior the local FastAPI application does not need.

Structure by responsibility: `app/` providers/router, `api/` generated/manual contract types and transport, `auth/`, `components/`, `features/student/`, `features/teacher/`, `features/learning/`, `pages/`, `styles/`, and `test/`. Components remain presentational where possible; server state belongs to queries/mutations, not a global state library.

### 2. Use the screenshot as a measured visual contract

CSS variables define the near-black background, charcoal surfaces, gold accent, text, borders, semantic statuses, radii, shadows, spacing, and focus rings. A fixed desktop sidebar and top bar lead into a responsive grid matching the screenshot's section order. Tablet reflows the right rail; mobile uses an accessible drawer and stacked cards. Screenshot sample values never enter fixtures used as runtime data.

### 3. Treat the backend as authoritative server state

TanStack Query owns fetching, invalidation, retries, cancellation, and cache boundaries. Axios adds the bearer header, maps the existing error envelope, and performs one session-expiry transition on 401. Queries use stable keys scoped by authenticated user/role. Mutations invalidate only affected resources. No optimistic update is used for protected assignment/report data; bookmark optimistic state is allowed only with rollback to confirmed server state.

The access token is held in memory and `sessionStorage` for tab-session continuity; it is never placed in URLs, logs, query keys, analytics, or persistent localStorage. `/auth/me` is authoritative for role. Route guards improve UX but backend authorization remains mandatory.

### 4. Separate current API integrations from additive support contracts

Current routes directly support login/registration/me, assignment list/detail/create/edit, submission create/list/detail/evaluate/report, student progress, and teacher analytics. Additive backend work supplies:

- `GET /concept-graph`
- optional assignment presentation/deadline fields
- `GET|PUT|DELETE /assignments/{id}/draft`
- `GET /bookmarks`, `PUT|DELETE /bookmarks/{assignment_id}`
- `GET /student/activity` only if persisted event writes are implemented coherently

Profile editing, password changes, notifications, contests, discussions, and calendars remain unavailable because no approved contract exists. Settings displays supported account information and local display/editor preferences clearly labeled device-local.

### 5. Keep execution and report semantics unchanged

The editor sends source only through submission endpoints; Run is enabled only if a distinct approved secure-run contract exists. Otherwise the workspace offers Submit/Evaluate and labels ad-hoc execution unavailable. HTTP 503 with an incomplete report is rendered as a valid persisted limitation, not a generic network failure. Result pages consume `assessment-report-v2` and never calculate scores or graph mastery themselves.

### 6. Derive dashboard data conservatively

Dashboard queries combine assignments, own submissions, evaluations/progress, bookmarks, and optional activity. Active/solved definitions are documented and based on actual statuses. Average excludes null totals. Continue Solving selects the newest owned draft or unevaluated/incomplete submission; absent backend evidence yields an empty state. Deadlines use ISO timestamps and user-local formatting. Difficulty, acceptance rates, passed-test progress, and topic groupings appear only when supplied by contracts.

### 7. Render graph and reports with accessible alternatives

React Flow renders nodes/edges and status overlays from `/concept-graph` plus persisted report evidence. A synchronized semantic list provides equivalent keyboard/screen-reader access. Recharts visualizes only defined score/time series; insufficient data produces an explanatory empty state. Monaco loads only in the workspace route and falls back to an accessible textarea if unavailable.

### 8. Test contracts and visual behavior at layers

Vitest and Testing Library cover components, routes, auth/session expiry, role guards, forms, filters, errors, and API adapters with MSW. TypeScript, ESLint, and Vite production build are mandatory. Playwright exercises authenticated student/teacher flows at desktop/tablet/mobile against a controlled API fixture server; it may verify UI state but never masquerades mocked data as backend execution evidence. Existing Python tests and strict validation run after backend additions.

## Risks / Trade-offs

- **Backend acceptance remains blocked** → Frontend development can proceed against tested contracts, but production readiness and real execution UX remain blocked and labeled.
- **Requested pages exceed current APIs** → Add only the contracts in `frontend-support-contracts`; render unsupported domains honestly.
- **Large initial client scope** → Implement vertical authenticated slices and verify each before moving forward; share query/state/error components.
- **Monaco/graph/chart bundle size** → Route-split heavy features, lazy-load them, and keep dashboard dependencies small.
- **Bearer token XSS exposure** → Avoid localStorage, enforce CSP-compatible code, escape server text, disallow HTML injection, and keep dependencies pinned/audited.
- **Visual fidelity can conflict with responsiveness** → Use the screenshot at its desktop aspect ratio as the primary baseline, then explicit tablet/mobile acceptance viewports.
- **Mocked browser tests can be mistaken for execution proof** → Label fixtures as UI contract tests; real worker evidence remains exclusively in `backend-core-audit`.

## Migration Plan

1. Add project-local frontend tooling and scripts without changing backend startup.
2. Add additive SQLite migrations/API contracts with backend tests and regenerated OpenAPI.
3. Implement authentication/shell, then student and teacher vertical slices against the typed contract.
4. Run frontend checks, backend regression tests, strict validation, and browser visual/accessibility verification.
5. Keep the frontend local and undeployed. Rollback removes `frontend/` and additive migrations/routes; existing backend routes and records remain compatible.

## Open Questions

- Independent benchmark approval and real-worker acceptance remain external backend gates; they do not change frontend architecture but determine when execution/result flows can be verified end-to-end.
