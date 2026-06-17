# Launch Decision

## Summary

- Project: SECPHO Intelligence System
- Change: intelligence-upgrade (unmerged branch over commit `9d74ede`)
- Date: 2026-06-17
- Owner: Daniel / SECPHO (WeCollabify)
- Launch target: Render web service `secpho-intelligence-chat` (single-file stdlib `http.server` app `backend_api/mvp_web_app.py` + precomputed CSVs); TLS terminated by Render
- Decision: BLOCKED for broad/public launch; CONDITIONAL GO for a closed, password-gated SECPHO-staff demo, pending owner Gate 20 sign-off and the conditions below

Decision must remain BLOCKED while any Critical finding is open. Critical findings block launch until the finding is fixed and verified, the affected feature or asset is removed from launch scope, or the severity is downgraded by new evidence. No Critical findings are open; the broad-launch BLOCK is driven by three High/blocking findings (Gates 14, 17, 18).

An exceptional Critical override is not normal approval. If a project defines one, it must require explicit owner approval, documented rationale, compensating controls, and follow-up remediation.

## Related Gates

- Gate 20 — Launch Decision
- Gate 21 — Continuous Monitoring

## Gate Status

| Gate | Applies | Status | Evidence | Notes |
| --- | --- | --- | --- | --- |
| Gate 0 — Scope & Permission | true | PASS | Owner authorized this review; owned local repo; intended users = authenticated SECPHO staff | Human confirmation required; closed internal pilot, not public/multi-tenant SaaS |
| Gate 1 — Product, Asset & Data Inventory | true | PASS | Inventory produced this review (app + CSVs in `data/processed`, `recommendation_engine/outputs`; OpenAI + Render dependencies) | Data classes: member PII, socio/company data, 7968 subscriber emails, captured feedback, secrets |
| Gate 2 — Threat Modeling | true | PASS | Threat model produced; high-impact features identified (auth, PII, public deploy, LLM agent) | — |
| Gate 3 — Code Security | true | PASS WITH FOLLOW-UP | Manual review + per-feature adversarial verifier reviews this session | Semgrep NOT run (not installable on this Windows host); follow-up: run Semgrep in Linux CI |
| Gate 4 — Secrets & Config Hygiene | true | PASS | Secrets are env-only; `.gitignore` excludes `.env`/`.env.*`, `data/app_state`, `data/generated_artifacts`; `render.yaml` uses `sync:false`; manually verified no secret in committed files | Gitleaks not run (CI follow-up) |
| Gate 5 — Frontend Exposure | true | PASS WITH FOLLOW-UP | Security headers on every response (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, HSTS, CSP) set in `send_security_headers` (~L4539) | RESIDUAL: CSP allows `'unsafe-inline'` for `script-src`/`style-src` (UI inlines all JS/CSS) — defense-in-depth weakness. The scanner's 2 "blocking" Gate 5 findings are FALSE POSITIVES inside `secpho_env` (the venv), not our frontend |
| Gate 6 — API Auth & Object Authorization | true | PASS | All `/api/*` require an authenticated session; admin endpoints (`/api/tool-requests`, `/api/tool-build-events`, `/api/feedback-inbox`, `/admin`) are fail-closed and double-gated (`is_admin` requires `ADMIN_ENABLED`) | Object-level authz: any authed staff user can read any member/socio — ACCEPTED for a single internal trust group. The 27 scanner "no auth guard" findings are FALSE POSITIVES in `secpho_env` (pandas.api/joblib); the stdlib router is not recognized by the scanner |
| Gate 7 — Injection & Input Safety | true | PASS WITH FOLLOW-UP | No SQL/DB; ids parsed via `to_int` -> 400 (no 500/traceback); LLM/markdown output is `html.escape`'d BEFORE limited token substitution (`markdown_to_chat_html`); request bodies size-capped | RESIDUAL XSS surface: `'unsafe-inline'` CSP + regex markdown renderer (mitigated by escape-first) |
| Gate 8 — Auth, Sessions & CSRF | true | PASS WITH FOLLOW-UP | HMAC-SHA256 signed stateless cookies (HttpOnly, SameSite=Lax, Secure behind proxy), constant-time password compare, TTL; per-IP rate limits (login 8/5min, llm 30/min, api 120/min, feedback 10/5min) | GAP: no CSRF token on POST `/login`, `/api/feedback`, `/api/agent` (relies on SameSite=Lax only); follow-up: CSRF tokens before broad launch |
| Gate 9 — File Upload, SSRF, Imports & Exports | false | N/A | Deployed web app has NO file upload; fetches only a FIXED outbound URL (OpenAI), no user-controlled URL; static/artifact serving uses `Path(...).name` basename defense | Event-registration import is an OFFLINE pipeline, not in the web app. Low risk; documented false (not a high-risk skip) |
| Gate 10 — Dependency, SBOM & Supply Chain | true | PASS WITH FOLLOW-UP | `requirements.txt` fully pinned (pandas, numpy, scipy, scikit-learn, requests, etc.) | Trivy/pip-audit NOT run (not installable here); follow-up: dependency vuln scan in CI |
| Gate 11 — Infrastructure, DNS, TLS & Web Hardening | true | PASS WITH FOLLOW-UP | TLS terminated by Render; app binds plain HTTP behind Render's proxy; Secure cookie depends on `X-Forwarded-Proto`/`RENDER` env; HSTS header set | Follow-up: confirm Render forces HTTPS |
| Gate 12 — Resilience, DDoS, Abuse & Cost Defense | true | PASS WITH FOLLOW-UP | Per-IP in-memory rate limits (`RATE_LIMITS`, per-process; Render free = single instance, acceptable now) | AI COST exposure: agent makes multiple LLM calls per question — mitigated by the `llm` rate bucket; follow-up: shared/persistent rate limiter + OpenAI cost alerts at scale |
| Gate 13 — Webhooks, Background Jobs & Integrations | true | PASS WITH FOLLOW-UP | Only integration is OpenAI (outbound). Self-extending "tool-learning loop" auto-builds ONLY the whitelisted `create_socio_metric_chart` tool (SVG output), queuing riskier proposals for human review | Follow-up: keep the allowlist tight; `codex_review_notes` is a placeholder, not a real review |
| Gate 14 — Privacy, Legal & Data Lifecycle | true | FAIL (blocking for broad/external launch) | Member + subscriber PII processed and sent to OpenAI for phrasing, with NO privacy notice, retention policy, or data-subject-request path; EU/Spain GDPR | For a CLOSED internal staff pilot over SECPHO's own data: legitimate-interest internal use, lower exposure, acceptable WITH owner awareness. REQUIRED before broad use: documented privacy stance, retention, DSR path, and a data-processing note for the OpenAI sub-processor |
| Gate 15 — AI/RAG/Agent Security | true | PASS WITH FOLLOW-UP | Deterministic scores (LLM cannot invent/reorder); bulk people lists drop emails (`_agent_compact_person`) as a compensating control against prompt-injection exfiltration; agent loop bounded (`max_steps`) and exception-safe; falls back to a deterministic router | RESIDUAL: prompt injection from user messages or from DATA text (reto/profile free-text) not formally tested; follow-up: a prompt-injection test pass |
| Gate 16 — Multi-Tenant & Internal Permission Isolation | false | N/A | Single tenant (SECPHO only); the only boundary is user vs admin role (covered by Gates 6/8); no cross-tenant data | High-confidence documented false; not a tenant-isolation system (not a high-risk skip) |
| Gate 17 — Observability, Logs & Incident Readiness | true | FAIL (blocking) | `Handler.log_message` overridden to a no-op (~L4956) -> NO access logs; no error logging or monitoring/alerting | No visibility if the app breaks or is abused. REQUIRED before any real use: at least error + key-event logging; a named incident owner |
| Gate 18 — Backup, Recovery, Deletion & Rotation | true | FAIL (blocking) | `data/app_state` (feedback_inbox.md, tool-loop state, persisted `.session_secret`) lives on Render's EPHEMERAL disk -> wiped on every redeploy | Captured feedback (the point of the loop) is lost; sessions break unless `SECPHO_SESSION_SECRET` env is set. REQUIRED: set `SECPHO_SESSION_SECRET`; durable storage for feedback (or strict export-before-redeploy); secret rotation plan |
| Gate 19 — Business Logic Abuse | false | N/A | No payments/plans/credits/quotas/invites/entitlements; recommendation logic is deterministic; tool-build loop is allowlisted (covered by Gate 13) | Documented false (not a high-risk skip) |
| Gate 20 — Launch Decision | true | PASS WITH FOLLOW-UP | Recommendation recorded; final decision is the owner's (human confirmation required) | RECOMMENDATION: BLOCKED for broad/public launch (Gates 14/17/18 open); CONDITIONAL GO for a closed, password-gated SECPHO-staff demo under the conditions below. Final approval pending owner sign-off |
| Gate 21 — Continuous Monitoring | true | PASS WITH FOLLOW-UP | No monitoring yet (tied to Gate 17) | Follow-up: uptime + error + OpenAI-cost monitoring once live |

