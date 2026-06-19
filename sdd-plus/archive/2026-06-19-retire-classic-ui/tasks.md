# Tasks

## Change

retire-classic-ui

## Implementation

- [x] Map endpoint ownership (confirm `/classic`-only vs shared; `/api/search` shared with /tuning — kept).
- [x] Remove INDEX_HTML + `/classic` route + the four `/classic`-only GET handlers.
- [x] Conservatively remove now-unreferenced functions (only `hash_password` qualified).
- [x] Verify: AST/escape, esprima chat JS, full suite (32), boot check (/ 200, /classic 404, /tuning 200).
- [x] Confirm the agent + chat_flow still work (their report/answer functions retained).
- [ ] Owner glance (optional; legacy page was unlinked, nothing user-visible changes).
