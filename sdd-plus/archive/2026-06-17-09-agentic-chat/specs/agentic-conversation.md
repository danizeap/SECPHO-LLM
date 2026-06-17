# Spec Delta: 09-agentic-chat

Capability: agentic-conversation

## ADDED Requirements

### Requirement: Tool-calling agent loop
The system SHALL answer chat questions by running a bounded tool-calling loop (`run_agent`, `max_steps=6`) over the OpenAI Responses API, where the model may call deterministic data tools in sequence and reason over their returned rows before answering.

#### Scenario: Cross-source question chains tools
- **WHEN** a user asks a question that spans sources (e.g. top socios by province plus photonics events)
- **THEN** the agent calls the relevant tools in sequence and returns a grounded answer composed from the returned rows.

#### Scenario: Loop is bounded and exception-safe
- **WHEN** the model keeps requesting tool calls past the step cap, or a tool raises
- **THEN** the loop makes one final capped model call and the tool dispatcher returns `{"error": ...}` instead of raising, so a request never runs unbounded or 500s.

### Requirement: Grounded, no-invention answers
The system SHALL instruct the agent to use tools for real data and never invent people, companies, counts, scores, events, or retos; when tools return nothing relevant the agent says so plainly.

#### Scenario: No relevant data
- **WHEN** the tools return nothing relevant to the question
- **THEN** the agent states it plainly and suggests what it can answer instead of fabricating a result.

### Requirement: Math decides ranking
The system SHALL source recommendation rankings and scores only from the `recommend_contacts` and `rerank_contacts` tools, and SHALL NOT reorder, re-score, merge, or invent matches; no other tool emits a ranking.

#### Scenario: Recommendation request
- **WHEN** a user asks who a person should connect with
- **THEN** the agent calls `recommend_contacts`, presents its `recommendations_ranked_by_model` order unchanged, preserves any `[person:ID]` token, and appends `[tune:THEIR_MEMBER_ID]` on a final line.

### Requirement: Conversation memory from client history
The system SHALL build the agent input from the last ~6 client-supplied conversation turns plus an optional selected-person context line and the new message, so multi-turn follow-ups resolve against prior turns. State is not stored server-side (`store: False`).

#### Scenario: Follow-up references earlier turn
- **WHEN** the user sends a follow-up like "de esos, quien encaja mejor por necesidades?"
- **THEN** the agent uses the prior turns in history, looks up the referenced people, and returns a grounded comparison.

### Requirement: Privacy of bulk personal data
The system SHALL drop personal email from people returned in bulk lists (`_agent_compact_person`); an email is surfaced only for a single, specifically requested contact.

#### Scenario: People list omits emails
- **WHEN** a tool returns a list of people
- **THEN** each entry carries member_id, name, socio, role, technologies, and sectors but not email.

### Requirement: Auth-gated, fail-closed agent endpoint
The system SHALL expose `POST /api/agent` behind the `/api` authentication gate and the `llm` rate-limit bucket, reject an empty message with 400 and a body over 200000 bytes with 413, and fall back internally to `chat_flow` when the LLM is unavailable or returns an empty answer — never returning 500.

#### Scenario: No API key configured
- **WHEN** `OPENAI_API_KEY` is unset or the agent returns an empty answer
- **THEN** the endpoint serves the `chat_flow` router result so the chat still works.

#### Scenario: Empty message rejected
- **WHEN** a request body has no message text
- **THEN** the endpoint responds 400 `empty_message`.
