# Tasks

## Change

live-projects-tool (P3 first slice)

## Implementation

- [x] `list_projects` fn (query filter; non-financial allowlist; empty-when-off).
- [x] Dispatch handler + `AGENT_TOOL_SCHEMAS` entry.
- [x] Hermetic tests (`tests/test_projects_tool.py`): filter, financial-exclusion, empty, tool registered.
- [x] Live proof: 38/152 projects match "fotónica"; budgets excluded.
- [x] agentic-conversation delta (twelfth tool) + verify + verifier + sync + archive.
- [ ] Owner glance (when live is on): ask the chat "qué proyectos hay de fotónica" → grounded list.
