# Verification

## Change

rbac-user-management

## Automated Checks

- [x] Full test suite green: `python -m pytest -q` → **110 passed** (includes +6 regression tests
      for the security-review fixes). New coverage: `test_rbac.py` (37), `test_org_users_endpoint.py`
      (9, real HTTP handler), `test_render_env.py` (11, network monkeypatched).
- [x] HTTP-level enforcement proven: non-admins get 403 on GET+POST `/api/org/users`; admin lists +
      creates; `@secpho.org` validation; admin cannot assign `dev`; last admin cannot be deleted.
- [x] Inline-JS esprima guard passes over the new `ADMIN_HTML` Usuarios UI (no escaping trap).
- [x] `python scripts/sdd.py verify rbac-user-management` → artifacts verified.
- [x] Secret sweep: `git grep` finds no `RENDER_API_KEY=` literal and no WP token in any tracked
      file; LaunchGuardian gitleaks gate = 0 findings; trivy = 0.

## Manual Checks

- [x] **Verifier subagent (independent):** VERIFIED WITH NOTES. Confirmed against the code:
      fail-closed `dispatch_tool` gating on the production path, all 14 agent tools mapped to a
      grant, admin-cannot-assign/touch-dev, last-admin lockout, OTPs pbkdf2-hashed and never logged,
      GET listing omits password hashes, and no secrets in the tree. Notes folded in: tasks.md
      test-count wording corrected; the "/api/agent always supplies grants" invariant recorded in
      `specs/access-control.md`.
- [x] **Adversarial security review (workflow):** 6 attack dimensions (privilege-escalation,
      fail-open gaps, secret handling, injection/XSS, authz/lockout bypass, session/CSRF), each
      finding adversarially re-verified (1 candidate correctly refuted). **3 real findings found and
      FIXED before archive** (see decision log): HIGH fail-open roster read → catastrophic clobber
      (now fail-closed parse + refuse-empty-read guard); MEDIUM heuristic fallback bypassed grants +
      PII redaction (now gated on `data.socios` + `redact_pii`); MEDIUM stale cookie role (now role
      re-derived from the live roster). +6 regression tests; suite **110 passing**.
- [~] **LaunchGuardian local scan:** gitleaks 0, trivy 0. The remaining BLOCKED status is NOT a code
      vulnerability: (a) the api_surface/frontend_exposure findings are all inside the `secpho_env`
      virtualenv (third-party, not shipped) and should be excluded from scope; (b) the semgrep gate
      reported a wrapper failure though semgrep 1.166 runs locally; (c) 3 `launch_policy` gates
      (9 SSRF/upload, 16 permission-isolation, 19 business-logic) need the Owner's human confirmation
      in `sdd-plus/security/gate-applicability.yml`. These are deploy-time release gates, tracked for
      the Owner — not implementation defects.

## Documentation Updates

- [x] New capability spec `specs/access-control.md` (delta) with requirement-level scenarios.
- [x] Decision log records the storage choice, role model, grant model, per-request resolution,
      one-time-password handling, tuner-access decision, and the WordPress production end-state.
- [ ] No README/PROJECT_CONTEXT change required for this change beyond the spec.

## Result

PASS (implementation) — VERIFIED WITH NOTES by the verifier subagent; 104 tests green; no secrets in
the tree. Going-LIVE prerequisites (Owner, deploy-time): set `RENDER_API_KEY` + `RENDER_SERVICE_ID`
on Render, and confirm the 3 LaunchGuardian high-risk gates in `gate-applicability.yml`. These gate
deployment, not the drydock archive.
