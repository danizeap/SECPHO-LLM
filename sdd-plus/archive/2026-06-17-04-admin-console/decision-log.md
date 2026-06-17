# Decision Log

## Change

04-admin-console

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-16 | Gate `/admin` and the admin API endpoints on the packet-01 `is_admin()` check (fail closed) | Keep one auth model; admin views must never be reachable by normal users | A separate admin auth scheme; gating only the page and not the endpoints |
| 2026-06-16 | Render the existing admin endpoints in one `ADMIN_HTML` page instead of opening raw JSON/markdown in new tabs | Give admins a readable single surface for feedback and the tool-learning loop | Linking out to raw `/api/...` responses; a heavier separate admin dashboard |
| 2026-06-16 | Keep `/health` public and expose only aggregate counts plus model/auth/admin flags | Allow ops/monitoring without auth while leaking no records or secrets | Auth-gating `/health`; returning full dataset rows; omitting counts entirely |
