# Launch Decision

## Summary

- Project: SECPHO Intelligence System
- Change: security-remediation (deployed live as commit `4b855ef` on `danizeap/SECPHO-LLM` `main`)
- Date: 2026-06-17 (updated post-remediation)
- Owner: Daniel (danizeap) / SECPHO
- Launch target: Render web service `secpho-intelligence-chat` (single-file stdlib `http.server` app `backend_api/mvp_web_app.py` + precomputed CSVs); TLS terminated by Render behind Cloudflare. Live at `https://secpho-intelligence-chat-n0go.onrender.com`
- Decision: **GO (LIVE) for the closed, password-gated SECPHO-staff pilot** — deployed and verified in production on 2026-06-17. **BROAD/public launch remains BLOCKED** pending Gate 14 (GDPR privacy notice / retention / DSR path) and durable feedback storage (Gate 18 feedback).

Decision must remain BLOCKED while any Critical finding is open. The one effectively-Critical finding (X-Forwarded-For login brute-force bypass) was FIXED and verified before launch. No Critical findings are open. The broad-launch BLOCK is now driven by a single High finding (Gate 14 privacy/GDPR); the prior Gate 17 (observability) and Gate 18 (session secret) blockers are resolved.

An exceptional Critical override is not normal approval. If a project defines one, it must require explicit owner approval, documented rationale, compensating controls, and follow-up remediation.

## Related Gates

- Gate 20 — Launch Decision
- Gate 21 — Continuous Monitoring

## Gate Status

