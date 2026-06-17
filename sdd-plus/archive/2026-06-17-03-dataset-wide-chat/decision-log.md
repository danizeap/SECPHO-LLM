# Decision Log

## Change

03-dataset-wide-chat

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-16 | Implement events/retos/overview/aggregate as deterministic data-retrieval tools, not scoring | Keeps "math decides, LLM explains" intact; these only read and count existing tables, they do not rank or recommend | Letting the LLM free-form answer over raw CSVs (rejected: non-deterministic, ungrounded) |
| 2026-06-16 | Replace the dumb `general_answer` fallback with a real keyword `heuristic_route_question` used inside `llm_route_question` | The app must be smart with OR without an OpenAI key; routing is the key robustness move for the demo | Requiring an API key for non-trivial routing (rejected: app too dumb when key absent) |
| 2026-06-16 | Add accent-insensitive (NFKD) + EN→ES synonym search for events and retos | SECPHO is a photonics (fotonica) cluster; "photonics" is the headline keyword and must match the Spanish "Fotonica" | Accent-sensitive substring match (rejected: missed "Fotonica"); a translation API call (rejected: slow, key-dependent, overkill) |
| 2026-06-16 | Give `list_retos(status=open)` a `none_open` fallback that shows the most recent retos | 0 retos are open as of 2026-06-16; an empty result reads like a failure, so show recent retos with a clear header instead | Returning an empty list / "no open retos" message only (rejected: dead-end UX) |
| 2026-06-16 | Load the four extra CSVs (events, retos, subscribers, members_all) as optional | Wider members/subscribers are enrichment, not the Phase-1 recommendation universe; a missing file must not crash startup | Adding them to the required-files list (rejected: would hard-fail load_data if any file is absent) |
