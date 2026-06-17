# Tasks

## Change

04-admin-console

## Implementation

- [x] Add the `ADMIN_HTML` template with "Feedback inbox" and "Tool requests & learning loop" sections plus header links (back to chat, classic view, sign out).
- [x] Add the inline loader script that fetches `/api/feedback-inbox` (markdown) and `/api/tool-requests` (cards) and degrades gracefully when a fetch is not OK.
- [x] Add the `GET /admin` route in `do_GET` that redirects unauthenticated users to `/login`, redirects non-admin sessions to `/`, and serves `ADMIN_HTML` for admins.
- [x] Enrich the public `GET /health` handler with the `counts` object (official_socios, people, members, events, retos, subscribers, matches) plus `model`, `auth_required`, and `admin_enabled`.
- [x] Confirm the admin-only `/api/feedback-inbox`, `/api/tool-requests`, and `/api/tool-build-events` handlers return `403 forbidden` for non-admins (reusing `is_admin`).
- [x] Add the "Admin console" sidebar block to `CHAT_HTML` with EN/ES i18n strings linking to `/admin`.
- [x] Run verification (py_compile, `/health` response, admin gate).