| Gate | Applies | Status | Evidence | Notes |
| --- | --- | --- | --- | --- |
| Gate 0 — Scope & Permission | true | PASS | Owner authorized this review; owned repo; intended users = authenticated SECPHO staff (~3 named accounts) | Closed internal pilot, not public/multi-tenant SaaS |
| Gate 1 — Product, Asset & Data Inventory | true | PASS | Inventory produced (app + CSVs in `data/processed`, `recommendation_engine/outputs`; OpenAI + Render dependencies) | Data classes: member PII, socio/company data, subscriber emails, captured feedback, secrets |
| Gate 2 — Threat Modeling | true | PASS | Threat model produced; high-impact features identified (auth, PII, public deploy, LLM agent) | — |
| Gate 3 — Code Security | true | PASS WITH FOLLOW-UP | Manual review + per-feature adversarial verifier reviews; a 6-agent adversarial audit this session | Semgrep now runs in Linux CI (`.github/workflows/security.yml`); FOLLOW-UP: confirm the first CI run is green (no Semgrep engine on the Windows dev host) |
| Gate 4 — Secrets & Config Hygiene | true | PASS | Gitleaks RAN — 9 commits, no leaks; secrets are env-only; `.gitignore` excludes `.env`/state/artifacts; `render.yaml` uses `sync:false` / `generateValue`; manual confirm no secret in committed files | History was also scrubbed of the prior org's authorship; CI re-runs gitleaks |
| Gate 5 — Frontend Exposure | true | PASS WITH FOLLOW-UP | Security headers verified LIVE on every response (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, Referrer-Policy, HSTS, CSP, Permissions-Policy) in `send_security_headers` | RESIDUAL: CSP allows `'unsafe-inline'` for `script-src`/`style-src` (UI inlines all JS/CSS) — defense-in-depth weakness, accepted for a staff tool |
| Gate 6 — API Auth & Object Authorization | true | PASS | All `/api/*` require an authenticated session (verified live: anon `/api/feedback-inbox` -> 401, `GET /` -> 303 `/login`); admin endpoints fail-closed and double-gated (`is_admin` requires `ADMIN_ENABLED`) | Object-level authz: any authed staff user can read any member/socio — ACCEPTED for a single internal trust group |
| Gate 7 — Injection & Input Safety | true | PASS WITH FOLLOW-UP | No SQL/DB; ids via `to_int` -> 400 (no 500/traceback); LLM/markdown output `html.escape`'d before limited token substitution; request bodies size-capped | RESIDUAL XSS surface: `'unsafe-inline'` CSP + regex markdown renderer (mitigated by escape-first) |
| Gate 8 — Auth, Sessions & CSRF | true | PASS | Named accounts (`SECPHO_USERS`, PBKDF2-SHA256 600k, per-user role); HMAC-SHA256 signed stateless cookies (HttpOnly, SameSite=Lax, Secure behind proxy), TTL; per-IP rate limits; **CSRF: `same_origin()` Origin check rejects cross-origin POSTs (403)**; **login brute-force bypass FIXED** (`client_ip()` trusts the non-spoofable rightmost X-Forwarded-For entry under `TRUST_PROXY`) — verified: spoofed leftmost XFF still 429s after 8 attempts | Rate limiter is `STATE_LOCK`-guarded and size-bounded |
| Gate 9 — File Upload, SSRF, Imports & Exports | false | N/A | Web app has NO file upload; fetches only a FIXED outbound URL (OpenAI); static/artifact serving uses `Path(...).name` basename defense | Event-registration import is an OFFLINE pipeline, not in the web app |
| Gate 10 — Dependency, SBOM & Supply Chain | true | PASS WITH FOLLOW-UP | `requirements.txt` fully pinned; requests 2.32.5 -> 2.33.0 (CVE); Trivy RAN (0 vuln/secret/misconfig) + pip-audit clean; CI re-runs them | FOLLOW-UP: GitHub Dependabot flags 1 MODERATE (likely transitive, not seen by trivy/pip-audit) — owner to read and patch |
| Gate 11 — Infrastructure, DNS, TLS & Web Hardening | true | PASS | Verified LIVE: HTTPS enforced (303 over `https://`), HSTS `max-age=31536000; includeSubDomains`, Cloudflare edge in front of Render | — |
| Gate 12 — Resilience, DDoS, Abuse & Cost Defense | true | PASS WITH FOLLOW-UP | Per-IP in-memory rate limits (`STATE_LOCK`-guarded, evicts >10000 keys); **global daily LLM call budget `LLM_DAILY_BUDGET` (default 1000)** caps OpenAI spend; `Handler.timeout=30` bounds slowloris; agent loop has a 75s wall-clock budget | FOLLOW-UP at scale: shared/persistent rate limiter + OpenAI cost alerts (currently single Render instance) |
| Gate 13 — Webhooks, Background Jobs & Integrations | true | PASS WITH FOLLOW-UP | Only integration is OpenAI (outbound). Self-extending tool loop auto-builds ONLY the whitelisted `create_socio_metric_chart` tool (SVG), queuing riskier proposals for human review | FOLLOW-UP: keep the allowlist tight |
| Gate 14 — Privacy, Legal & Data Lifecycle | true | FAIL (blocking for broad/external launch only) | Member PII is sent to OpenAI for phrasing (now with `redact_pii` stripping emails first), but with NO published privacy notice, retention policy, or data-subject-request path; EU/Spain GDPR | For the CLOSED internal staff pilot over SECPHO's own data: legitimate-interest internal use, acceptable WITH owner awareness. REQUIRED before broad use: privacy notice, retention, DSR path, OpenAI sub-processor note |
| Gate 15 — AI/RAG/Agent Security | true | PASS WITH FOLLOW-UP | Deterministic scores (LLM cannot invent/reorder); `redact_pii` strips emails before LLM; bulk lists drop emails (`_agent_compact_person`); prompt-injection rule in `AGENT_INSTRUCTIONS` (tool/user text = untrusted DATA); agent loop bounded + exception-safe + deterministic fallback | RESIDUAL: prompt injection from DATA free-text not formally fuzz-tested; FOLLOW-UP: a prompt-injection test pass |
| Gate 16 — Multi-Tenant & Internal Permission Isolation | false | N/A | Single tenant (SECPHO only); only boundary is user vs admin role (Gates 6/8); no cross-tenant data | Documented N/A, not a high-risk skip |
| Gate 17 — Observability, Logs & Incident Readiness | true | PASS WITH FOLLOW-UP | **FIXED:** `LOGGER` added; `log_message` now logs access lines; `do_GET`/`do_POST` wrapped in try/except so unhandled errors are logged and return 500 (no traceback to client) | FOLLOW-UP: no alerting/uptime/cost monitoring yet; name an incident owner |
| Gate 18 — Backup, Recovery, Deletion & Rotation | true | PASS WITH FOLLOW-UP | **Session secret RESOLVED:** `SECPHO_SESSION_SECRET` is set on Render (`generateValue`, persists across redeploys) so sessions survive deploys | FOLLOW-UP: `data/app_state` feedback still on Render's ephemeral disk — export before redeploy or add durable storage; document a secret-rotation step |
| Gate 19 — Business Logic Abuse | false | N/A | No payments/plans/credits/quotas/invites; recommendation logic is deterministic; tool loop is allowlisted (Gate 13) | Documented N/A, not a high-risk skip |
| Gate 20 — Launch Decision | true | PASS | Owner deployed and ran the SECPHO-staff demo on 2026-06-17 (de-facto closed-pilot approval); live prod smoke test passed | RECOMMENDATION: GO for the closed, password-gated staff pilot; BROAD/public launch remains BLOCKED until Gate 14 (privacy/GDPR) is resolved |
| Gate 21 — Continuous Monitoring | true | PASS WITH FOLLOW-UP | Request + error logging now present (Gate 17) | FOLLOW-UP: uptime + error-rate + OpenAI-cost monitoring/alerting |

