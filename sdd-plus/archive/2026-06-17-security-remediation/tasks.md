# Tasks

## Change

security-remediation

## Implementation

- [x] Named-account auth (`SECPHO_USERS`, PBKDF2-SHA256 600k, roles, fail-closed admin).
- [x] Fix X-Forwarded-For brute-force bypass (rightmost entry + `TRUST_PROXY` gate).
- [x] Global LLM daily cost budget; slowloris socket timeout; rate-limiter lock + eviction.
- [x] CSRF same-origin check on POSTs; minimal `/health`; access + error logging.
- [x] PII redaction before LLM; prompt-injection rule in agent instructions.
- [x] Dependency CVE bump (requests 2.33.0); CI security workflow; `make_user.py` helper.
- [x] Named-account Render blueprint (generateValue session secret).
- [x] Run secret/dep scanners (gitleaks, trivy, pip-audit) — all clean.
- [x] Verify live in production (fail-closed auth + security headers).
- [x] Update LGF launch-decision to post-fix state.
