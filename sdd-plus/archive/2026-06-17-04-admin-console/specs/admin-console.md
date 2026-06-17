Capability: admin-console

## ADDED Requirements

### Requirement: Admin console page

The system SHALL serve an admin console at `GET /admin`, accessible only to an
authenticated admin session, that renders captured chat feedback and the
tool-learning loop in one read-only page (`ADMIN_HTML`).

#### Scenario: Admin opens the console
- **WHEN** an authenticated admin session requests `GET /admin`
- **THEN** the system serves the `ADMIN_HTML` page, which loads the feedback
  inbox from `/api/feedback-inbox` and the tool requests from
  `/api/tool-requests` and renders them in two sections

#### Scenario: Unauthenticated request
- **WHEN** an unauthenticated client requests `GET /admin`
- **THEN** the system redirects to `/login`

#### Scenario: Non-admin authenticated session
- **WHEN** an authenticated non-admin ("user") session requests `GET /admin`
- **THEN** the system redirects to `/` and does not serve the admin page

### Requirement: Admin-only data endpoints

The system SHALL restrict the admin data endpoints `/api/feedback-inbox`,
`/api/tool-requests`, and `/api/tool-build-events` to admin sessions, returning
`403 forbidden` otherwise.

#### Scenario: Non-admin calls an admin endpoint
- **WHEN** an authenticated non-admin session requests `/api/tool-requests`
  (or `/api/feedback-inbox` or `/api/tool-build-events`)
- **THEN** the system responds with HTTP 403 and body `{"error": "forbidden"}`

### Requirement: Observable data state via health endpoint

The system SHALL expose a public `GET /health` endpoint that reports liveness
and the loaded dataset counts without exposing any sensitive records.

#### Scenario: Operator checks health
- **WHEN** any client requests `GET /health`
- **THEN** the system returns JSON with `status`, `llm_available`, `model`,
  `auth_required`, `admin_enabled`, and a `counts` object containing
  official_socios, people, members, events, retos, subscribers, and matches,
  and no record-level or secret data

### Requirement: Admin console entry point in chat

The system SHALL show an "Admin console" link to `/admin` in the chat sidebar,
localized for English and Spanish.

#### Scenario: User views the chat sidebar
- **WHEN** a user views the chat UI (`CHAT_HTML`)
- **THEN** the sidebar shows an "Admin console" block linking to `/admin`,
  in the active language (EN/ES)
