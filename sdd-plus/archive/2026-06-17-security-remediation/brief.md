# Brief

## Change

security-remediation

## User Need

The app is deployed on the public internet (Render) for ~3 named SECPHO staff
users and processes SECPHO member PII. It must be safe to reach from the internet
without a security incident, even though it is staff-only.

## Problem

A LaunchGuardian (22-gate) review plus a 6-agent adversarial audit of the
internet-deploy work found exposure gaps. Most critically, an X-Forwarded-For
trust bug let a client spoof its IP and bypass the login rate limiter (unlimited
password brute-force). Other gaps: unbounded OpenAI cost, no slowloris bound, a
rate-limiter race + unbounded growth, an information-leaking `/health` endpoint,
no CSRF defense beyond SameSite, a no-op access log, shared-password (not
per-user) auth, and an ephemeral session secret that broke sessions on redeploy.

## Scope

In scope:

- Named-account auth (per-user email+password+role) replacing shared passwords.
- Trustworthy client-IP derivation behind Render's proxy (fix the brute-force bypass).
- Global LLM cost cap; slowloris socket bound; rate-limiter locking + eviction.
- CSRF (same-origin) defense on POSTs; minimal `/health`; access + error logging.
- PII redaction before LLM; prompt-injection rule in agent instructions.
- Dependency CVE bump + CI security workflow; named-account Render blueprint.

Out of scope:

- GDPR privacy notice / retention / data-subject-request path (Gate 14) — required
  only before BROAD/public launch, not this closed staff pilot.
- Durable feedback storage (Gate 18 feedback) — feedback still on ephemeral disk.
- Object-level authorization between staff users (single internal trust group).

## Acceptance Criteria

- [x] Login brute-force cannot be bypassed by spoofing X-Forwarded-For.
- [x] Per-user named accounts with hashed passwords and roles; auth fail-closed on Render.
- [x] OpenAI spend is bounded by a global daily call budget.
- [x] Slowloris bounded; rate limiter is concurrency-safe and bounded in size.
- [x] Cross-origin POSTs rejected; `/health` discloses nothing; requests are logged.
- [x] Secrets/deps scanned (gitleaks/trivy/pip-audit) clean; CI security workflow runs them.
- [x] Verified live in production (fail-closed auth + security headers).

## Impact Areas

- Backend: auth, sessions, client-IP, rate limiting, cost guard, logging, CSRF
- Frontend: login form (email+password); security headers already present
- Data model: none (CSV-only, no DB); `SECPHO_USERS` is env config
- API: all `/api/*` require a session; admin endpoints fail-closed
- AI/model behavior: PII redaction before LLM; prompt-injection rule
- Documentation: this packet; LGF launch-decision updated to post-fix
- Operations/security: Render env (`SECPHO_USERS`, `SECPHO_SESSION_SECRET`, `LLM_DAILY_BUDGET`)

## Open Questions

- Was the OpenAI key ever exposed in the old WeCollabify Render env (rotate-or-not)? — owner to confirm.