## Findings

| Severity | Count | Launch Impact |
| --- | --- | --- |
| Critical | 0 | Blocks launch if greater than 0 until fixed and verified, removed from launch scope, or downgraded by new evidence |
| High | 3 | Blocks launch unless explicitly accepted by a human owner — Gate 14 privacy/GDPR (broad launch), Gate 17 observability, Gate 18 ephemeral data loss |
| Medium | 6 | Track mitigation or follow-up — CSRF tokens (Gate 8), `'unsafe-inline'` CSP (Gates 5/7), prompt-injection test (Gate 15), dependency vuln scan (Gate 10), OpenAI cost monitoring (Gates 12/21), shared/persistent rate limiter (Gate 12) |
| Low | 0 | Track if useful |

Disclosed limitation: the Gitleaks / Semgrep / Trivy scanner stack is not installed on this Windows host and was not run here (run it in Linux CI). The `api_surface` / `frontend` scanner outputs that were produced were all false positives originating inside `secpho_env` (the venv: pandas.api/joblib, and venv-internal HTML), not in `backend_api/mvp_web_app.py`. Manual review and per-feature adversarial verifier reviews were performed in lieu of automated scanning.

## Skipped High-Risk Gates

| Gate | Reason | Confirmed By | Date |
| --- | --- | --- | --- |
| None | Gates 9, 16, and 19 are marked `applies=false` (documented N/A), not high-risk skips: no file upload/SSRF surface in the web app (9), single tenant with no cross-tenant data (16), no payments/quotas/entitlements (19) | LaunchGuardian (Claude) | 2026-06-17 |

