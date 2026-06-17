# Verification

## Change

security-remediation

## Automated Checks

- [x] gitleaks: 9 commits scanned, no leaks.
- [x] trivy: `requirements.txt` — 0 vulnerabilities / 0 secrets / 0 misconfig.
- [x] pip-audit: clean after requests 2.33.0.
- [x] `python -c "ast.parse(...)"` on `mvp_web_app.py`: parses.
- [x] CI security workflow added (`.github/workflows/security.yml`) so Linux-only
      scanners (Semgrep) run on every push.

## Manual Checks

- [x] Brute-force bypass closed: rotating the leftmost XFF with a constant rightmost
      entry (`9.9.9.9`) -> HTTP 429 after 8 login attempts (the limiter keys on the
      non-spoofable rightmost entry).
- [x] Auth roles: admin -> `/api/feedback-inbox` 200; user -> 403; anonymous -> 401.
- [x] Live prod smoke test (`https://secpho-intelligence-chat-n0go.onrender.com`):
  - `/health` -> 200 `{"status":"ok"}` (no disclosure)
  - `GET /` unauthenticated -> 303 redirect to `/login` (fail-closed)
  - `GET /api/feedback-inbox` unauthenticated -> 401
  - headers present: HSTS, `X-Frame-Options: DENY`, CSP, `nosniff`, Referrer-Policy,
    Permissions-Policy; Cloudflare edge in front of Render.

## Documentation Updates

- [x] LGF `launch-decision.md` updated to the post-fix state.
- [x] Deploy/env documented in `render.yaml` + this packet (no README change needed).
- [ ] No documentation update needed. Reason: covered above.

## Result

PASS for the closed, password-gated SECPHO-staff pilot (now LIVE and verified in
production). Broad/public launch remains gated on Gate 14 (GDPR privacy notice /
retention / DSR path) and durable feedback storage (Gate 18 feedback) — tracked as
follow-ups, not part of this change.
