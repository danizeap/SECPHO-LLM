# Brief

## Change

09-agentic-chat

## User Need

SECPHO staff need to ask free-form questions over the whole cluster dataset (socios, people, events, retos) and get grounded answers in one conversation, including multi-turn follow-ups, instead of a chat that only routes single intents to the matchmaker.

## Problem

The chat was a single-intent router (`chat_flow`) that bridged to the recommender API. It could not reason across sources, chain lookups, or use prior turns, so cross-source and follow-up questions failed or required the user to restate context. The project plan's "Hermes agent" (call tools, reason over evidence, answer) was unrealized.

## Scope

In scope:

- A tool-calling agent loop over the OpenAI Responses API that wraps the existing deterministic data functions as 11 tools.
- A grounding system prompt enforcing "math decides, the LLM explains" and Phase-1/privacy rules.
- A new auth-gated, rate-limited `POST /api/agent` endpoint that runs the agent and falls back to `chat_flow` internally.
- Frontend: chat posts to `/api/agent` with client-managed conversation history.

Out of scope:

- Any change to ranking/scoring math (`recommend_contacts`/`rerank_contacts` remain the sole ranking source).
- Server-side conversation storage (stateless; client manages memory).
- Changes to existing endpoints (`/api/chat-flow`, `/api/rerank`, `/api/report-tuned`, `/tuning`, `/admin`).

## Acceptance Criteria

- [x] The chat answers cross-source questions by chaining tool calls and reasoning over returned rows.
- [x] Multi-turn follow-ups use prior conversation turns (last ~6) sent by the client.
- [x] Recommendation rankings come only from `recommend_contacts`/`rerank_contacts`; the agent never reorders or invents matches.
- [x] Bulk people lists drop personal emails via `_agent_compact_person`.
- [x] `[person:ID]` tokens are preserved and `[tune:ID]` is appended after recommendations.
- [x] `POST /api/agent` is behind the `/api` auth gate, rate-limited on the `llm` bucket, rejects empty messages with 400 and bodies > 200000 with 413.
- [x] When no API key is set or the agent returns empty, the endpoint falls back to `chat_flow` and never 500s.

## Impact Areas

- Backend: New agent loop, tool dispatcher, and `POST /api/agent` handler in `backend_api/mvp_web_app.py`.
- Frontend: `CHAT_HTML` `sendMessage` posts `/api/agent` with history; `newChat` clears history.
- Data model: None.
- API: New `POST /api/agent` endpoint; existing endpoints unchanged.
- AI/model behavior: Single-intent router replaced by a bounded tool-calling agent with a grounding prompt.
- Documentation: This change packet and the `agentic-conversation` capability spec.
- Operations/security: Auth gate, `llm` rate-limit bucket, body-size cap, stateless calls (`store: False`), email redaction in bulk lists.

## Open Questions

None.
