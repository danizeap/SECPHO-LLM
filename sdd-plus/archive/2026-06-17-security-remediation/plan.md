# Plan

## Change

security-remediation

## Approach

Single-file stdlib app (`backend_api/mvp_web_app.py`), no framework, no DB.
Hardening applied in place, env-driven, fail-closed:

1. Named accounts: `SECPHO_USERS` env (`email|role|pbkdf2_sha256$...`) parsed into
   `USERS`; `hash_password`/`verify_password` (PBKDF2-SHA256, 600k iters);
   `check_credentials` -> `(role, email)`; shared-password path kept only as fallback.
2. Trustworthy client IP: `client_ip()` trusts the RIGHTMOST X-Forwarded-For entry
   only when `TRUST_PROXY` (RENDER env) is set; otherwise the socket peer. The
   rightmost entry is appended by Render's proxy and cannot be spoofed by the client.
3. Cost guard: `llm_budget_ok()` enforces `LLM_DAILY_BUDGET` (default 1000) across
   `call_llm` and `call_agent_step`.
4. Slowloris: `Handler.timeout = 30` on the inbound socket.
5. Rate limiter: `is_rate_limited` wrapped in `STATE_LOCK`, evicts when >10000 keys.
6. CSRF: `same_origin()` Origin check rejects cross-origin POSTs (403); cookies SameSite=Lax.
7. Disclosure: `/health` returns only `{"status":"ok"}`.
8. Observability: `LOGGER`; `log_message` logs; `do_GET`/`do_POST` wrapped -> 500s logged.
9. AI safety: `redact_pii` strips emails before LLM; prompt-injection rule in `AGENT_INSTRUCTIONS`.
10. Fail-closed: `main()` exits if `TRUST_PROXY and not SESSION_SECRET_FROM_ENV`.
11. Supply chain: requests 2.32.5 -> 2.33.0 (CVE); `.github/workflows/security.yml` (pip-audit, semgrep, gitleaks, trivy).
12. Deploy: `render.yaml` declares `SECPHO_USERS`/`OPENAI_API_KEY` (sync:false),
    `SECPHO_SESSION_SECRET` (generateValue), `LLM_DAILY_BUDGET`.

## Files Expected To Change

- `backend_api/mvp_web_app.py` (auth, client_ip, budget, locks, /health, logging, CSRF, redaction, fail-closed)
- `render.yaml` (named-account blueprint)
- `requirements.txt` (requests 2.33.0)
- `.github/workflows/security.yml` (new)
- `scripts/make_user.py` (new — generate `SECPHO_USERS` entries)
- `sdd-plus/security/*` (LGF records), `sdd-plus/security/launch-decision.md` (post-fix)

## Risks

- Rightmost-XFF trust depends on Render appending the real client IP (true for
  single-proxy Render). A different proxy topology could over- or under-count, but
  it never UNDER-protects login (the rightmost entry is non-spoofable by the client).
- 600k PBKDF2 iterations add ~0.1s per login — acceptable for ~3 users.
- Cost budget and rate limiter are per-process (single Render instance) — fine now;
  need a shared store if scaled to multiple instances.

## Rollback

Per-control and env-driven. Revert commit `e3035c5` (+ `4b855ef` blueprint), or unset
the relevant env var. No schema/data migration (CSV-only), so rollback is code-only.
Hard disable: suspend the Render service. Do NOT unset `SECPHO_USERS` without a
replacement in prod (auth would fall back to shared-password or, with none set, disabled).
