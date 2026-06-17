# Plan

## Change

01-auth-and-runtime-hardening

## Approach

Concrete steps taken in `backend_api/mvp_web_app.py`:

1. Make `Handler.session()` open-mode return `{"role": "user", "auth_disabled": True}` instead of a synthetic admin, so the app stays usable without passwords but never auto-grants admin.
2. Add `ADMIN_ENABLED = bool(ADMIN_PASSWORD)` and require it in `is_admin()` (`ADMIN_ENABLED and session.role == "admin"`), double-gating admin so a forged `role=admin` cookie is inert when no admin password is set.
3. Add `_load_or_create_session_secret()`: read `SECPHO_SESSION_SECRET`/`SESSION_SECRET`, else reuse/persist a generated token in `data/app_state/.session_secret`; fall back to an in-memory token only on `OSError`. Track `SESSION_SECRET_FROM_ENV`.
4. Add `to_int(value, default=None)` and use it in `/api/person`, `/api/llm-report`, `/api/llm-chat`, `/api/chat-flow` (and `/api/rerank`, `/api/report-tuned`, and the POST id path) so a bad id returns 400 JSON.
5. Add `STATE_LOCK = threading.Lock()` and wrap every state-file write: `save_feedback`, `save_missing_tool_request`, `update_tool_request_status`, `save_generated_tools_registry`, `append_tool_build_event`.
6. Emit `send_security_headers()` + `Content-Length: 0` on the `do_GET` and `do_POST` 404 branches.
7. Change `OPENAI_MODEL` to `os.getenv("OPENAI_MODEL") or "gpt-5-mini"` and route model selection through `current_model()`.
8. Add `ensure_state_dirs()` (creates `data/app_state` + `data/generated_artifacts`), called at import (line 223) and at the top of `main()`.
9. Add a `main()` startup banner: model, LLM key presence, auth enabled + admin-password presence, and a warning when `SECPHO_SESSION_SECRET` is unset.

## Files Expected To Change

- `backend_api/mvp_web_app.py`:
  - Config block: `OPENAI_MODEL`, `_load_or_create_session_secret()`, `SESSION_SECRET`, `SESSION_SECRET_FROM_ENV`, `AUTH_REQUIRED`, `ADMIN_ENABLED`, `STATE_LOCK`, `current_model()`, `ensure_state_dirs()`, `to_int()`.
  - `Handler.session()`, `Handler.is_admin()`, `Handler.send_security_headers()`.
  - id-parsing handlers in `do_GET`/`do_POST` and the two 404 branches.
  - State writers: `save_missing_tool_request`, `update_tool_request_status`, `save_generated_tools_registry`, `append_tool_build_event`, `save_feedback`.
  - `main()`.
- `render.yaml`: confirms `SECPHO_APP_PASSWORD`, `SECPHO_ADMIN_PASSWORD`, `SECPHO_SESSION_SECRET` are declared as `sync: false` secrets (no code there).

## Risks

- Existing endpoints regress under the new gating. Mitigated: live HTTP test confirmed normal flows (login, person report, tool-build chart loop) still 200; only non-admins on admin endpoints now 403.
- Persisting the session secret to disk could leak it. Mitigated: written under `data/app_state/`, which is gitignored, and env var takes precedence in production.
- `STATE_LOCK` serializes all state writes and could bottleneck. Accepted: writes are infrequent (feedback, tool requests) and brief; correctness outweighs throughput here.

## Rollback

- Per-function git revert of the listed functions in `backend_api/mvp_web_app.py` restores prior behavior.
- The admin hardening is effectively config-driven: leaving `SECPHO_ADMIN_PASSWORD` unset keeps admin disabled (fail-closed) rather than open; setting it restores admin access. No data migration to undo.
- Removing `SECPHO_SESSION_SECRET` falls back to the persisted file secret, so rollback does not invalidate sessions.
