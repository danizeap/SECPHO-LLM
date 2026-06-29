# Brief

## Change

rbac-user-management

## User Need

SECPHO's team (not the developer) must own who can use the tool and exactly what each person can
see and do. Admins (Sergio, Eli) need to create org users themselves and grant per-user access to
data and tools by checkbox; the developer (Daniel) needs full `dev` access including system
internals. This is the access layer the live-data platform needs before any financial/PII source
becomes chat-queryable.

Full design in [blueprint.md](blueprint.md).

## Problem

Auth today is binary (`is_admin()` yes/no) with a flat `{user, admin}` roster baked into the
`SECPHO_USERS` env var, editable only by someone with a Render dashboard. There is no third `dev`
tier, no per-user grant model, and no way for Sergio/Eli to create users or scope access without
the developer. Sensitive sources (financial, PII) cannot yet be safely gated.

## Scope

In scope:

- Third role `dev`; precedence `dev ⊇ admin ⊇ user`.
- Per-user grant catalog (data + tool keys), sensitive keys default-off and admin/dev-only.
- Settings → Usuarios tab: list/create/edit/delete, one-time password generation, `@secpho.org`
  validation, checkbox grant matrix.
- Persist by rewriting `SECPHO_USERS` and PATCHing it via the Render API (`render_env.py`).
- Fail-closed enforcement in the agent tools, sensitive data loaders, and admin-only surfaces.

Out of scope:

- External DB / persistent disk / third-party auth / SSO / email delivery / self-registration.
- Password-reset-by-email; fine-grained per-row ACLs; full audit-log subsystem.
- The WordPress-hosted roster (production end-state) — documented, not built.

## Acceptance Criteria

- [ ] `dev`/`admin`/`user` resolve correctly; `dev` reaches system internals, `admin` does not.
- [ ] A `usuario` is refused (server-side, 403/`forbidden`) any tool or data source not granted.
- [ ] Admin can create a `@secpho.org` user with a one-time password and a checkbox grant set; non
      `@secpho.org` emails are rejected; the password is never logged or persisted in plaintext.
- [ ] Grants resolve per-request from `USERS`; revocation applies at the next redeploy.
- [ ] Lockout guards prevent removing the last admin/dev and editing the env-seeded dev via UI.
- [ ] Org endpoints reject non-admin callers; all hermetic tests pass; esprima guard passes.

## Impact Areas

- Backend: role vocabulary, grant catalog/resolution, fail-closed checks, `/api/org/users`.
- Frontend: Settings → Usuarios tab (server-rendered + delegated JS).
- Data model: `SECPHO_USERS` gains an optional 4th grants field (backward compatible).
- API: new `/api/org/users` CRUD; `render_env.py` writer.
- AI/model behavior: each agent tool gated by a required grant in `dispatch_tool`.
- Documentation: new `access-control` capability spec; PROJECT_CONTEXT/security note.
- Operations/security: new `RENDER_API_KEY`/`RENDER_SERVICE_ID` secrets; LaunchGuardian gate.

## Open Questions

- Force password change on first login now, or later?
- Keep a lightweight action-log line for user-management events in this change, or defer?
- Confirm the exact Render API env-var/deploy shape at P4c against current Render docs.
