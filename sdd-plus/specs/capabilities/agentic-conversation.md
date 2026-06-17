# Capability: agentic-conversation

## Purpose

A conversational analyst over SECPHO's cluster data: a bounded tool-calling agent that reasons over real socios/people/events/retos, preserves the deterministic matchmaker as the sole ranking authority, converses naturally, and degrades gracefully when the LLM is slow or unavailable.

## Requirements

### Requirement: Tool-calling agent loop
The system SHALL answer chat questions by running a bounded tool-calling loop (`run_agent`) over the OpenAI Responses API, capped BOTH by a step count (`max_steps=4`) AND by a cumulative wall-clock budget (`AGENT_TOTAL_BUDGET_S=75`), where each model call's timeout shrinks with the remaining budget. The model may call deterministic data tools in sequence and reason over their returned rows before answering. Eleven tools wrap the existing deterministic functions: search_people, get_person_profile, search_socios, get_socio_profile, rank_socios, list_events, list_retos, ecosystem_overview, aggregate_stats, recommend_contacts, rerank_contacts.

#### Scenario: Cross-source question chains tools
- **WHEN** a user asks a question that spans sources (e.g. top socios by province plus photonics events)
- **THEN** the agent calls the relevant tools in sequence and returns a grounded answer composed from the returned rows.

#### Scenario: Loop is bounded and exception-safe
- **WHEN** the model keeps requesting tool calls past the step cap, or a tool raises
- **THEN** the loop makes one final capped model call and the tool dispatcher returns `{"error": ...}` instead of raising, so a request never runs unbounded or 500s.

#### Scenario: Loop is bounded in time
- **WHEN** the model/tool calls are slow
- **THEN** each call's timeout shrinks with the remaining budget and, once the budget is spent, the loop stops and the endpoint falls back to `chat_flow` — so a single chat turn cannot exceed ~75s of outbound wait (kept under the proxy/CDN ~100s cutoff).

### Requirement: Conversational-first interaction
The system SHALL behave as a conversational assistant first, not a report generator, and SHALL reply at the size of the message. It SHALL greet and converse for greetings/small talk; answer direct data questions directly without asking permission; and for open or exploratory messages (e.g. "who should I test?", "show me an example") give a brief, concrete suggestion, OFFER the next step, and WAIT — it SHALL NOT produce a full recommendations report unprompted.

#### Scenario: Greeting
- **WHEN** the user sends a greeting ("hola")
- **THEN** the agent replies conversationally and offers what it can do, calling no tools and producing no report.

#### Scenario: Exploratory question offers and waits
- **WHEN** the user asks an open question like "¿quién me sugieres testear?"
- **THEN** the agent suggests a specific person with brief reasoning, offers to generate the report, and waits — it does not generate the report unprompted.

#### Scenario: Direct data question answered directly
- **WHEN** the user asks a direct data question ("¿cuántos socios hay por provincia?")
- **THEN** the agent looks it up with a tool and answers directly, without asking permission.

### Requirement: Grounded, no-invention answers
The system SHALL instruct the agent to use tools for real data and never invent people, companies, counts, scores, events, or retos; when tools return nothing relevant the agent says so plainly.

#### Scenario: No relevant data
- **WHEN** the tools return nothing relevant to the question
- **THEN** the agent states it plainly and suggests what it can answer instead of fabricating a result.

### Requirement: Math decides ranking
The system SHALL source recommendation rankings and scores only from the `recommend_contacts` and `rerank_contacts` tools, and SHALL NOT reorder, re-score, merge, or invent matches; no other tool emits a ranking. In chat, recommendations are presented as a concise ranked list with one line of evidence each plus the `[tune:THEIR_MEMBER_ID]` token; the full one-page report is written inline only when the user explicitly asks for "the report" / "el informe".

#### Scenario: Recommendation request
- **WHEN** a user asks who a person should connect with
- **THEN** the agent calls `recommend_contacts`, presents its `recommendations_ranked_by_model` order unchanged, preserves any `[person:ID]` token, and appends `[tune:THEIR_MEMBER_ID]` on a final line.

### Requirement: Reliable under variable model latency
The system SHALL set the OpenAI request timeout to 60s for both the agent step (`call_agent_step`) and the single-shot LLM call (`call_llm`), because gpt-5-mini latency is highly variable (measured 4–60s+ for identical calls). A latency spike within 60s SHALL be awaited rather than treated as a failure, so the chat does not silently fall back to the heuristic router on common spikes.

#### Scenario: Latency spike within budget is awaited
- **WHEN** a model call takes longer than 30s but under 60s
- **THEN** the agent waits for the real answer instead of falling back to the heuristic router.

### Requirement: Conversation memory from client history
The system SHALL build the agent input from the last ~6 client-supplied conversation turns plus an optional selected-person context line and the new message, so multi-turn follow-ups resolve against prior turns. Conversation state is not stored server-side (`store: False`); the client maintains the history array (capped at 12) and clears it on new chat.

#### Scenario: Follow-up references earlier turn
- **WHEN** the user sends a follow-up like "de esos, quien encaja mejor por necesidades?"
- **THEN** the agent uses the prior turns in history, looks up the referenced people, and returns a grounded comparison.

### Requirement: Privacy of bulk personal data
The system SHALL drop personal email from people returned in bulk lists (`_agent_compact_person`); an email is surfaced only for a single, specifically requested contact.

#### Scenario: People list omits emails
- **WHEN** a tool returns a list of people
- **THEN** each entry carries member_id, name, socio, role, technologies, and sectors but not email.

### Requirement: Auth-gated, fail-closed agent endpoint
The system SHALL expose `POST /api/agent` behind the `/api` authentication gate and the `llm` rate-limit bucket, reject an empty message with 400 and a body over 200000 bytes with 413, and fall back internally to `chat_flow` when the LLM is unavailable or returns an empty answer — never returning 500. The frontend chat always posts to `/api/agent`.

#### Scenario: No API key configured
- **WHEN** `OPENAI_API_KEY` is unset or the agent returns an empty answer
- **THEN** the endpoint serves the `chat_flow` router result so the chat still works.

#### Scenario: Empty message rejected
- **WHEN** a request body has no message text
- **THEN** the endpoint responds 400 `empty_message`.
