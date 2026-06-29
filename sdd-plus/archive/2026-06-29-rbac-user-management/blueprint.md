# Build Blueprint — rbac-user-management

> Tier: FULL (auth, permissions, sensitive-data gating, a privileged secret). No product code
> until the Owner signs off on this blueprint.

## 1. Product Goal

Give SECPHO real role-based access control plus a self-service user manager, so the cluster
team — not the developer — owns who can use the tool and exactly what each person can see and do.
Three roles (`dev` > `admin` > `user`); admins create org users from the UI; each user's access to
data and tools is granted by checkbox. This is the access layer the live-data platform (P4) needs
before any financial/PII source becomes chat-queryable.

## 2. Users

- **dev** — Daniel (`dani.paez.salazar@gmail.com`). Full access to everything, including system
  internals: the tool-calling loop, the feedback/learning inbox, the scoring console, and the user
  manager itself. Seeded directly via env, never editable from the UI.
- **admin** — Sergio (`sergio.saez@secpho.org`), Eli (`elisabeth.torralba@secpho.org`). All data +
  all tools, **and** can create/manage org users and set their grants. Cannot reach the dev-only
  system internals.
- **user** — created by an admin. Sees only the data and tools an admin checkboxed for them.

## 3. Core Workflows

1. **Admin creates a user.** Settings → Usuarios → "Añadir usuario": type a `@secpho.org` email
   (rejected otherwise), pick role (`usuario`/`admin`), tick the data + tool checkboxes, click
   "Generar contraseña" → the server mints a one-time password shown once for the admin to hand off
   → "Crear usuario" persists the row. The user is active after a ~90s redeploy.
2. **Admin edits / removes a user.** Toggle grants, change role, or delete — same persist path.
   Guard rails prevent locking the org out (see §10).
3. **A user logs in and is bounded.** Their session resolves to exactly their granted data + tools;
   a tool or data source they weren't granted is refused server-side (fail-closed), not hidden in
   the UI only.
4. **Dev sees everything.** No checkboxes apply to dev/admin — they implicitly hold all grants.

## 4. MVP Scope

- Third role `dev`; `dev ⊇ admin ⊇ user` precedence.
- Per-user grant set over a fixed catalog of data + tool keys (§7), with sensitive keys (financial,
  PII, scoring, feedback) default-off and only grantable by admin/dev.
- Settings → Usuarios tab: list users, add/edit/delete, generate one-time password, `@secpho.org`
  validation, checkbox grant matrix.
- Persist by rewriting `SECPHO_USERS` and PATCHing it onto the Render service via the Render API
  (Owner-chosen option 1). No new datastore.
- Fail-closed enforcement threaded through the agent tools, the data loaders for sensitive sources,
  and the admin-only pages/endpoints.

## 5. Non-Goals (intentionally not built yet)

- No external database, no persistent disk, no third-party auth provider.
- No SSO / OAuth / magic-link / email delivery (admin hands the password off out-of-band).
- No self-registration or password-reset-by-email flow (admin re-issues a password).
- No fine-grained per-row/per-field ACLs beyond the source-level grant catalog.
- No audit-log subsystem (a minimal action log line is fine; a full audit store is later).
- The WordPress-hosted roster (production end-state, §11) is documented but not built now.

## 6. System Components

- **Backend (`backend_api/mvp_web_app.py`)** — extend the existing auth: role vocabulary, grant
  catalog + resolution, fail-closed checks in `dispatch_tool`/`ctx` and the sensitive data paths,
  the `/api/org/users` endpoints, and the Settings → Usuarios UI (server-rendered HTML + delegated
  JS).
- **New module `backend_api/render_env.py`** — the only thing that talks to the Render API: read the
  current env, rewrite `SECPHO_USERS`, trigger a deploy. Flag-gated, mockable, never reachable by the
  client or the LLM.
- **External service: Render API** — `PATCH .../services/{id}/env-vars` + deploy trigger, authed by
  a new `RENDER_API_KEY` secret (Render dashboard → env, never in repo).
- **No frontend framework** — same server-rendered, data-attribute + delegated-listener pattern as
  the rest of the app (esprima guard applies).

## 7. Data Model Sketch

A user record (logical):

```
{ email, role ∈ {dev, admin, user}, pw_hash (pbkdf2_sha256$…), grants: set<grant_key> }
```

Grant catalog (the checkboxes):

