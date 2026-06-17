# Decision Log

## Change

01-auth-and-runtime-hardening

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-16 | Fail-closed admin: open mode grants role `"user"`, and `is_admin()` also requires `ADMIN_ENABLED` (a configured admin password). | Admin data (emails, feedback inbox, tool requests) must never be exposed by default; double-gating means even a forged `role=admin` cookie cannot unlock admin without a real password. | Require auth for all access (rejected: breaks frictionless local dev); trust the cookie role alone (rejected: forgeable / not fail-closed). |
| 2026-06-16 | Keep the app usable without any password for local dev, gating only admin data. | Preserve fast local iteration while protecting sensitive endpoints before public exposure. | Force a password in all environments (rejected: too much dev friction). |
| 2026-06-16 | Resolve the session secret from env, else persist a generated token to gitignored `data/app_state/.session_secret`. | A per-process random secret invalidated every session on restart and broke multi-instance; a persisted fallback keeps sessions stable even when the env var is unset. | Env-only secret (rejected: app unusable until an env var is set, no graceful fallback); per-process random (the original bug). |
| 2026-06-16 | Parse ids via `to_int()` returning 400 on failure instead of bare `int()`. | A non-numeric `?id=` raised an unhandled 500 with a traceback (information leak) and no security headers. | Leave 500 handling to a generic error page (rejected: still leaks and is wrong status). |
| 2026-06-16 | Serialize all state-file writes behind a single `STATE_LOCK`. | `ThreadingHTTPServer` runs handlers concurrently; unlocked appends/rewrites of the inbox, JSONL, and registry risked corruption. | Per-file locks (rejected: unnecessary complexity for low write volume). |
