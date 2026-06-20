# Verification

## Change

live-projects-tool (P3 first slice)

## Automated Checks

- [x] `ast.parse` + `-W error::DeprecationWarning` → clean.
- [x] Full suite: 47 passed (43 + 4 projects-tool), hermetic.
- [x] `tests/test_projects_tool.py`: query filter (only "fotónica" project); financial fields
      (budget_total/aid_received/capital) absent from output; empty `{projects:[],total:0}` when the
      proyectos table is empty; `list_projects` present in `AGENT_TOOL_SCHEMAS`.

## Manual Checks

- [x] LIVE proof (token from `.env`): loaded real proyectos, `list_projects(query="fotónica")` → 38 of
      152 matched, real acronyms, budget fields excluded.
- [ ] OWNER glance (once `SECPHO_LIVE_DATA=1` on the deploy): "qué proyectos hay de fotónica" returns a
      grounded project list (no budgets).

## Documentation Updates

- [x] agentic-conversation delta: the agent loop now wraps twelve tools (adds `list_projects`).
- [x] README / project context: no change.

## Result

PASS (static + hermetic suite + live proof). The chat can now query SECPHO projects from the live
in-memory table; budgets gated until the access model.
