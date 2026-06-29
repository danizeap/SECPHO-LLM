# Capability: access-control

## Purpose

Role-based access control plus a self-service user manager so SECPHO's own team owns who can use the
tool and exactly what each person can see and do. Three roles (`dev` > `admin` > `user`); admins
create org users and grant per-user access to data and tools by checkbox; enforcement is server-side
and fail-closed. The roster persists with zero new datastore — it lives in the `SECPHO_USERS`
environment variable, written at runtime through a single swappable writer seam.

## Requirements

### Requirement: Three-tier role model
The system SHALL support exactly three roles with precedence `dev > admin > user`. `dev` holds
everything including system internals (the tool loop, feedback, scoring console); `admin` holds all
data and tools plus user management; `user` holds only the grants assigned to them. The session
cookie SHALL carry the role, and `parse_session_cookie` SHALL accept only `user`/`admin`/`dev`.
`is_admin()` SHALL be true for `admin` and `dev`; `is_dev()` SHALL be true only for `dev`. The role
used for authorization SHALL be re-derived PER REQUEST from the live roster for named accounts (as
grants are), so a demotion or deletion takes effect on the next request rather than lingering until
the cookie expires; in named-account mode a session whose account no longer exists has no role.

#### Scenario: Revoked role takes effect without waiting for cookie expiry
- **WHEN** a named account is demoted or deleted in the roster while its session cookie is still valid
- **THEN** authorization re-derives the role from the live roster, so the stale cookie no longer
  grants the old privileges (a deleted account is treated as unprivileged).

#### Scenario: Dev outranks admin outranks user
- **WHEN** access is checked with `role_at_least`
- **THEN** `dev` satisfies `admin` and `dev`; `admin` satisfies `admin` but not `dev`; `user`
  satisfies only `user`; and a missing session satisfies nothing (fail-closed).

#### Scenario: Dev role survives the signed cookie
- **WHEN** a `dev` logs in
- **THEN** the signed session cookie round-trips the `dev` role and the dev reaches admin surfaces.

