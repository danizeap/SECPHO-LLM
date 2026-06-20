# Verification

## Change

live-activities-tool (P3 activities slice)

## Automated Checks

- [x] `ast.parse` + `-W error::DeprecationWarning` on both files → clean.
- [x] Full suite: 51 passed (47 + 4: normalizer + 3 tool), hermetic.
- [x] `test_actividades_normalizer`: canonical columns, HTML stripped, 16-char synthetic `activity_id`,
      `KEY_COLUMNS["actividades"]=="activity_id"`.
- [x] `list_activities` tests: socio filter (only ACME); most-recent-first (15/03 before 20/01); empty
      `{activities:[],total:0}` when off; `list_activities` in `AGENT_TOOL_SCHEMAS`.

## Manual Checks

- [x] LIVE proof (token from `.env`): 6,131 activities queryable; most recent dated **today** (live!);
      129 match "fotónica"; tool registered (13 tools). Nothing persisted.
- [ ] OWNER glance (when `SECPHO_LIVE_DATA=1`): "qué ha hecho [socio] últimamente" → recent activities.

## Documentation Updates

- [x] agentic-conversation delta: the agent loop now wraps thirteen tools (adds `list_activities`).
- [x] README / project context: no change.

## Result

PASS (static + hermetic suite + live proof). The chat can now query the activity log; the most-recent
activity being dated today confirms the live layer is genuinely current. Engagement signal in place for P5.
