# Frontend Shell and Authentication

## Purpose

Provide a secure, accessible, responsive CodeAssess application shell and role-aware authentication experience grounded in the existing backend contract.

## ADDED Requirements

### Requirement: Match the approved visual system
The frontend SHALL use the approved near-black, charcoal, white, muted-gray, and golden-yellow system with reusable cards, controls, tables, badges, focus states, and responsive spacing. Green SHALL be semantic only.

#### Scenario: Desktop dashboard shell
- **WHEN** an authenticated student opens the dashboard on a desktop viewport
- **THEN** the sidebar, top bar, greeting, cards, two-column content, typography, borders, and yellow emphasis closely match the supplied reference without decorative banners or unrelated widgets

#### Scenario: Mobile navigation
- **WHEN** the viewport cannot contain the desktop sidebar
- **THEN** navigation collapses into a keyboard-accessible control and primary actions remain usable without overlap or horizontal page overflow

### Requirement: Authenticate through the existing API
The client SHALL use `/auth/login`, `/auth/register`, and `/auth/me`, preserve invitation-gated teacher registration, keep credentials out of URLs/logs, and clear local session state on logout or authentication failure.

#### Scenario: Role redirect
- **WHEN** a valid student or teacher signs in
- **THEN** the client loads `/auth/me` and routes the user to the appropriate dashboard

#### Scenario: Expired session
- **WHEN** an authenticated request returns 401
- **THEN** the client clears the token, cancels protected queries, redirects to login, and displays a non-sensitive session-expired message

### Requirement: Protect routes and actions by role
Protected pages SHALL require an authenticated user and SHALL hide or reject actions outside the current role without treating client checks as a replacement for backend authorization.

#### Scenario: Student opens teacher route
- **WHEN** a student navigates directly to a teacher-only URL
- **THEN** the client shows an authorized-route error or redirects without issuing a teacher mutation

### Requirement: Search only available resources
Global search SHALL query or filter resources actually returned by authenticated assignment and concept contracts. Empty, loading, unavailable, and no-result states SHALL be distinguishable.

#### Scenario: Search has no matching data
- **WHEN** the user searches a term that matches no loaded assignment or concept
- **THEN** the client displays no results and invents no problems, popularity, or acceptance percentages

### Requirement: Represent unsupported screenshot features honestly
Contests, discussion, notifications, and calendar navigation SHALL be disabled or labeled unavailable unless a tested backend contract exists. Controls without working behavior SHALL NOT appear active.

#### Scenario: Notifications unavailable
- **WHEN** no notification endpoint is present
- **THEN** the notification control shows a truthful empty/unavailable state and no fabricated badge count

### Requirement: Meet baseline accessibility
Pages SHALL use semantic structure, labeled controls, keyboard navigation, visible focus indicators, sufficient contrast, reduced-motion-safe interactions, and meaningful loading/error announcements.

#### Scenario: Keyboard-only navigation
- **WHEN** a user navigates the shell, dialog, forms, tabs, and tables using a keyboard
- **THEN** focus order remains logical and every actionable control can be operated without a pointer
