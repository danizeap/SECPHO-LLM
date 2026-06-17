# Tasks

## Change

03-dataset-wide-chat

## Implementation

- [x] Add path constants `EVENTS_PATH` / `RETOS_PATH` / `SUBSCRIBERS_PATH` / `MEMBERS_ALL_PATH` and load all four as optional CSVs in `load_data`.
- [x] Add `strip_accents`, `SYNONYM_MAP`, `SEARCH_STOPWORDS`, `expand_search_terms`, `text_contains_any` for accent-insensitive EN↔ES search.
- [x] Implement `search_events` + `render_events` (topic/tech/sector/province + upcoming/past timeframe).
- [x] Implement `list_retos` + `render_retos` with the `none_open` graceful fallback to most-recent retos.
- [x] Implement `_top_terms`, `ecosystem_overview` + `render_ecosystem_overview` (whole-dataset counts and top terms).
- [x] Implement `DIMENSION_CONFIG`, `infer_dimension`, `aggregate_stats` + `render_aggregate_stats` (deterministic distributions).
- [x] Wire `search_events`, `list_retos`, `ecosystem_overview`, `aggregate_stats` branches into `tool_answer`.
- [x] Add `heuristic_route_question` and use it as the fallback inside `llm_route_question` (and directly when no API key).
- [x] Extend the `llm_route_question` prompt with the four new actions and routing rules.
- [x] Refresh CHAT_HTML welcome example prompts + sidebar "Try" list (EN/ES) to showcase events, retos, overview, breakdowns.
- [x] Add in-flight disabled send button and animated "thinking" dots in `sendMessage`.
- [x] Run verification (py_compile, import smoke test, deterministic spot checks).
