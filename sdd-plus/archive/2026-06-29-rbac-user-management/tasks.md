# Tasks

## Change

rbac-user-management

## Implementation

- [x] **P4a — role + grant core (backend, hermetic).** `dev` role; `load_users` parses optional 4th
      grants field (legacy 3-field still valid); grant catalog + role-default sets; `grants_for`,
      `role_at_least`, `resolve_grants` (per-request from `USERS`); `is_admin`/`is_dev`/`has_grant`
      handler helpers; cookie + `parse_session_cookie` accept `dev`; `ADMIN_ENABLED` counts dev.
      Tests: `tests/test_rbac.py` (14, hermetic). Full suite 68 passing.
- [x] **P4b — fail-closed enforcement.** `TOOL_REQUIRED_GRANT` map + fail-closed check in
      `dispatch_tool` (data.* + tool.matchmaking); `/api/agent` requires `tool.chat` and threads the
      caller's grants into `ctx`; `/api/feedback-inbox` accepts admin OR `tool.feedback`; `/tuning`
      console gated by admin OR `tool.scoring` (Owner: inline `[tune]` widget + `/api/report-tuned`
      stay open to all chat users). Tests +6 (suite 74).
- [x] **P4c — `render_env.py`.** `write_enabled`, `read_users_env` (fresh read-before-write),
      `update_users_env` (single-var PUT + deploy trigger); flag-gated; single `_request` choke point.
      Tests: `tests/test_render_env.py` (8, network monkeypatched). Suite 82.
- [x] **P4d — Settings → Usuarios UI + `/api/org/users`.** DONE. Usuarios section in the existing
      `/admin` page (dark theme): user list with role pills + Editar/Contraseña/Eliminar, add-user
      form (email + role + checkbox grant matrix), one-time password shown once after create/reset.
      Backend helpers: `parse_users_string`/`serialize_users` (round-trip), `hash_password`,
      `gen_password`, `valid_secpho_email`, `org_user_guard` (forbidden/dev-protection/lockout),
      `apply_org_user_action`, `persist_users` (the single writer swap seam). Endpoints GET+POST
      `/api/org/users` (admin/dev-gated). Action-log line on each change (no secrets). JS via
      data-attrs + delegated listener, zero backslashes (esprima guard passes). Tests:
      `test_rbac.py` now 35 (incl. +15 for P4d) + 7 HTTP (`test_org_users_endpoint.py`). Suite 104.
      Forced password-change-on-first-login deferred to a fast-follow (Owner confirmed).
- [x] **P4e — close-out.** `sdd.py verify` (artifacts), verifier subagent (VERIFIED WITH NOTES,
      folded in), adversarial security review (6 dimensions → 3 findings FIXED, +6 tests, suite 110),
      LaunchGuardian local scan (gitleaks 0 / trivy 0; venv-noise + semgrep-wrapper failure + 3
      human-confirmation gates are Owner deploy-time items). Spec sync DONE (`access-control` living
      capability created; `agentic-conversation` cross-referenced). Archived + committed.

## Delta specs

- [x] `specs/access-control.md` — new capability spec with the RBAC + grant + enforcement scenarios;
      synced into `sdd-plus/specs/capabilities/access-control.md`.

## Verification

- [x] Verification run (`python scripts/sdd.py verify rbac-user-management`) + verifier subagent +
      adversarial security review. Result in `verification.md`: 110 tests green, 3 findings fixed.
