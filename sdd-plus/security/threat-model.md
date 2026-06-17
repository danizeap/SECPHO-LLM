# Threat Model

LaunchGuardian Framework (LGF) launch record for the SECPHO Intelligence System security review.

## Context

- Project: SECPHO Intelligence System
- Change: intelligence-upgrade (chat app + admin feedback/tool-learning loop; unmerged tonight on branch `intelligence-upgrade`)
- Date: 2026-06-17
- Owner: Daniel / SECPHO (WeCollabify)
- Scope: Closed, password-gated internal pilot for SECPHO staff over SECPHO's own member data. Single tenant, not a public/multi-tenant SaaS. Deploy target: Render web service `secpho-intelligence-chat`. Reviewer: LaunchGuardian (Claude).

## Related Gates

- Gate 2 — Threat Modeling
- Gate 3 — Code Security
- Gate 7 — Injection & Input Safety
- Gate 12 — Resilience, DDoS, Abuse & Cost Defense
- Gate 19 — Business Logic Abuse

## System Summary

Single-file Python stdlib `http.server` application (`backend_api/mvp_web_app.py`) backed by precomputed CSVs (no database). At startup it loads normalized member, company (socio), and subscriber data from `data/processed` and `recommendation_engine/outputs` into memory. It serves a single-page chat UI and a `/admin` console behind a signed-cookie session.

- **Deployable artifact:** the `mvp_web_app.py` process, started via `python backend_api/mvp_web_app.py` (per `render.yaml`), binding plain HTTP behind Render's TLS-terminating proxy.
- **Users:** authenticated SECPHO staff (single trust group). Two roles only: standard authenticated user, and admin (holder of `SECPHO_ADMIN_PASSWORD`, who additionally sees the feedback inbox and tool-learning loop). The public and unauthenticated users are excluded.
- **Environments:** Render web service `secpho-intelligence-chat` (free plan, single instance). Secrets supplied as env vars (`sync: false` in `render.yaml`, set in the dashboard).
- **Major components:** stdlib HTTP request handler / router (`do_GET`/`do_POST`); HMAC-signed stateless session cookies; deterministic recommendation/scoring engine over in-memory CSVs; a bounded LLM agent loop (`run_agent`, `max_steps=6`) that grounds answers in deterministic data and uses OpenAI only for phrasing; a markdown→HTML renderer (`markdown_to_chat_html`) that escapes first; an admin feedback inbox and an allowlisted self-extending "tool-learning" loop.
- **External dependencies:** OpenAI Responses API (outbound only, fixed URL `https://api.openai.com/v1/responses`); Render hosting (TLS termination). The SECPHO WordPress REST endpoints are used only by the OFFLINE data pipeline, not by the deployed web app.

## Trust Boundaries

| Boundary | What Crosses It | Controls | Open Questions |
| --- | --- | --- | --- |
| Browser → app | Login password, chat questions, feedback notes, session cookie, over HTTPS (Render TLS) | TLS at proxy; HMAC-SHA256 signed `HttpOnly; SameSite=Lax` cookie (`Secure` when `X-Forwarded-Proto: https` or `RENDER` set); per-IP rate limits; security headers (X-Frame-Options DENY, nosniff, Referrer-Policy, HSTS, CSP) | No CSRF token on POST `/login`, `/api/feedback`, `/api/agent` (relies on SameSite=Lax only). Confirm Render forces HTTPS so `Secure` always applies. |
| App → OpenAI | User question + grounded data snippets (including member names/profiles) for phrasing; `OPENAI_API_KEY` in Authorization header | Fixed outbound URL (no user-controlled URL/SSRF); HTTPS; bulk people lists drop emails before grounding | PII leaves the EU/Spain to a sub-processor with no data-processing note or privacy notice (see Gate 14 residual). |
| User input → LLM agent | Free-text chat messages, and free-text DATA fields (reto/profile text) that get grounded into prompts | Deterministic scoring (LLM cannot invent/reorder results); bounded agent loop (`max_steps=6`), exception-safe with deterministic-router fallback; email-drop on bulk lists; escape-first output rendering | Prompt injection from user messages or from data free-text not formally tested (Gate 15 follow-up). |
| Authenticated user → member/subscriber PII | Read access to any member/socio profile; single contact email surfaced on request; bulk lists | All `/api/*` require an authenticated session; bulk people lists DROP email (`_agent_compact_person`) as a privacy control; object-level read of any member ACCEPTED for the single internal trust group | No per-object authorization (any authed staff reads any member) — accepted only because there is one trust group, no orgs/teams. |
| User → admin functions | Admin login; access to `/admin`, `/api/tool-requests`, `/api/tool-build-events`, `/api/feedback-inbox` | Fail-closed, double-gated: `is_admin()` requires `ADMIN_ENABLED` (set only when `SECPHO_ADMIN_PASSWORD` present) AND session role `admin`; constant-time password compare | Admin is open-by-default ONLY if the admin password is unset — mitigated because `ADMIN_ENABLED` is false without the env var, so admin endpoints fail closed. |

