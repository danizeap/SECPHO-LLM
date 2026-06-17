# Capability: application-security

## Purpose

Keep the single-file SECPHO intelligence app (`backend_api/mvp_web_app.py`) safe to expose on the public internet for named staff: admin data stays fail-closed, named accounts gate access, the login limiter resists IP spoofing, LLM cost and slow clients are bounded, sessions are stable (fail-closed in prod), PII is redacted before the LLM, requests degrade gracefully, and runtime config/state are robust on fresh deploys.

## Requirements

### Requirement: Fail-Closed Admin Authorization
The system SHALL never grant admin access by default and SHALL gate every admin-only endpoint on configured admin credentials in addition to the session role. Admin may be configured by a `SECPHO_USERS` entry with role `admin` or by the legacy `SECPHO_ADMIN_PASSWORD`; `ADMIN_ENABLED` is true only if one of those exists.

#### Scenario: No admin configured
- **WHEN** no `SECPHO_USERS` admin entry and no `SECPHO_ADMIN_PASSWORD` exist and any request is made
- **THEN** `Handler.session()` returns role `"user"` (never `"admin"`) and admin endpoints (`/api/feedback-inbox`, `/api/tool-requests`, `/api/tool-build-events`) return 403.

#### Scenario: Forged admin cookie without admin configured
- **WHEN** a request carries a cookie claiming `role=admin` but `ADMIN_ENABLED` is `False`
- **THEN** `is_admin()` returns `False` and the admin endpoint returns 403.

#### Scenario: Authenticated non-admin user
- **WHEN** a logged-in normal user requests `GET /api/feedback-inbox`
- **THEN** the response is 403; an admin session returns 200.

### Requirement: Named-Account Authentication
The system SHALL support per-user named accounts parsed from `SECPHO_USERS` (`email|role|pbkdf2_sha256$...` entries joined by `;`), verifying passwords with PBKDF2-SHA256 (600k iterations) in constant time. The shared `SECPHO_APP_PASSWORD` is only a fallback when no named users are configured.

#### Scenario: Valid named login
- **WHEN** a user submits an email + password matching a `SECPHO_USERS` entry
- **THEN** `check_credentials()` returns `(role, email)` and a signed session cookie carrying that role and `sub` is issued.

#### Scenario: Wrong password
- **WHEN** the password does not verify against the stored PBKDF2 hash
- **THEN** login fails (401) and the attempt is logged.

### Requirement: Stable Session Secret
The system SHALL use a session-signing secret that survives process restarts, and SHALL FAIL CLOSED when running behind a trusted proxy without one. When `TRUST_PROXY` is set (e.g. the `RENDER` environment) and no session secret is provided via the environment, `main()` exits at startup rather than serving with an ephemeral secret.

#### Scenario: Secret provided by environment
- **WHEN** `SECPHO_SESSION_SECRET` or `SESSION_SECRET` is set
- **THEN** that value is used to sign sessions and `SESSION_SECRET_FROM_ENV` is `True`.

#### Scenario: Behind a proxy with no env secret
- **WHEN** `TRUST_PROXY` is true and no session-secret env var is set
- **THEN** the process exits at startup (fail closed) instead of serving with a non-persistent secret.

#### Scenario: Local run with no env secret
- **WHEN** `TRUST_PROXY` is false and no session-secret env var is set
- **THEN** the system reuses, or generates and persists, a token in gitignored `data/app_state/.session_secret`, so local sessions remain valid across restarts.

### Requirement: Spoof-Resistant Client IP for Rate Limiting
The system SHALL derive the client IP for rate limiting from the RIGHTMOST `X-Forwarded-For` entry only when `TRUST_PROXY` is set, and from the socket peer otherwise, so a client cannot bypass the login limiter by forging `X-Forwarded-For`.

#### Scenario: Forged X-Forwarded-For
- **WHEN** an attacker rotates the leftmost `X-Forwarded-For` values while the proxy-appended rightmost entry stays constant
- **THEN** the login limiter keys on the rightmost entry and returns 429 after the threshold.

### Requirement: Bounded LLM Cost
The system SHALL cap total daily OpenAI calls via `LLM_DAILY_BUDGET` (default 1000), enforced in both `call_llm` and `call_agent_step`.

#### Scenario: Budget exhausted
- **WHEN** the daily LLM call count reaches `LLM_DAILY_BUDGET`
- **THEN** further LLM calls return a fallback and do not hit the API.

### Requirement: CSRF Defense on POSTs
The system SHALL reject cross-origin state-changing POSTs via a same-origin check, in addition to `SameSite=Lax` cookies.

#### Scenario: Cross-origin POST
- **WHEN** a POST arrives with an `Origin` header that does not match the host
- **THEN** `same_origin()` fails and the request is rejected with 403.

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

### Requirement: Abuse & Disclosure Hardening
The system SHALL bound slow-client connections, keep rate-limiter state concurrency-safe and size-bounded, minimize health disclosure, and log access and errors.

#### Scenario: Slowloris
- **WHEN** a client holds a connection open without completing the request
- **THEN** `Handler.timeout` (30s) closes the inbound socket.

#### Scenario: Health endpoint
- **WHEN** `GET /health` is requested
- **THEN** the response is exactly `{"status":"ok"}` with no counts or internal state.

#### Scenario: Unhandled error
- **WHEN** a request handler raises
- **THEN** the wrapper logs it via `LOGGER` and returns 500 with no traceback to the client; normal requests are access-logged.

### Requirement: PII Redaction Before LLM
The system SHALL strip email/PII keys from any object before it is sent to the LLM.

#### Scenario: Object sent to the model
- **WHEN** tool output or a payload is passed to an LLM call
- **THEN** `redact_pii()` removes email fields first.

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