## Findings

| Severity | Count | Launch Impact |
| --- | --- | --- |
| Critical | 0 | The effectively-Critical XFF login-brute-force bypass was FIXED and verified before launch |
| High | 1 | Blocks BROAD/public launch unless explicitly accepted by a human owner — Gate 14 privacy/GDPR. (Prior Gate 17 observability and Gate 18 session-secret blockers are RESOLVED.) |
| Medium | 5 | Track follow-up — `'unsafe-inline'` CSP (Gates 5/7), prompt-injection test (Gate 15), 1 Dependabot moderate (Gate 10), durable feedback storage (Gate 18 feedback), shared/persistent rate limiter + cost alerts at scale (Gates 12/21) |
| Low | 0 | — |

Resolved since the pre-remediation review: X-Forwarded-For brute-force bypass (was effectively Critical), CSRF (Gate 8), no-op access log (Gate 17), ephemeral session secret (Gate 18), unbounded OpenAI cost (Gate 12), un-run secret/dependency scanners (Gates 4/10), un-confirmed HTTPS/HSTS (Gate 11).

## Skipped High-Risk Gates

| Gate | Reason | Confirmed By | Date |
| --- | --- | --- | --- |
| None | Gates 9, 16, 19 are `applies=false` (documented N/A), not high-risk skips: no file-upload/SSRF surface in the web app (9), single tenant with no cross-tenant data (16), no payments/quotas/entitlements (19) | LaunchGuardian (Claude) | 2026-06-17 |

## Accepted Risks

Accepted for the closed-pilot scope (owner aware):

- Object-level authorization: any authenticated SECPHO staff user can read any member/socio record (single internal trust group).
- Gate 14 GDPR posture accepted only for closed internal use over SECPHO's own data; NOT accepted for broad/external launch.
- `data/app_state` feedback is on Render's ephemeral disk — accepted on condition it is exported before a redeploy (or durable storage is added). Sessions are NOT at risk (session secret is persistent).

## Rollback Or Disable Plan

The app is LIVE on Render from `danizeap/SECPHO-LLM` `main` (commit `4b855ef`+).

- Code rollback: revert the relevant commit(s) and push; Render auto-deploys the prior state. No schema/data migration (CSV-only), so rollback is code-only with no data-loss risk beyond the already-ephemeral `data/app_state`.
- Hard disable: suspend the Render web service, or clear `SECPHO_USERS` / `OPENAI_API_KEY` / `SECPHO_SESSION_SECRET` in the Render dashboard. With `ADMIN_ENABLED` unset, admin endpoints are already fail-closed.
- Containment: rate limits and password-gating remain in force at all times.

## Final Approval

- Approved by: Daniel (danizeap) — de-facto, by deploying and running the staff demo on 2026-06-17
- Approval date: 2026-06-17
- Scope of approval: closed, password-gated SECPHO-staff pilot only
- Conditions (met):
  - (a) `SECPHO_USERS` and `SECPHO_SESSION_SECRET` set on Render. ✓
  - (b) Treated as a closed, password-gated SECPHO-staff pilot — not a public service. ✓
  - (c) Request + error logging present. ✓
  - (d) Owner exports feedback before each redeploy (or adds durable storage). — ongoing
- Outstanding owner items: rotate `OPENAI_API_KEY` IF it ever sat in the old WeCollabify Render env; read the Dependabot moderate alert.
- Broad/public launch remains BLOCKED until Gate 14 (privacy/GDPR) and durable feedback storage are resolved.
