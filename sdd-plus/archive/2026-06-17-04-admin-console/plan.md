# Plan

## Change

04-admin-console

## Approach

1. Add an `ADMIN_HTML` template with two sections — "Feedback inbox" and
   "Tool requests & learning loop" — plus header links back to chat, classic
   view, and sign out. Its inline script `fetch`es `/api/feedback-inbox`
   (rendered as preformatted markdown) and `/api/tool-requests` (rendered as
   cards showing tool name, effective status, and the originating question),
   degrading gracefully to "No ... access." text when a fetch is not OK.
2. Add a `GET /admin` branch in `do_GET` that reuses the packet-01 gates:
   redirect to `/login` when not authenticated, redirect to `/` when
   authenticated but not admin, otherwise serve `ADMIN_HTML`.
3. Enrich the existing public `GET /health` handler to add a `counts` object
   (official_socios, people, members, events, retos, subscribers, matches),
   `model` (`current_model()`), `auth_required` (`AUTH_REQUIRED`), and
   `admin_enabled` (`ADMIN_ENABLED`).
4. Add the "Admin console" sidebar block to `CHAT_HTML` linking to `/admin`,
   with EN and ES i18n strings.
5. Verify by compiling, hitting `/health`, and confirming the admin gate.

## Files Expected To Change

- `backend_api/mvp_web_app.py`
  - `ADMIN_HTML` constant (admin page markup + loader script).
  - `BaseRequestHandler.do_GET` — `GET /admin` route and enriched `GET /health` handler.
  - `is_admin()` — reused unchanged (delivered in packet 01).
  - Admin-only handlers `/api/feedback-inbox`, `/api/tool-requests`,
    `/api/tool-build-events` — surfaced by the console (gate via `send_forbidden`).
  - `CHAT_HTML` — "Admin console" sidebar block + `block_admin` i18n strings (EN/ES).

## Risks

- Leaking sensitive data through the public `/health` endpoint. Mitigated by
  exposing only aggregate row counts and boolean flags — no records, no secrets.
- Exposing admin views to non-admins. Mitigated by reusing the packet-01
  fail-closed `is_admin` gate on `/admin` and on each admin API endpoint
  (`send_forbidden` / 403 for non-admins, redirect for the page).

## Rollback

Revert the `ADMIN_HTML` constant, the `GET /admin` branch, the `/health`
`counts`/`model`/`auth_required`/`admin_enabled` additions, and the
"Admin console" sidebar block in `backend_api/mvp_web_app.py` (single-file
`git revert`/`git checkout` of those hunks). Alternatively, leaving
`ADMIN_PASSWORD` unset makes `ADMIN_ENABLED` false, so `is_admin()` is always
false and `/admin` plus the admin endpoints are inaccessible while `/health`
keeps working.
