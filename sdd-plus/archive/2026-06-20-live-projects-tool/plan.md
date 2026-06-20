# Plan

## Change

live-projects-tool (P3 first slice)

## Approach

1. `list_projects(query, limit)` in `mvp_web_app.py`: read `DATA.get("proyectos")`; if empty, return
   `{projects:[], total:0}`; else token-filter (reusing `expand_search_terms` / `text_contains_any`)
   over title/acronym/tech/sectors/ámbitos/partners/program/type/stage/lead; return an allowlisted set
   of NON-financial fields (no budget_total/aid_received/capital).
2. Dispatch: `if name == "list_projects": return list_projects(...)`.
3. Schema: add a `list_projects` entry to `AGENT_TOOL_SCHEMAS`.
4. Tests: hermetic (inject a proyectos DataFrame) — query filter, financial-field exclusion, empty
   when no data, tool registered.

## Files Expected To Change

- `backend_api/mvp_web_app.py`; `tests/test_projects_tool.py` (new); agentic-conversation delta.

## Risks

- Surfacing project budgets to all staff → mitigated: budget fields excluded by allowlist (P4 gates them).
- Tool errors on missing/odd data → mitigated: `clean()` + empty-frame guard; hermetic tests cover it.

## Rollback

Revert the three hunks in `mvp_web_app.py` + the test. The tool is inert when live is off (empty table).
