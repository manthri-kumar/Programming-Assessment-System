# Design

## Context

See `proposal.md` for motivation. The React client posts the correct payload to `/api/auth/register`, and Vite proxies `/api` to `127.0.0.1:8000` by default. FastAPI returns a sanitized generic `error.message` for HTTP exceptions and places its safe route reason in `detail`. The Axios interceptor retains `detail`, but the registration form displays only `Error.message`. The screenshot therefore loses the actionable reason. Separately, the local health probe confirmed no backend was currently reachable on port 8000.

## Goals / Non-Goals

**Goals:**

- Preserve the current endpoint, payload, role authorization, constant-time invitation comparison, session handling, and theme.
- Give registration-specific, safe messages for connectivity, validation, invitation configuration/mismatch, duplicates, and server failures.
- Enforce a minimal bounded email-shape check at the API boundary.
- Verify registration and subsequent authentication for both roles.

**Non-Goals:**

- Invitation expiry, single-use invitations, invitation persistence, password reset, email verification, or automatic login after registration.
- Displaying arbitrary server `detail` values.
- Changing unrelated global error messages, assessment behavior, agents, or frontend layout.

## Decisions

### Use a registration-specific error translator

The form will translate `ApiError` using status plus a small whitelist of recognized safe detail strings. Network failures use status zero. Unknown details are ignored. This is safer than globally promoting `detail` to `Error.message`, which could expose sensitive information from unrelated endpoints.

### Retain the sanitized backend envelope

The API keeps the existing correlated error envelope and generic top-level message. Existing clients and security tests remain compatible. Route-specific reasons stay in `detail`, while the frontend owns user-friendly wording.

### Validate email shape without a new dependency

The bounded API request model will trim email input and require a non-whitespace local part, `@`, and dotted non-whitespace domain. This matches the supported academic workflow without adding a global package solely for internationalized email validation. SQLite remains authoritative for case-insensitive duplicate detection through normalized storage.

### Keep static invitation semantics explicit

The existing environment-owned invitation is reusable and has no expiry metadata. Missing and mismatched values are tested; expired/used states are documented as not applicable rather than fabricated.

## Risks / Trade-offs

- **[Conservative email validation rejects uncommon valid addresses]** → Document the supported shape and keep validation bounded and deterministic.
- **[Backend detail wording changes could break message selection]** → Cover the backend response and frontend translation together with contract tests; status-based safe fallbacks remain useful.
- **[A stopped backend can resemble configuration failure to users]** → Network-without-response has its own message and browser/API integration verifies the distinction.
- **[Duplicate-email messaging can reveal account existence]** → This is explicitly requested for registration usability and reveals no credentials or account data beyond the submitted address.

## Migration Plan

No database migration is required. Deploy backend validation and frontend translation together, regenerate the checked-in OpenAPI document if its schema changes, and retain the prior client fallback for non-registration requests. Rollback consists of reverting these source changes; existing users and sessions remain compatible.
