# Proposal

## Why

The teacher assignment form accepts values that the authoritative `POST /assignments` contract rejects, most notably arbitrary concept identifiers, and then replaces FastAPI's useful validation detail with the generic message `request could not be completed`. This makes a recoverable validation error look like an unexplained integration failure even though the default schema-compatible payload creates an assignment successfully.

## What Changes

- Align assignment-form validation and serialization with the existing FastAPI request schema without weakening server-side validation.
- Source allowed concept identifiers from the backend Knowledge Graph instead of accepting unchecked free text or hardcoding a duplicate list.
- Present safe, field-specific messages for FastAPI validation errors, unknown concepts, duplicate assignment data, authorization failures, and connectivity failures.
- Preserve the existing `POST /assignments` request shape, teacher ownership enforcement, hidden-test protection, and student visibility rules.
- Add regression coverage for valid creation, invalid fields, persistence, teacher ownership, student visibility, and the real browser form flow.

## Capabilities

### New Capabilities

- `assignment-authoring`: Defines schema-aligned, authorized assignment creation and actionable validation feedback across the teacher frontend and backend.

### Modified Capabilities

None. The repository has no synchronized main specifications; this capability formalizes and strengthens behavior previously described only inside the completed frontend change.

## Impact

- Frontend teacher assignment form, API error mapping, validation, and tests.
- Existing FastAPI assignment endpoint tests and, only if required by acceptance tests, narrowly scoped request validation improvements that remain backward compatible.
- Browser coverage for assignment creation through the actual UI and subsequent teacher/student visibility.
- No changes to the two-agent architecture, secure execution policy, hidden-test response filtering, authentication, or authorization.