## Assets

| Asset | Why It Matters | Sensitivity | Owner |
| --- | --- | --- | --- |
| Member personal data (names, emails, role/title, company, location, technologies/sectors, optional hobbies/languages/university) | Core GDPR-regulated PII; exposure or exfiltration is a privacy/legal incident | Personal (GDPR, EU/Spain) | SECPHO |
| Socio/company data (company name, type, province, readiness, main_contact_email) | Business + contact data tied to members; misuse harms member relationships | Business/contact | SECPHO |
| Subscriber data (7,968 newsletter contacts/emails in `suscriptores_normalized.csv`) | Largest PII set; bulk-email exposure is the highest-volume privacy risk | Personal (GDPR) | SECPHO |
| OpenAI API key (`OPENAI_API_KEY`) | Theft enables third-party spend and abuse on SECPHO's account | Secret | SECPHO / Daniel |
| Session secret (`SECPHO_SESSION_SECRET`) | Signs session cookies; loss/forgery breaks auth or lets attackers mint valid sessions | Secret | SECPHO / Daniel |
| Captured feedback (`data/app_state/feedback_inbox.md`: notes + member id + truncated user-agent) | The point of the learning loop; contains references to members; lives on ephemeral disk | Personal/business | SECPHO |
| Other secrets (`SECPHO_API_AUTH_TOKEN`, `SECPHO_APP_PASSWORD`, `SECPHO_ADMIN_PASSWORD`) | Gate access to the app, admin console, and the offline WordPress pipeline | Secret | SECPHO / Daniel |

## Threats And Mitigations

