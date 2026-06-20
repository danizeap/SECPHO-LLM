# Decision Log

## Change

live-projects-tool (P3 first slice)

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-20 | Ship projects as the first P3 tool | Highest-value, lowest-risk slice: 152 projects already loaded (P1/P2), Eli explicitly wanted Proyectos, and project info is semi-public | Start with a sensitive source (rejected: needs the access model first) |
| 2026-06-20 | Exclude budget/aid/capital from the tool output (allowlist non-financial fields) | Projects carry budget figures; surfacing them to all staff before the access model would leak financials | Show everything (rejected: pre-access-model leak) |
| 2026-06-20 | Mirror the `list_retos` pattern (deterministic filter over the in-memory table) | Consistency with the existing tools; math decides, the LLM explains; empty when live is off | A new query DSL (rejected: over-engineering for one entity) |