| Key | Group | Sensitive | Default for new `user` |
|---|---|---|---|
| `data.socios` | Datos | no | on |
| `data.eventos` | Datos | no | on |
| `data.retos` | Datos | no | on |
| `data.proyectos` | Datos | no | on |
| `data.casos` | Datos | no | on |
| `data.financiero` | Datos | 🔒 yes | off |
| `data.contactos` (PII) | Datos | 🔒 yes | off |
| `tool.chat` | Tools | no | on |
| `tool.matchmaking` | Tools | no | on |
| `tool.scoring` | Tools | 🔒 yes | off |
| `tool.feedback` | Tools | 🔒 yes | off |

`dev` and `admin` implicitly hold the full catalog (`*`); their grant field is ignored. Sensitive
keys can only be set by an admin/dev and never auto-default on.

Persisted encoding (one line per user in `SECPHO_USERS`), backward compatible with today's 3-field
format:

```
email|role|pbkdf2_sha256$iters$salt$hash|grant1,grant2,grant3
            ^role now also accepts "dev"   ^new optional 4th field; absent ⇒ role-default grants
```

## 8. Data Flow

- **Read (every request):** cookie carries `sub` (email) + `role`. Grants are resolved **per
  request from the in-process `USERS` map keyed by email** — *not* stored in the cookie — so a
  grant change takes effect at the next redeploy (same ~90s as everything else) instead of lingering
  until the cookie expires. Shared-password sessions (no `USERS` entry) fall back to role-default
  grants. This makes revocation effectively immediate and keeps one source of truth.
- **Write (create/edit/delete user):** admin/dev-gated endpoint → validate (`@secpho.org`, role,
  grants, lockout guards) → under `STATE_LOCK`, re-read the current `SECPHO_USERS` from Render,
  apply the change, PATCH it back, trigger a deploy → respond with the one-time password (create
  only). On redeploy the app reloads `USERS` from the fresh env; the new/edited user is live.
- **Passwords** exist in plaintext only transiently: generated in memory, returned once over TLS in
  the create response, immediately hashed for storage. Never logged, never persisted in plaintext,
  never seen by the LLM.

## 9. API / Interface Boundaries

- `GET  /api/org/users` — list (admin/dev only): emails, roles, grants. No hashes, no passwords.
- `POST /api/org/users` — create (admin/dev only): `{email, role, grants[]}` → `{ok, one_time_password}`.
- `PATCH /api/org/users/{email}` — update role/grants (admin/dev only).
- `DELETE /api/org/users/{email}` — remove (admin/dev only), subject to lockout guards.
- All four sit behind the existing `/api` auth gate + a rate-limit bucket, reject non-admin with
  **403**, and validate every field server-side. The client is never trusted for role/grant.
- `render_env.py` exposes `update_users_env(new_value)` used only by these endpoints.

## 10. Auth & Permissions Assumptions

- `parse_session_cookie` accepts `role ∈ {user, admin, dev}` (today: `{user, admin}`).
- New helpers: `has_role(session, minimum)` (precedence dev>admin>user) and
  `has_grant(session, key)` (admin/dev ⇒ always true; user ⇒ membership in resolved grants;
  **missing/garbled grants ⇒ deny**).
- `is_admin()` stays true for `admin` and `dev`; a new `is_dev()` gates system internals.
- Enforcement points (all fail-closed, server-side):
  - **Agent tools** — each tool maps to a required grant in `dispatch_tool`; ungranted ⇒
    `{"error": "forbidden"}`, never executes. `search_*`/`list_*` for sensitive sources require the
    matching `data.*` grant.
  - **Sensitive data loaders/endpoints** — financial + PII sources only load/return for a caller
    holding `data.financiero` / `data.contactos`.
  - **Admin surfaces** — scoring console, feedback inbox, and all `/api/org/*` require admin/dev.
- **Lockout guards:** cannot delete or demote the last `admin`/`dev`; the env-seeded `dev` is not
  editable/deletable through the UI; an admin cannot grant themselves `dev`.

## 11. External Services / Integrations

- **Render API** — new dependency. Secrets: `RENDER_API_KEY` (privileged — can reconfigure the
  service) + `RENDER_SERVICE_ID`. Both live only in Render's env; absent ⇒ the user-manager write
  path is disabled and the UI says so (read-only roster). Cost: none beyond current hosting.
- **Production end-state (documented, not built):** move the roster into SECPHO's WordPress (their
  system of record) behind one authenticated endpoint their WP dev adds — instant, self-serve,
  custody fully on SECPHO. Swapping `render_env.py` for a `wp_users.py` writer is the only change.

