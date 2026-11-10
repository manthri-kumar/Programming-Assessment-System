# Registration Error Handling Specification

## Purpose

Provide secure, deterministic student and invitation-gated teacher registration with actionable failure messages and consistent validation across the API and frontend.

## ADDED Requirements

### Requirement: Registration transport contract
The client SHALL send registration credentials only in a JSON body to `POST /auth/register` and SHALL distinguish a reachable API response from a network connection failure.

#### Scenario: Backend is unreachable
- **WHEN** registration fails before any HTTP response is received
- **THEN** the client SHALL display `Unable to connect to the server. Please try again.` and SHALL NOT claim that an account was created

#### Scenario: Compatible payload
- **WHEN** a student or teacher submits a valid form
- **THEN** the request SHALL contain `email`, `password`, `role`, and, only when supplied for a teacher, `teacher_registration_code`

### Requirement: Registration input validation
The API SHALL reject malformed email addresses, passwords outside the supported length, unsupported roles, and missing required teacher invitation input without creating a user.

#### Scenario: Invalid email
- **WHEN** a registration email lacks a valid local part, `@`, or domain
- **THEN** the API SHALL return HTTP 422 and the client SHALL display `Please check the entered details.`

#### Scenario: Invalid password
- **WHEN** a password is shorter than 8 characters or longer than 128 characters
- **THEN** registration SHALL be rejected without persisting the password or user

#### Scenario: Missing teacher invitation
- **WHEN** a teacher request omits the invitation code
- **THEN** the API SHALL reject the request and the client SHALL display an invitation-specific or form-validation message

### Requirement: Invitation-gated teacher creation
The API SHALL create a teacher only when a server-owned invitation value is configured and matches the supplied value using the existing constant-time comparison.

#### Scenario: Valid configured invitation
- **WHEN** a teacher supplies the configured invitation value and valid account details
- **THEN** the API SHALL return HTTP 201 and persist the user with role `teacher`

#### Scenario: Invalid invitation
- **WHEN** a supplied invitation does not match the configured value
- **THEN** the API SHALL return HTTP 403 and the client SHALL display `Invalid teacher invitation code.`

#### Scenario: Teacher registration is unconfigured
- **WHEN** no server-owned teacher invitation value is configured
- **THEN** the API SHALL return HTTP 503 and the client SHALL display `Teacher registration is currently unavailable. Please contact an administrator.`

#### Scenario: Invitation lifecycle unsupported
- **WHEN** expiry or single-use behavior is requested for the current static invitation mechanism
- **THEN** the system SHALL NOT simulate those states and documentation SHALL state that they are unsupported

### Requirement: Safe registration failure messages
The client SHALL translate only recognized registration statuses and safe structured reasons into approved messages and SHALL NOT render arbitrary backend details, stack traces, secrets, or database errors.

#### Scenario: Existing account
- **WHEN** the API returns HTTP 409 for an existing email
- **THEN** the client SHALL display `An account with this email already exists.`

#### Scenario: Unexpected server failure
- **WHEN** the API returns an unrecognized HTTP 5xx registration failure
- **THEN** the client SHALL display `Registration failed due to a server error. Please try again.`

#### Scenario: Unknown client failure
- **WHEN** the API returns another unrecognized registration failure
- **THEN** the client SHALL display `Registration failed. Please check the entered details and try again.`

### Requirement: Authentication behavior remains intact
Successful student and teacher registrations SHALL retain the existing role, login, session restoration, logout, dashboard routing, and protected-route authorization behavior.

#### Scenario: Student registration and login
- **WHEN** a valid student registers and signs in
- **THEN** `/auth/me` SHALL return role `student` and the client SHALL route to the student dashboard

#### Scenario: Teacher registration and login
- **WHEN** an authorized teacher registers and signs in
- **THEN** `/auth/me` SHALL return role `teacher` and the client SHALL route to the teacher dashboard

#### Scenario: Protected route authorization
- **WHEN** an authenticated user opens a route for the other role
- **THEN** the existing server and client authorization controls SHALL continue to reject or redirect access

