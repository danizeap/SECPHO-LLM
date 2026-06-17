# Decision Log

## Change

09-agentic-chat

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-16 | Replace the single-intent router with a tool-calling agent loop. | Make the chat a real conversational analyst over the whole dataset, realizing the plan's "Hermes agent". | Keep extending the heuristic `chat_flow` router with more intents. |
| 2026-06-16 | Stateless agent with client-managed memory (last ~6 turns), `store: False`. | Robust; no dependence on OpenAI storing conversation state. | Server-side or OpenAI-managed conversation state. |
| 2026-06-16 | `recommend_contacts`/`rerank_contacts` are the only ranking source; the agent never reorders. | Preserve "math decides, the LLM explains"; no other tool can emit a ranking. | Let the LLM merge/re-score results from multiple tools. |
| 2026-06-16 | Drop personal email from bulk people lists via `_agent_compact_person`. | Privacy; emails are only for a single specifically requested contact. | Return full profiles including email in every list. |
| 2026-06-16 | Client always posts `/api/agent`; the server falls back to `chat_flow` internally. | Chat still works with no API key or on LLM error; the endpoint never 500s. | Branch on the client between an agent endpoint and the router endpoint. |
| 2026-06-16 | Prompt the agent to act with sensible defaults instead of asking to clarify. | Decisive, useful answers for SECPHO staff. | Ask clarifying questions whenever a request is underspecified. |
