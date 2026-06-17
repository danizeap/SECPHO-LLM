# Brief

## Change

01-auth-and-runtime-hardening

## User Need

SECPHO needs to access the intelligence app over the public internet without exposing member emails, the feedback inbox, or tool-build internals to non-admin users, and without the server 500-ing or losing sessions under normal use.

## Problem

The single-file app (`backend_api/mvp_web_app.py`) was wide open and fragile before exposure:

- With neither `SECPHO_APP_PASSWORD` nor `SECPHO_ADMIN_PASSWORD` set, `AUTH_REQUIRED` was `False` and `Handler.session()` returned a synthetic admin, so admin-only endpoints (member emails, feedback inbox, tool requests) were public.
- `SESSION_SECRET` fell back to a per-process random token, invalidating every session on each restart and breaking multi-instance deploys.
- Handlers parsed `?id=` with bare `int()`, so a non-numeric id raised an unhandled 500 with a traceback (info leak).
- State files (`feedback_inbox.md`, `*.jsonl`, the tools registry JSON) were written from multiple `ThreadingHTTPServer` threads with no lock (corruption risk).
- 404 responses sent no security headers.
- `OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")` returned `""` when the env var was set-but-empty (as in the local `.env`), so every LLM call used an empty model id and failed.
- `data/app_state` and `data/generated_artifacts` did not exist on a fresh Render deploy.

## Scope

In scope:

- Fail-closed admin gating in `Handler.session()` / `is_admin()`.
- Stable, persisted session secret.
- Safe `?id=` parsing returning 400 instead of 500.
- A write lock around all state-file mutations.
- Security headers on 404 responses.
- Empty-env-var-safe model id resolution.
- Auto-creation of runtime state directories.
- A startup banner reporting model, LLM key, auth, and session-secret status.

Out of scope:

- Login/session cookie signing mechanism itself (already present).
- Rate limiting (already present).
- Recommendation engine, scoring, or LLM prompt behavior.
- Any frontend redesign.

## Acceptance Criteria

- [x] With no passwords set, the app is usable but `session()` role is `"user"`; admin endpoints return 403.
- [x] Admin endpoints are double-gated: a forged `role=admin` cookie cannot unlock admin when no admin password is configured (`ADMIN_ENABLED` is `False`).
- [x] The session secret is read from `SECPHO_SESSION_SECRET`/`SESSION_SECRET`, else persisted to `data/app_state/.session_secret`, so sessions survive restarts.
- [x] `GET /api/person?id=notanumber` returns 400 JSON, not a 500 traceback.
- [x] Every state-file write is wrapped in `STATE_LOCK`.
- [x] 404 responses include security headers and `Content-Length: 0`.
- [x] A set-but-empty `OPENAI_MODEL` resolves to `gpt-5-mini`, not `""`.
- [x] `data/app_state` and `data/generated_artifacts` are created at import and in `main()`.
- [x] `main()` prints a startup banner with model, LLM key presence, auth + admin-password state, and a session-secret warning.

## Impact Areas

- Backend: Auth gating, request parsing, thread safety, startup, and config resolution in `backend_api/mvp_web_app.py`.
- Frontend: None.
- Data model: None.
- API: Error contract hardened — bad `?id=` now returns 400 JSON; admin endpoints return 403 for non-admins. No endpoint added or removed.
- AI/model behavior: None functional; only fixes empty-model-id resolution so LLM calls use a valid model.
- Documentation: This packet (retroactive); startup banner serves as operator guidance.
- Operations/security: Fail-closed admin, stable session secret, security headers on 404, state-dir creation; env vars `SECPHO_APP_PASSWORD`, `SECPHO_ADMIN_PASSWORD`, `SECPHO_SESSION_SECRET`.

## Open Questions

None.
