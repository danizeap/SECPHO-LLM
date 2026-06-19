# Verification

## Change

sidebar-declutter

## Automated Checks

- [x] `ast.parse` + `-W error::DeprecationWarning` → clean.
- [x] esprima parses the chat inline `<script>` (no escaping breakage).
- [x] Full suite: `python -m pytest tests/` → 33 passed.
- [x] Served `CHAT_HTML` structure: `side-foot` present, ⚙ + `/admin` present; no `side-block`
      divs, no `block_*` blurbs, no sidebar scoring-console link.

## Manual Checks

- [ ] OWNER live glance on the deploy: the explainer cards are gone, ⚙ Admin sits at the bottom
      and opens the admin login, Sign out works, and the conversation list still shows above it.

## Documentation Updates

- [x] No spec change needed: presentational cleanup, no capability requirement changes; bilingual
      coverage preserved (admin_link added in en + es).
- [x] README / project context: no change needed.

## Result

PASS (static + suite green). One open item: the Owner's live glance.
