# Decision Log

## Change

retire-classic-ui

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-19 | Retire `/classic` (INDEX_HTML) + its four exclusive GET endpoints | Orphaned legacy interface, unlinked, superseded by the main chat; reduces surface (Owner approved) | Keep it as a fallback (rejected by Owner) |
| 2026-06-19 | Conservative function removal: only names appearing exactly once | Guarantees no live (agent/chat_flow) function is removed; the call graph for `llm_report_for_person` etc. still has live callers | Aggressively remove the "free-form report" functions (rejected: the AGENT still uses them) |
| 2026-06-19 | Keep `/api/search` | Shared with the /tuning page, not `/classic`-exclusive | — |
| 2026-06-19 | Defer migrating the agent's inline report to the unified report | Bigger, separate change; `/classic` retirement is a clean standalone win | Bundle it here (rejected: scope creep + needs its own design) |
