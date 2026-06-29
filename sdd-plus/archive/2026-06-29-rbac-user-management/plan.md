# Plan

## Change

rbac-user-management

## Approach

Phased, each phase hermetic and independently testable (full rationale in [blueprint.md](blueprint.md)
§13):

- **P4a — role + grant core.** Add `dev`; extend `load_users` to parse the optional 4th grants
  field (legacy 3-field lines still parse with role-default grants); define the grant catalog +
  role-default sets; add `has_role`/`has_grant`/`is_dev`; resolve grants per-request from `USERS`
  keyed by the cookie email; let `parse_session_cookie` accept `dev`.
- **P4b — fail-closed enforcement.** Map each agent tool to a required grant in `dispatch_tool`/
  `ctx`; gate the financial/PII loaders + endpoints; gate scoring/feedback/org surfaces to admin/dev.
- **P4c — `render_env.py`.** Read/rewrite/PATCH `SECPHO_USERS` via the Render API + deploy trigger;
  flag-gated on `RENDER_API_KEY`/`RENDER_SERVICE_ID`; fully mockable; no network in tests.
- **P4d — Settings → Usuarios UI + `/api/org/users`.** list/create/update/delete, one-time password
  generation, `@secpho.org` validation, lockout guards, checkbox matrix; data-attr + delegated JS.
- **P4e — close-out.** verify → verifier subagent → LaunchGuardian strict scan → sync → archive.

## Files Expected To Change

- `backend_api/mvp_web_app.py` — auth extension, enforcement, `/api/org/users`, Settings UI.
- `backend_api/render_env.py` — NEW; the only Render API caller.
- `tests/test_rbac.py` (+ enforcement/UI tests) — NEW hermetic coverage.
- `sdd-plus/specs/capabilities/access-control.md` — NEW capability (synced at close-out).
- `sdd-plus/changes/rbac-user-management/specs/access-control.md` — delta spec for this change.
- Security/ops note (PROJECT_CONTEXT or a security standard) for the new secrets.

## Risks

- `RENDER_API_KEY` is privileged → env-only, never in repo/logs/client/LLM; used only by the
  admin/dev-gated write path; LaunchGuardian secrets gate must pass.
- Privilege escalation → all checks server-side on signed sessions; client never trusted.
- Redeploy lag/blip on each user change → documented; UI states "activo en ~1–2 min".
- Concurrent edits → `STATE_LOCK` + fresh read-before-write from Render.

## Rollback

Disable by unsetting `RENDER_API_KEY`/`RENDER_SERVICE_ID` (write path goes read-only) and/or
reverting the role to the binary `{user, admin}` parse — legacy 3-field `SECPHO_USERS` lines remain
valid throughout, so the existing roster keeps working with no migration. The change is additive and
flag-gated; reverting the commit restores prior behavior with no data to undo (nothing new is
persisted beyond the env var, which stays human-editable).
