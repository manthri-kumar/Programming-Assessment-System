# Tasks

## 1. Backend registration contract

- [x] 1.1 Add bounded API-side email normalization and shape validation; verify malformed email, short/long passwords, unsupported roles, and missing teacher invitation input return 422 without creating users.
- [x] 1.2 Preserve invitation security while asserting safe structured outcomes for valid, invalid, missing, and unconfigured invitations plus duplicate email; verify roles and no unauthorized teacher creation in backend authentication tests.
- [x] 1.3 Regenerate the checked-in OpenAPI contract if the observable request schema changes and verify generated-contract equality.

## 2. Frontend failure translation

- [x] 2.1 Add a registration-specific safe error translator for network, 403 invitation, 409 duplicate, 422 validation, 503 unconfigured invitation, and unexpected failures; verify arbitrary backend details are never displayed.
- [x] 2.2 Integrate the translator and trimmed form values into the existing black-and-yellow registration form; verify student/teacher payloads and accessible error announcements without changing the layout or session architecture.

## 3. Authentication integration and regression

- [x] 3.1 Add frontend tests for valid registration, invalid email/password, duplicate email, invalid/missing invitation, unconfigured teacher registration, backend unreachable, and server failure; verify the approved messages and absence of false success.
- [x] 3.2 Run disposable API/browser flows for student and authorized teacher registration, subsequent login, stored roles, dashboard redirect, session restoration, protected-route behavior, and logout; record that invitation expiry/single-use is unsupported by the static mechanism.
- [x] 3.3 Run backend authentication and regression tests, frontend tests, TypeScript, lint, build, API integration, and strict OpenSpec validation; fix introduced failures and record actual results without exposing credentials or invitation values.

## Workflow follow-up

- Archive only after implementation review and verified acceptance.