## 12. Risks & Tradeoffs

- **`RENDER_API_KEY` is powerful.** Mitigate: Render-env-only, never in repo/logs/client/LLM; used
  only by the admin/dev-gated write path; documented rotation; LaunchGuardian secrets gate must pass.
- **Privilege escalation.** Mitigate: every role/grant check is server-side on signed sessions; the
  client cannot self-grant; sensitive grants are admin/dev-settable only.
- **Redeploy lag + blip.** A user change is live after a ~90s redeploy, which briefly restarts the
  app (drops the in-RAM live cache → re-pull). Acceptable for a roster that changes rarely; the UI
  states "activo en ~1–2 min."
- **Concurrent edits.** Two admins editing near-simultaneously: mitigated by `STATE_LOCK` + a fresh
  read-before-write from Render; last-writer-wins on a fresh read. Low risk at ~10 users.
- **Stale grants.** Resolved by deriving grants per-request from `USERS` (not the cookie), so the
  only lag is the uniform ~90s redeploy.
- **Free-tier hosting** isn't zero-downtime; document the brief redeploy blip.

## 13. Implementation Phases

- **P4a — role + grant core (backend, hermetic).** `dev` role; `load_users` parses the 4th grants
  field (backward compatible); grant catalog + role-default sets; `has_role`/`has_grant`;
  per-request grant resolution from `USERS`; cookie accepts `dev`. Unit tests.
- **P4b — fail-closed enforcement.** Map each agent tool → required grant; gate sensitive data
  loaders/endpoints; gate scoring/feedback/org surfaces to admin/dev. Tests prove a `usuario` is
  refused.
- **P4c — Render env writer (`render_env.py`).** PATCH `SECPHO_USERS` via the Render API; flag-gated;
  fully mockable; **no network in tests**.
- **P4d — Settings → Usuarios UI + `/api/org/users`.** list/create/update/delete, one-time password
  generation, `@secpho.org` validation, lockout guards, the checkbox matrix; delegated JS + esprima
  guard.
- **P4e — close-out.** `/drydock:verify` + verifier subagent + LaunchGuardian strict scan + spec
  sync + archive.

## 14. Testing Strategy

All hermetic (Render API and network mocked; no real deploys, no LLM). Cover: `SECPHO_USERS`
round-trip including legacy 3-field lines; role precedence; `has_grant` fail-closed on
missing/garbled grants; per-request resolution prefers `USERS` over cookie; a `usuario` is denied
sensitive tools and the org endpoints (403); `@secpho.org` validation; password gen→hash→verify
round-trip; lockout guard (cannot remove the last admin/dev); esprima inline-JS guard on the new UI.
New capability spec `access-control.md` carries the scenarios.

## 15. LaunchGuardian Handoff

P4e, before declaring launch-ready: full local strict scan. The secrets gate must confirm no
`RENDER_API_KEY`/tokens in tracked files; the auth changes and the privileged secret make this a
required gate, not optional.

## 16. Next Skill Recommendation

On Owner approval of this blueprint → implementation skill, phase by phase (P4a→P4e), each verified
and the change archived per close-out discipline before P5.

---

### Evidence note

- **Requirements extracted:** 3-tier RBAC (dev/admin/user); admin self-service user creation;
  `@secpho.org`-only; admin-generated one-time passwords; checkbox per-user data+tool grants;
  future tools appear as new checkboxes; zero new data custody.
- **Key decisions:** keep `SECPHO_USERS` env as the store, written via the Render API (Owner choice);
  grants resolved per-request from `USERS` (not the cookie) for near-immediate revocation; sensitive
  grants default-off and admin/dev-only; `render_env.py` isolates the privileged secret.
- **Assumptions:** app is deployed on Render with API access; ~10 staff accounts; roster changes are
  rare; TLS terminates at the platform.
- **Open questions:** (a) force-password-change-on-first-login now or later? (b) keep a lightweight
  action log line for user-management events in this change or defer? (c) exact Render API shape to
  confirm against current Render docs at P4c.
- **Rejected alternatives:** Supabase (reserved for wecollabify); paid Render disk (costs, leaves
  free tier); pure env-paste (Sergio/Eli have no Render dashboard → fails self-serve).
- **Result:** PASS WITH OPEN QUESTIONS — ready to build on approval; the three open questions are
  refinements, not blockers.
- **Next skill:** implementation (P4a first).