| Threat | Impact | Likelihood | Severity | Mitigation | Evidence | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Open-admin-by-default (admin endpoints reachable without admin auth) | Unauthorized read of feedback inbox + tool-learning loop | Low | High | Fail-closed: `is_admin()` requires `ADMIN_ENABLED` (true only when `SECPHO_ADMIN_PASSWORD` is set) AND session role `admin`; admin routes redirect to `/login` otherwise | `mvp_web_app.py:75` (`ADMIN_ENABLED = bool(ADMIN_PASSWORD)`), `:4528-4530` (`is_admin`), `:4657-4669` (`/admin` gate) | Daniel | Mitigated |
| Session-secret loss (cookie secret wiped on redeploy) | Sessions break for all users; persisted secret on ephemeral disk is lost; risk of weak/rotating secret | Medium | High | Sign cookies with `SECPHO_SESSION_SECRET` env var (HMAC-SHA256) instead of the ephemeral persisted `.session_secret` | `mvp_web_app.py:245` (`sign_value`), `:274` (`compare_digest` verify); Gate 18 | Daniel | Open (REQUIRED: set `SECPHO_SESSION_SECRET` on Render) |
| XSS via `'unsafe-inline'` CSP + regex markdown renderer | Script injection into the chat UI | Low | High | Escape-first rendering: LLM/markdown output is `html.escape`'d BEFORE limited token substitution in `markdown_to_chat_html`; full security-header set incl. CSP | `mvp_web_app.py:2972` (`markdown_to_chat_html`), `:4538-4554` (headers/CSP); Gate 5/7 | Daniel | Mitigated (residual: CSP allows `'unsafe-inline'` — defense-in-depth weakness) |
| CSRF on state-changing POSTs | Forced login, feedback injection, or agent calls from a malicious origin | Low | Medium | `SameSite=Lax` cookie limits cross-site POSTs | `mvp_web_app.py:4536` (`SameSite=Lax`); POST routes `:4844` `/login`, `:4876` `/api/feedback`, `:4905` `/api/agent` | Daniel | Open (follow-up: add CSRF tokens before broad launch) |
| Prompt injection (from user messages or from data free-text) | LLM coerced to leak PII or misbehave | Medium | High | Deterministic scoring (LLM cannot invent/reorder results); bulk people lists drop emails (`_agent_compact_person`); bounded agent loop with deterministic-router fallback | `mvp_web_app.py:2741` (`_agent_compact_person`), `:2918-2943` (`run_agent`, `max_steps`); Gate 15 | Daniel | Mitigated by email-drop + grounding (residual: not formally injection-tested) |
| PII sent to OpenAI sub-processor | Member/subscriber personal data leaves EU/Spain to a third party | High (by design) | High | Bulk lists drop emails before grounding; outbound to a single fixed URL; minimal snippets for phrasing only | `OPENAI_RESPONSES_URL` `mvp_web_app.py:47`; `_agent_compact_person`; Gate 14 | Daniel | Residual (REQUIRED before broad use: privacy notice, retention, DSR path, OpenAI sub-processor data-processing note) |
| Ephemeral-data-loss (feedback + state on Render's ephemeral disk) | Captured feedback — the point of the loop — wiped on every redeploy; sessions break | High | High | None in code; relies on export-before-redeploy / setting `SECPHO_SESSION_SECRET` | `data/app_state/feedback_inbox.md` (gitignored, ephemeral); Gate 18 | Daniel | Open (REQUIRED: durable storage or strict export-before-redeploy; secret rotation plan) |
| Cost abuse (multiple LLM calls per question) | Runaway OpenAI spend on SECPHO's account | Medium | Medium | Per-IP in-memory rate limits, incl. an `llm` bucket (30/min); login 8/5min, api 120/min, feedback 10/5min | `mvp_web_app.py:80` (`RATE_LIMITS`), `:302` (`_check_rate`); Gate 12 | Daniel | Rate-limited (follow-up: shared/persistent limiter + OpenAI cost alerts at scale) |
| No observability (no access/error logs, no monitoring) | No visibility if the app breaks or is abused; no incident detection | High | High | None — `log_message` is overridden to a no-op | `mvp_web_app.py:4956` (`log_message` no-op); Gate 17/21 | Daniel | Open (REQUIRED before real use: error + key-event logging; an incident owner) |

## Abuse Cases

- An authenticated staff user enumerates members through chat/search to extract a bulk contact list — bulk people lists drop emails (`_agent_compact_person`); single-contact email is surfaced only on explicit request.
- A user crafts a prompt-injection message (or seeds malicious text into a reto/profile field consumed by the agent) to coerce the LLM into leaking emails or fabricating results — countered by deterministic scoring and the email-drop control; not yet formally injection-tested.
- An attacker who steals or guesses the OpenAI key, or who floods `/api/agent`, drives up OpenAI spend — countered by the per-IP `llm` rate bucket; no cost alerting yet.
- A malicious site auto-submits a cross-origin POST to `/api/feedback` or `/api/agent` on behalf of a logged-in staff user — partially countered by `SameSite=Lax`; no CSRF token.
- The admin password is left unset, exposing the admin console — countered by fail-closed `ADMIN_ENABLED` gating (admin endpoints stay closed without the password).
- A redeploy silently discards captured feedback and the tool-loop state on Render's ephemeral disk — operational abuse/data-loss risk with no current technical guard.
- An attacker submits malformed ids or oversized request bodies to trigger crashes/tracebacks — countered by `to_int` (400, no 500/traceback) and request body size caps.

## Critical Findings

Critical findings block launch until fixed and verified, removed from launch scope, or downgraded by new evidence.

An exceptional Critical override is not normal approval. If a project defines one, it must require explicit owner approval, documented rationale, compensating controls, and follow-up remediation.

| Finding | Evidence | Required Fix | Owner | Status |
| --- | --- | --- | --- | --- |
| None recorded |  |  |  |  |

No Critical findings. Three High/blocking findings (Gate 14 privacy for broad/external launch, Gate 17 observability, Gate 18 ephemeral data loss) govern the launch decision and are tracked in the threats table and residual risk below.

## Residual Risk

Overall result: **FAIL for broad/public launch**; **CONDITIONAL GO** for a closed, password-gated SECPHO-staff demo pending the owner's Gate 20 sign-off. Critical findings: 0. High/blocking: 3 (Gate 14 privacy for broad launch, Gate 17 observability, Gate 18 ephemeral data loss). Medium/follow-up: ~6 (CSRF tokens, `'unsafe-inline'` CSP hardening, prompt-injection test pass, dependency vuln scan, OpenAI cost monitoring, shared/persistent rate limiter).

Risks remaining after mitigations:

- **PII to OpenAI (Gate 14):** member/subscriber personal data is sent to OpenAI for phrasing with no privacy notice, retention policy, or data-subject-request path. Accepted only as legitimate-interest internal use over SECPHO's own data for a closed pilot, with owner awareness. Broad use requires a documented privacy stance, retention, DSR path, and an OpenAI sub-processor data-processing note. → `accepted-risks`.
- **No observability (Gate 17):** no access/error logs or monitoring; the app is blind to breakage and abuse. Blocking for any real use until at least error + key-event logging and a named incident owner exist.
- **Ephemeral data loss (Gate 18):** feedback, tool-loop state, and the persisted session secret live on Render's ephemeral disk and are wiped on redeploy. Requires `SECPHO_SESSION_SECRET` env var set, durable feedback storage (or strict export-before-redeploy), and a secret-rotation plan.
- **CSRF (Gate 8):** state-changing POSTs rely on `SameSite=Lax` only; add CSRF tokens before broad launch. → `accepted-risks` for the closed pilot.
- **`'unsafe-inline'` CSP (Gate 5):** the UI inlines all JS/CSS, weakening the CSP as defense-in-depth; XSS is mitigated escape-first but not eliminated.
- **Prompt-injection not formally tested (Gate 15):** grounding + email-drop are compensating controls; a dedicated injection test pass is a follow-up.
- **Object-level authorization:** any authenticated staff user can read any member/socio. Accepted for the single internal trust group; would need per-object authz before multi-org use.
- **Single-instance, in-memory rate limits (Gate 12):** acceptable on Render's single free instance; needs a shared/persistent limiter and cost alerts at scale.
- **Tooling gap (disclosed):** Semgrep / Gitleaks / Trivy / pip-audit were not run on this Windows host — to be run in Linux CI. `requirements.txt` is fully pinned. Scanner "blocking" Gate 5/6 findings were verified as venv (`secpho_env`) false positives, not the app's frontend or routes.

Conditional-GO requirements for the closed staff demo: (a) `SECPHO_APP_PASSWORD` + `SECPHO_ADMIN_PASSWORD` + `SECPHO_SESSION_SECRET` set on Render; (b) owner accepts ephemeral feedback and exports before redeploy (or adds durable storage); (c) treated as a closed pilot, not a public service; (d) basic error logging added (recommended). Final approval pending owner Gate 20 sign-off.
