# Decision Log

## Change

security-remediation

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-17 | Trust the RIGHTMOST X-Forwarded-For entry, only when `TRUST_PROXY` (RENDER) is set | Render's proxy appends the real client IP as the rightmost entry; the client controls only leftmost entries, so trusting leftmost let an attacker spoof their IP and bypass the login rate limiter | Trust leftmost (rejected: client-spoofable); always trust socket peer (rejected: behind a proxy that's the proxy IP, collapsing all users into one bucket) |
| 2026-06-17 | Named accounts via `SECPHO_USERS` env (`email\|role\|pbkdf2` hash), not a DB | App is CSV-only with no database and ~3 staff users; env config stays stateless and avoids adding a datastore | Add a user DB (rejected: over-engineering for 3 users); keep shared password (rejected: no per-user accountability) |
| 2026-06-17 | PBKDF2-SHA256, 600k iterations | OWASP-aligned, stdlib-only (`hashlib`), no native dependency | bcrypt/argon2 (rejected: extra dependency on a stdlib-only app) |
| 2026-06-17 | Fail closed: exit on boot if `TRUST_PROXY` and no session secret from env | Prevents a public Render deploy from running with an ephemeral/regenerating session secret that silently breaks sessions and weakens cookie integrity | Warn-and-continue (rejected: insecure default in prod) |
| 2026-06-17 | Global daily LLM call budget (`LLM_DAILY_BUDGET`) | Bounds OpenAI cost / cost-based DoS from the agent's multi-call loops | Rely on per-IP rate limits only (rejected: they don't bound total spend) |
| 2026-06-17 | Origin-check CSRF (`same_origin`) + SameSite=Lax, not per-form tokens | Stateless app; Origin check + SameSite gives adequate CSRF defense for a staff tool without session-stored tokens | Synchronizer tokens (deferred: heavier; revisit for broad launch) |
| 2026-06-17 | Closed-pilot GO; broad launch stays gated on Gates 14 / 18-feedback | Gates 17 (logging) and 18 (session secret) are now resolved; GDPR notice/retention/DSR (14) and durable feedback (18) are only required for broad/external use | Block everything until GDPR done (rejected: disproportionate for an internal staff pilot over SECPHO's own data) |
| 2026-06-17 | Migrate hosting off WeCollabify onto the owner's personal accounts: new INDEPENDENT (non-forked) repo `danizeap/SECPHO-LLM` + personal Render service, git history scrubbed of WeCollabify authorship, hardened app deployed live (`4b855ef`) and smoke-tested | The app must run on owner-controlled infrastructure fully decoupled from the prior org; a brand-new repo + history scrub removes all WeCollabify provenance (no fork link, no commit authorship) | Keep the WeCollabify fork `danizeap/SECPHO` (rejected: retains fork link); keep the WeCollabify Render service (rejected: wrong owner) — see LGF `launch-decision.md` for the deploy evidence |
