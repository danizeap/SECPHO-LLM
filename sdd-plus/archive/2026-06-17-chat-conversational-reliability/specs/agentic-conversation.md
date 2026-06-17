# Capability: agentic-conversation (delta)

Delta from change `chat-conversational-reliability`. Merge into the living
`agentic-conversation` capability spec on sync.

## MODIFIED Requirements

### Requirement: Conversational-first interaction
The system SHALL behave as a conversational assistant first, not a report
generator, and SHALL reply at the size of the message. It SHALL greet and
converse for greetings/small talk; answer direct data questions directly without
asking permission; and for open or exploratory messages (e.g. "who should I
test?", "show me an example") give a brief, concrete suggestion, OFFER the next
step, and WAIT — it SHALL NOT produce a full recommendations report unprompted.
This replaces the prior "defaults to acting with sensible defaults rather than
asking the user to clarify" instruction, which caused full reports to be dumped
on chatty questions. (The no-invention / grounded-answer rules are unchanged.)

#### Scenario: Greeting
- **WHEN** the user sends a greeting ("hola")
- **THEN** the agent replies conversationally and offers what it can do, calling no tools and producing no report.

#### Scenario: Exploratory question offers and waits
- **WHEN** the user asks an open question like "¿quién me sugieres testear?"
- **THEN** the agent suggests a specific person with brief reasoning, offers to generate the report, and waits — it does not generate the report unprompted.

#### Scenario: Direct data question answered directly
- **WHEN** the user asks a direct data question ("¿cuántos socios hay por provincia?")
- **THEN** the agent looks it up with a tool and answers directly, without asking permission.

#### Scenario: Recommendations are concise unless the full report is requested
- **WHEN** the user explicitly asks for recommendations for a named person
- **THEN** the agent returns a concise ranked list (one evidence line each) plus the `[tune:ID]` token, and writes the full one-page report inline only when the user explicitly asks for "the report" / "el informe".

### Requirement: Tool-calling agent loop
The system SHALL answer chat questions by running a bounded tool-calling loop
(`run_agent`) over the OpenAI Responses API, capped BOTH by a step count
(`max_steps=4`) AND by a cumulative wall-clock budget (`AGENT_TOTAL_BUDGET_S=75`).
The eleven deterministic data tools are unchanged. Each model call's timeout
shrinks with the remaining budget; once the budget is spent the loop stops.

#### Scenario: Loop is bounded in time
- **WHEN** the model/tool calls are slow
- **THEN** each call's timeout shrinks with the remaining budget and, once the budget is spent, the loop stops and the endpoint falls back to `chat_flow` — so a single chat turn cannot exceed ~75s of outbound wait (kept under the proxy/CDN ~100s cutoff).

## ADDED Requirements

### Requirement: Reliable under variable model latency
The system SHALL set the OpenAI request timeout to 60s for both the agent step
(`call_agent_step`) and the single-shot LLM call (`call_llm`), because gpt-5-mini
latency is highly variable (measured 4-60s+ for identical calls). A latency spike
within 60s SHALL be awaited rather than treated as a failure, so the chat does not
silently fall back to the heuristic router on common spikes.

#### Scenario: Latency spike within budget is awaited
- **WHEN** a model call takes longer than the old 30s but under 60s
- **THEN** the agent waits for the real answer instead of falling back to the heuristic router.
