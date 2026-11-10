# Proposal

## Why

CodeAssess has a tested FastAPI/SQLite backend and exactly two deterministic assessment agents, but no frontend exists. Students and teachers need an accessible, responsive interface that consumes the real authenticated APIs, presents unavailable execution honestly, and follows the approved dark/gold dashboard reference without fabricating data.

## What Changes

- Add one React/TypeScript/Vite frontend with a reusable dark/gold design system, responsive application shell, protected routing, and centralized typed API client.
- Implement authentication and role-aware student/teacher navigation against the existing bearer-token API, including invitation-gated teacher registration and session-expiry handling.
- Implement student dashboard, assignments, coding workspace, assessment/report/feedback views, submissions, progress, learning graph, recommendations, bookmarks, and supported settings using real API data and truthful empty/unavailable states.
- Implement teacher dashboard, assignment creation/editing, submission review, rubric/test configuration, and analytics with existing ownership rules.
- Add the smallest compatible backend contracts needed for client-safe concept-graph reads, deadlines, bookmarks, drafts, activity, and profile display only where those behaviors are approved and testable; unsupported contests/discussion/notifications remain clearly unavailable.
- Preserve exactly `ImplementationEvaluationAgent` followed by `FeedbackAgent`; never execute source in the browser or host and never convert unavailable isolation into simulated success.
- Add frontend unit/route/API tests, production build/lint/type checks, backend regressions, and desktop/tablet/mobile browser verification against the supplied screenshot.
- **BREAKING:** none. Existing API paths and `assessment-report-v2` remain compatible; any added fields/endpoints are additive.

## Capabilities

### New Capabilities

- `frontend-shell-auth`: Application shell, design system, authentication, protected routes, search, navigation, responsive behavior, and truthful unsupported-feature states.
- `student-assessment-experience`: Student dashboard, assignments, workspace, submission, evaluation, report, feedback, history, progress, bookmark, and recommendation experiences.
- `teacher-assessment-experience`: Teacher dashboard, assignment/rubric/test management, owned-submission review, and analytics.
- `learning-visualization`: Client-safe Knowledge Graph, prerequisite paths, weak-concept evidence, recommendations, and progress visualization.
- `frontend-support-contracts`: Additive client-safe API contracts for missing metadata and persistence needed by approved frontend behavior.

### Modified Capabilities

None. No capabilities have been archived into the main OpenSpec store; the active backend change remains the functional source of truth and is not rewritten by this frontend change.

## Impact

Adds a single `frontend/` application and project-local JavaScript dependencies. It consumes existing `/auth`, `/assignments`, `/submissions`, `/student/progress`, `/teacher/analytics`, `/health`, and `/ready` routes. Small additive FastAPI/SQLite changes may be required for concept graph reads, assignment deadlines/descriptions, bookmarks, drafts, activities, and safe profile display. Backend security, role ownership, report schemas, fail-closed execution, and all existing Python tests must remain intact. No deployment, external LLM, social login, frontend code execution, or production data is introduced.
