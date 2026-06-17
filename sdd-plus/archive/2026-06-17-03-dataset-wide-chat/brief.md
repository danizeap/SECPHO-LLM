# Brief

## Change

03-dataset-wide-chat

## User Need

A SECPHO operator using the chat wants to ask about the WHOLE dataset — events, retos, dataset overviews, and distributions — and get correct answers whether or not an OpenAI API key is configured, including English questions about Spanish data ("photonics" must hit "Fotonica").

## Problem

The chat was only a bridge to the matchmaker: it could answer about people, socios, and recommendations, but had no tools for events, retos, ecosystem overviews, or aggregate distributions. In fallback mode (no API key) the router returned `general_answer` for everything, so the app was far dumber without a key. Topic search also missed Spanish data because it was accent-sensitive and English-only — "photonics" and "foton" never matched "Fotonica".

## Scope

In scope:

- New deterministic query + render tools over events, retos, the ecosystem, and aggregate distributions in `backend_api/mvp_web_app.py`.
- Loading four more optional CSVs (events, retos, subscribers, all members) in `load_data`.
- A real keyword `heuristic_route_question` used as the fallback so routing works with OR without an API key.
- Accent-insensitive + EN↔ES synonym search applied to event and reto search.
- Chat UX: welcome example prompts / sidebar "Try" list showcasing the new breadth; in-flight disabled send button with animated "thinking" dots.

Out of scope:

- Any change to matchmaking scores or the "math decides, LLM explains" scoring path.
- Enriched `/health` (delivered in the admin-console packet).
- New data ingestion or normalization of the source CSVs themselves.

## Acceptance Criteria

- [x] Chat can search events by topic/technology/sector/province and timeframe, and render them.
- [x] Chat can list/search retos with open/closed status, and falls back to most-recent retos when none are open.
- [x] Chat can return a whole-dataset ecosystem overview with counts and top technologies/sectors/provinces.
- [x] Chat can return deterministic aggregate distributions (province, company_type, member_type, public_private, technology, sector, readiness).
- [x] All four new actions are wired into `tool_answer` and the `llm_route_question` prompt.
- [x] `heuristic_route_question` routes correctly by keyword so the app is smart with OR without an API key.
- [x] Search is accent-insensitive and maps EN→ES synonyms: `search_events("photonics")` and `("fotonica")` both return results.
- [x] Welcome prompts / sidebar showcase events, retos, overview, and breakdowns; send button disables in-flight with animated dots.

## Impact Areas

- Backend: New deterministic query/render functions, four new router actions, real heuristic fallback router, four more optional CSV loads.
- Frontend: CHAT_HTML welcome example prompts + sidebar "Try" list refreshed; `sendMessage` in-flight disabled send button and animated thinking dots.
- Data model: None (reads existing normalized CSVs; all four new loads are optional/graceful).
- API: None (no new endpoints; `/api/agent` request/response shape unchanged).
- AI/model behavior: Router prompt extended with four actions; heuristic fallback replaces dumb `general_answer`; data-retrieval tools only — scoring untouched.
- Documentation: This packet + delta and living capability specs.
- Operations/security: None (no new env vars, no auth/permission changes).

## Open Questions

None.