### Requirement: Per-user grant catalog, fail-closed enforcement
The system SHALL define a fixed grant catalog over data sources and tools. `admin`/`dev` implicitly
hold the whole catalog; a `user` holds exactly their assigned keys. Grants SHALL be resolved PER
REQUEST from the live roster (keyed by the cookie's email), not stored in the cookie, so a grant
change takes effect at the next redeploy rather than lingering until the cookie expires. Every agent
tool SHALL map to a required grant and `dispatch_tool` SHALL refuse an ungranted tool with a
`forbidden` result; `/api/agent` SHALL require `tool.chat`; missing or unparseable grants SHALL deny.
Invariant: `/api/agent` is the ONLY production entry into the agent loop and ALWAYS resolves and
threads the caller's grants into `ctx`. `dispatch_tool` skips its per-tool check only when `ctx`
carries no `grants` key, which by construction happens solely for internal/test callers — never for
an authenticated request.

#### Scenario: Ungranted tool is refused
- **WHEN** the agent calls a tool the caller was not granted (e.g. `list_projects` without
  `data.proyectos`)
- **THEN** `dispatch_tool` returns `{"error": "forbidden", ...}` and the tool never executes.

#### Scenario: Every tool is gated
- **WHEN** the registered agent tools are enumerated
- **THEN** each one has an entry in `TOOL_REQUIRED_GRANT` (a tool cannot ship ungated).

#### Scenario: Grants resolve from the live roster
- **WHEN** a named user's grants are resolved for a request
- **THEN** they come from the current `USERS` map, while a shared-password session falls back to the
  role's default grants and open dev-mode gets the non-sensitive default set.

#### Scenario: Heuristic fallback is gated and PII-safe
- **WHEN** the LLM is unavailable or returns empty and the request falls to the heuristic engine
- **THEN** the fallback requires the baseline data grant before serving any socio/people data and
  redacts personal emails from its response, so it never serves what the gated agent path withholds.

### Requirement: Sensitive grants default-off and admin-settable only
The system SHALL mark financial, PII/contacts, scoring-console, and feedback grants as sensitive.
A newly created `user` SHALL receive only non-sensitive grants by default; sensitive grants SHALL be
grantable only by an admin/dev explicitly checking them. The standalone `/tuning` scoring console
SHALL require `admin`/`dev` or the `tool.scoring` grant; the inline tuner stays open to chat users.

#### Scenario: New user gets no sensitive access by default
- **WHEN** an admin creates a user without ticking sensitive boxes
- **THEN** the user holds the non-sensitive defaults and none of financial/PII/scoring/feedback.

### Requirement: Self-service user management
The system SHALL expose admin/dev-only `GET`/`POST /api/org/users` to list, create, update, delete,
and reset-password org users. Creation SHALL require a `@secpho.org` email and SHALL mint a strong
one-time password server-side, return it ONCE, and store only its pbkdf2 hash — never logging or
persisting the plaintext, never exposing password hashes in any response. Each change SHALL write an
action-log line (no secrets). Non-admin callers SHALL receive 403.

#### Scenario: Admin creates a secpho user
- **WHEN** an admin posts a create for `nombre@secpho.org` with a grant selection
- **THEN** the response carries a one-time password, the new user appears in the listing with those
  grants, and no password hash is exposed.

#### Scenario: Non-secpho email rejected
- **WHEN** a create uses a non-`@secpho.org` email
- **THEN** the endpoint responds 400 `email_must_be_secpho`.

#### Scenario: Non-admin is refused
- **WHEN** a `user` calls `GET` or `POST /api/org/users`
- **THEN** the endpoint responds 403.

### Requirement: Authorization guards (dev-protection + lockout)
The system SHALL prevent privilege-related foot-guns: only a `dev` may create/modify/delete a `dev`
account or assign the `dev` role; the system SHALL never delete or demote the LAST remaining
admin-or-dev account. Writes SHALL serialize under a lock and take a fresh read of the authoritative
roster before writing when the writer is enabled.

#### Scenario: Admin cannot assign or touch dev
- **WHEN** an `admin` tries to create a `dev` or delete an existing `dev`
- **THEN** the action is refused with `dev_requires_dev`.

#### Scenario: Last privileged account is protected
- **WHEN** a delete or demotion would remove the only remaining admin-or-dev
- **THEN** the action is refused with `would_lock_out`.

### Requirement: Zero-new-persistence roster store
The system SHALL store the roster in the `SECPHO_USERS` environment variable and write it at runtime
through a single seam (`persist_users` → `render_env.update_users_env`) so admins without a hosting
dashboard can self-serve. The serialized form SHALL round-trip with the parser and SHALL stay
backward compatible with legacy 3-field entries. The Render writer SHALL be flag-gated on
`RENDER_API_KEY` + `RENDER_SERVICE_ID`; when disabled, changes apply in-memory only and the UI SHALL
say so. The privileged `RENDER_API_KEY` SHALL never appear in the repo, client, LLM, or logs.

#### Scenario: Roster round-trips
- **WHEN** a roster is serialized and parsed back
- **THEN** roles and grants are preserved (admin/dev as implicit-all; user as explicit keys).

#### Scenario: Writer disabled degrades safely
- **WHEN** the Render writer is not configured
- **THEN** a user change still applies in-memory for the running instance and the response/UI flags
  that it will not survive a redeploy.

#### Scenario: Unparseable or empty authoritative read fails closed
- **WHEN** a fresh roster read returns an unrecognized success shape, or an empty roster while a
  populated one is held in memory
- **THEN** the read is treated as indeterminate (the known roster is kept) or the write is refused —
  the system never computes a write against a guessed-empty roster that would clobber every
  credential.

### Requirement: data.financiero gates the financial tools
The `data.financiero` grant SHALL gate the four financial tools (`financial_overview`,
`socio_financials`, `cuota_status`, `list_invoices`) via `TOOL_REQUIRED_GRANT`, enforced fail-closed
in `dispatch_tool`. Financial data SHALL NOT be reachable through any non-gated path: it is excluded
from the heuristic fallback and from the matchmaking report.

#### Scenario: Granted vs ungranted financial access
- **WHEN** the same financial tool is invoked with and without `data.financiero`
- **THEN** the granted caller gets the computed result; the ungranted caller gets `forbidden` and the
  tool never executes.

### Requirement: Two-tier gating for health/churn
Engagement tools (`at_risk_socios`, `socio_health`, `health_overview`) SHALL require `data.socios`;
the churn-reason tool (`churn_breakdown`) SHALL require `data.financiero`, because the reasons are
candid internal assessments of why members left. Reading membership status to restrict
`at_risk_socios`/`health_overview` to active members exposes no reason or amount and is permitted at
the `data.socios` tier.

#### Scenario: Churn reasons need the financial tier
- **WHEN** a `data.socios`-only caller invokes `churn_breakdown`
- **THEN** `dispatch_tool` returns `forbidden`; only a `data.financiero` holder reaches the candid
  churn reasons.
