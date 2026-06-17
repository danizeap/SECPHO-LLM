# Brief

## Change

04-admin-console

## User Need

SECPHO admins need one place to read captured chat feedback and review the
tool-learning loop (missing-tool proposals and the codex tool-build log),
instead of opening raw JSON/markdown endpoints in separate tabs. Operators also
need the app's data state to be observable for monitoring.

## Problem

The admin endpoints (`/api/feedback-inbox`, `/api/tool-requests`,
`/api/tool-build-events`) existed but had no human-readable surface, so admins
had to hit raw endpoints by hand. `/health` reported only liveness, giving no
visibility into how much data the running app had loaded.

## Scope

In scope:

- An admin-gated HTML page (`ADMIN_HTML`) served at `GET /admin` that renders
  feedback and tool-request data in one view.
- A sidebar "Admin console" link in the chat UI (EN/ES) pointing at `/admin`.
- Enriching the public `GET /health` JSON with dataset `counts`, `model`,
  `auth_required`, and `admin_enabled`.

Out of scope:

- The admin auth mechanism itself (`is_admin` / fail-closed gate were delivered
  in packet 01-app-authentication; reused unchanged here).
- Any change to how feedback or tool requests are captured or stored.
- Editing/mutating feedback or tool requests from the console (read-only).

## Acceptance Criteria

- [x] `GET /admin` serves `ADMIN_HTML` only for an authenticated admin session;
      an unauthenticated request redirects to `/login` and a non-admin
      authenticated session is redirected to `/`.
- [x] The admin page loads the feedback inbox from `/api/feedback-inbox` and the
      tool requests from `/api/tool-requests` and renders them in two sections.
- [x] `/api/feedback-inbox`, `/api/tool-requests`, `/api/tool-build-events`
      return `403 forbidden` for non-admin sessions.
- [x] `GET /health` is public and returns `counts` for official_socios, people,
      members, events, retos, subscribers, matches, plus `model`,
      `auth_required`, and `admin_enabled`, and exposes no sensitive data.
- [x] The chat sidebar shows an "Admin console" link to `/admin` (EN and ES).

## Impact Areas

- Backend: New `GET /admin` route and enriched `GET /health` handler in `backend_api/mvp_web_app.py`.
- Frontend: `ADMIN_HTML` page and the "Admin console" sidebar block in `CHAT_HTML`.
- Data model: None.
- API: `/health` response shape extended (additive); admin endpoints surfaced (no new endpoints added by this packet).
- AI/model behavior: None.
- Documentation: This packet; no end-user docs.
- Operations/security: `/health` intentionally public for monitoring, counts only (non-sensitive); admin views fail closed via the packet-01 `is_admin` gate.

## Open Questions

None.
