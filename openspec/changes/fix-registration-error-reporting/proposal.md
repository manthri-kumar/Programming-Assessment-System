# Proposal

## Why

Teacher registration failures currently surface as the generic message `request could not be completed` even though the backend returns a safe reason in its structured response. This prevents users from distinguishing an unreachable backend, an unconfigured or invalid invitation, duplicate email, invalid form data, and an unexpected server failure.

## What Changes

- Preserve the existing invitation-gated teacher registration and bearer-session architecture.
- Define safe, specific registration error messages from structured HTTP responses without exposing stack traces, credentials, tokens, configured invitation values, or database internals.
- Validate registration email and password inputs consistently at the API boundary and in the form.
- Keep the existing registration payload and endpoint compatible.
- Add backend, frontend, and API regression coverage for both student and teacher registration, duplicate accounts, invalid input, missing/invalid/unconfigured teacher invitations, login, roles, session restoration, logout, and protected-route authorization.
- Document that invitation expiry and single-use behavior are unsupported by the current static server-owned invitation configuration rather than simulating those states.

## Capabilities

### New Capabilities

- `registration-error-handling`: Secure student and invitation-gated teacher registration, validation, connectivity distinction, and safe user-facing failure reporting.

### Modified Capabilities

None. No synchronized main specifications currently exist; this capability refines the already implemented authentication behavior without changing endpoint compatibility.

## Impact

- Frontend authentication form, API error translation, and their tests.
- FastAPI registration validation/error contract and authentication tests.
- Generated OpenAPI documentation if the request schema changes observably.
- No changes to assessment agents, scoring, execution, authorization boundaries, frontend theme, or unrelated pages.
