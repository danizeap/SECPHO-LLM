# Spec Delta: live-projects-tool

Capability: agentic-conversation

P3 (first slice): the agent can now query SECPHO projects from the live in-memory table.

## MODIFIED Requirements

### Requirement: Tool-calling agent loop
The system SHALL answer chat questions by running a bounded tool-calling loop (`run_agent`) over the
OpenAI Responses API, capped BOTH by a step count (`max_steps=4`) AND by a cumulative wall-clock
budget (`AGENT_TOTAL_BUDGET_S=75`), where each model call's timeout shrinks with the remaining
budget. The model may call deterministic data tools in sequence and reason over their returned rows
before answering. The tools wrap existing deterministic functions: search_people, get_person_profile,
search_socios, get_socio_profile, rank_socios, list_events, list_retos, **list_projects**,
ecosystem_overview, aggregate_stats, recommend_contacts, rerank_contacts. `list_projects` lists/searches
SECPHO projects (proyectos) from the live in-memory table and returns **non-financial fields only**
(budgets are gated until the access model); it returns empty when the live layer is off.

#### Scenario: Projects question
- **WHEN** the user asks about SECPHO projects (e.g. "projects in photonics")
- **THEN** the agent calls `list_projects`, which filters the in-memory projects table by the query and returns matching projects (title, acronym, tech, sectors, partners, stage, dates) without any budget figures.

#### Scenario: Cross-source question chains tools
- **WHEN** a user asks a question that spans sources (e.g. top socios by province plus photonics events)
- **THEN** the agent calls the relevant tools in sequence and returns a grounded answer composed from the returned rows.
