# Spec Delta: live-activities-tool

Capability: agentic-conversation

P3 (activities slice): the agent can now query SECPHO member activities (the engagement signal) from
the live in-memory table.

## MODIFIED Requirements

### Requirement: Tool-calling agent loop
The system SHALL answer chat questions by running a bounded tool-calling loop (`run_agent`) over the
OpenAI Responses API, capped BOTH by a step count (`max_steps=4`) AND by a cumulative wall-clock
budget (`AGENT_TOTAL_BUDGET_S=75`), where each model call's timeout shrinks with the remaining
budget. The model may call deterministic data tools in sequence and reason over their returned rows
before answering. The tools wrap existing deterministic functions: search_people, get_person_profile,
search_socios, get_socio_profile, rank_socios, list_events, list_retos, list_projects,
**list_activities**, ecosystem_overview, aggregate_stats, recommend_contacts, rerank_contacts.
`list_activities` lists/searches SECPHO member activities (actividades) from the live in-memory table,
most recent first, optionally filtered by socio and/or topic; it returns empty when the live layer is
off.

#### Scenario: Activities question
- **WHEN** the user asks about a socio's recent activity (e.g. "what has ACME been up to lately?")
- **THEN** the agent calls `list_activities`, which filters the in-memory activity log by socio/topic and returns the matching activities, most recent first.

#### Scenario: Cross-source question chains tools
- **WHEN** a user asks a question that spans sources (e.g. top socios by province plus photonics events)
- **THEN** the agent calls the relevant tools in sequence and returns a grounded answer composed from the returned rows.