## Accepted Risks

Pending owner decision at Gate 20. The following are proposed for explicit owner acceptance for the closed-pilot scope and are NOT yet accepted:

- Object-level authorization: any authenticated SECPHO staff user can read any member/socio record (single internal trust group).
- Gate 14 GDPR posture accepted only for closed internal use over SECPHO's own data, with owner awareness; not accepted for broad/external launch.
- Ephemeral feedback/session state on Render's disk, conditional on `SECPHO_SESSION_SECRET` being set and feedback exported before redeploy.

No risks are formally accepted until the owner signs off in Final Approval below.

## Rollback Or Disable Plan

The `intelligence-upgrade` branch is unmerged; the live Render service `secpho-intelligence-chat` currently runs the pre-session code.

- Primary rollback: do NOT merge `intelligence-upgrade`. The running service is unaffected by this work until a merge/deploy happens.
- If already deployed: revert the service to commit `9d74ede` (last known pre-session commit) and redeploy on Render.
- Hard disable: unset / clear the app env vars (`SECPHO_APP_PASSWORD`, `SECPHO_ADMIN_PASSWORD`, `OPENAI_API_KEY`, `SECPHO_SESSION_SECRET`) in the Render dashboard, or suspend the Render web service. With `ADMIN_ENABLED` unset, admin endpoints are already fail-closed.
- Containment: rate limits and password-gating remain in force; no data migration or schema change is involved (CSV-only, no DB), so rollback has no data-loss or migration risk beyond the already-ephemeral `data/app_state`.

## Final Approval

- Approved by:
- Approval date:
- Conditions:
  - (a) `SECPHO_APP_PASSWORD`, `SECPHO_ADMIN_PASSWORD`, and `SECPHO_SESSION_SECRET` set on Render.
  - (b) Owner accepts ephemeral feedback and exports it before each redeploy (or adds durable storage).
  - (c) Treated as a closed, password-gated SECPHO-staff pilot — not a public service.
  - (d) Basic error logging added (recommended).
  - Broad/public launch remains BLOCKED until Gates 14 (privacy/GDPR), 17 (observability), and 18 (durable storage + secret rotation) are resolved.
