# Spec Delta: 01-auth-and-runtime-hardening

Capability: application-security

## ADDED Requirements

### Requirement: Fail-Closed Admin Authorization
The system SHALL never grant admin access by default and SHALL gate every admin-only endpoint on a configured admin password in addition to the session role.

#### Scenario: No passwords configured
- **WHEN** neither `SECPHO_APP_PASSWORD` nor `SECPHO_ADMIN_PASSWORD` is set and any request is made
- **THEN** `Handler.session()` returns role `"user"` (never `"admin"`) and admin endpoints (`/api/feedback-inbox`, `/api/tool-requests`, `/api/tool-build-events`) return 403.

#### Scenario: Forged admin cookie without admin password
- **WHEN** a request carries a cookie claiming `role=admin` but `SECPHO_ADMIN_PASSWORD` is unset (`ADMIN_ENABLED` is `False`)
- **THEN** `is_admin()` returns `False` and the admin endpoint returns 403.

#### Scenario: Authenticated non-admin user
- **WHEN** a logged-in normal user requests `GET /api/feedback-inbox`
- **THEN** the response is 403; an admin session returns 200.

### Requirement: Stable Session Secret
The system SHALL use a session-signing secret that survives process restarts.

#### Scenario: Secret provided by environment
- **WHEN** `SECPHO_SESSION_SECRET` or `SESSION_SECRET` is set
- **THEN** that value is used to sign sessions and `SESSION_SECRET_FROM_ENV` is `True`.

#### Scenario: No secret in environment
- **WHEN** no session-secret env var is set
- **THEN** the system reuses, or generates and persists, a token in gitignored `data/app_state/.session_secret`, so sessions remain valid across restarts.

### Requirement: Safe Request Id Parsing
The system SHALL reject a non-numeric `id` with HTTP 400 instead of raising an unhandled 500.

#### Scenario: Non-numeric id
- **WHEN** `GET /api/person?id=notanumber` (or `/api/llm-report`, `/api/llm-chat`, `/api/chat-flow`, `/api/rerank`, `/api/report-tuned`) is requested
- **THEN** `to_int()` returns the default and the handler responds 400 JSON with no traceback leaked.

### Requirement: Thread-Safe State Writes
The system SHALL serialize all writes to runtime state files so concurrent request threads cannot corrupt them.

#### Scenario: Concurrent state mutations
- **WHEN** `save_feedback`, `save_missing_tool_request`, `update_tool_request_status`, `save_generated_tools_registry`, or `append_tool_build_event` runs from multiple `ThreadingHTTPServer` threads
- **THEN** each write holds `STATE_LOCK` for the duration of the mutation.

### Requirement: Security Headers On All Responses
The system SHALL include security headers on every response, including 404s.

#### Scenario: Not-found response
- **WHEN** a `do_GET` or `do_POST` request matches no route
- **THEN** the 404 response includes `send_security_headers()` and `Content-Length: 0`.

### Requirement: Robust Runtime Configuration
The system SHALL resolve runtime configuration safely on fresh deploys and report startup state to the operator.

#### Scenario: Empty model environment variable
- **WHEN** `OPENAI_MODEL` is set but empty
- **THEN** the model id resolves to `gpt-5-mini` via `os.getenv("OPENAI_MODEL") or "gpt-5-mini"` (surfaced through `current_model()`), not `""`.

#### Scenario: Fresh deploy directories
- **WHEN** the process starts and `data/app_state` or `data/generated_artifacts` is missing
- **THEN** `ensure_state_dirs()` creates them (at import and in `main()`).

#### Scenario: Startup banner
- **WHEN** `main()` starts the server
- **THEN** it prints the model, whether the LLM key is set, whether auth and the admin password are configured, and a warning if `SECPHO_SESSION_SECRET` is unset.
