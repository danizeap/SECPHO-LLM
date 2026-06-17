# Verification

## Change

01-auth-and-runtime-hardening

## Automated Checks

- [x] `python -m py_compile backend_api/mvp_web_app.py` passed (module compiles; import-time `ensure_state_dirs()` and config block load cleanly).

## Manual Checks

Live HTTP test against a running instance with `SECPHO_APP_PASSWORD` and `SECPHO_ADMIN_PASSWORD` set:

- [x] `GET /` unauthenticated returns 303 redirect to `/login`.
- [x] Login with a wrong password returns 401.
- [x] Login with the valid password issues a signed session cookie.
- [x] `GET /api/feedback-inbox` as a normal `"user"` returns 403 (the core fail-closed fix).
- [x] `GET /api/feedback-inbox` as admin returns 200.
- [x] `GET /api/person?id=notanumber` returns 400 (no 500 traceback).
- [x] The tool-build chart loop still returns 200 (no regression to existing endpoints).
- [x] Independent `drydock:verifier` review returned VERIFIED: admin surface is genuinely fail-closed (double-gated) with no regression to existing endpoints.

## Documentation Updates

- [ ] README or user-facing docs updated, if needed.
- [ ] Project context updated, if needed.
- [x] Specs updated (delta spec + living `application-security` capability spec).

## Result

PASS -- admin endpoints are fail-closed and double-gated, bad ids return 400, state writes are locked, and runtime config/dirs are robust; verified by py_compile, live HTTP checks, and an independent verifier review.
