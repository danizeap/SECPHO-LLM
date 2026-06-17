# Plan

## Change

03-dataset-wide-chat

## Approach

1. Extend `load_data` to also load four optional CSVs via new path constants `EVENTS_PATH`, `RETOS_PATH`, `SUBSCRIBERS_PATH`, `MEMBERS_ALL_PATH`, using the existing `optional(path)` helper so a missing file degrades to an empty DataFrame instead of crashing.
2. Add accent/synonym search primitives: `strip_accents` (unicodedata NFKD), `SYNONYM_MAP` (EN→ES accent-stripped, e.g. photonics→fotonica, quantum→cuantica, semiconductors→semiconductores, cybersecurity→ciberseguridad), `SEARCH_STOPWORDS`, `expand_search_terms`, and `text_contains_any`.
3. Add deterministic query + render pairs: `search_events`/`render_events`; `list_retos`/`render_retos` (with a graceful `none_open` fallback to most-recent retos); `_top_terms` + `ecosystem_overview`/`render_ecosystem_overview`; `DIMENSION_CONFIG` + `infer_dimension` + `aggregate_stats`/`render_aggregate_stats`.
4. Wire the four new actions (`search_events`, `list_retos`, `ecosystem_overview`, `aggregate_stats`) into `tool_answer`, each producing a deterministic fallback string and passing structured evidence through `decorate_grounded_answer`.
5. Replace the dumb fallback inside `llm_route_question` with a real keyword router `heuristic_route_question` (also used directly when no API key is present), and extend the LLM router prompt with the four new actions + routing rules.
6. Refresh CHAT_HTML: welcome `prompt-grid` example prompts (ecosystem, events on photonics, retos, socios by province, recommend, report) and the sidebar `block_try` list (EN + ES); add in-flight send-button disabling and animated "thinking" dots in `sendMessage`.

## Files Expected To Change

- `backend_api/mvp_web_app.py`:
  - Path constants `EVENTS_PATH` / `RETOS_PATH` / `SUBSCRIBERS_PATH` / `MEMBERS_ALL_PATH`; `load_data` (4 optional loads).
  - `strip_accents`, `SYNONYM_MAP`, `SEARCH_STOPWORDS`, `expand_search_terms`, `text_contains_any`.
  - `search_events` / `render_events`; `list_retos` / `render_retos`.
  - `_top_terms`, `ecosystem_overview` / `render_ecosystem_overview`.
  - `DIMENSION_CONFIG`, `infer_dimension`, `aggregate_stats` / `render_aggregate_stats`.
  - `heuristic_route_question`; new branches in `tool_answer`; extended `llm_route_question` prompt.
  - CHAT_HTML welcome `prompt-grid` + `block_try` (EN/ES); `sendMessage` in-flight state (`.send:disabled`, `.thinking` dots).

## Risks

- Bad/missing date strings in `events_normalized.csv` / `retos_normalized.csv` — mitigated by `pd.to_datetime(..., errors="coerce")` and `.notna()` guards before comparisons.
- A source CSV absent at runtime — mitigated by `optional(path)` returning an empty DataFrame and every consumer guarding `empty`/missing-column.
- "No open retos" looking like a failure — mitigated by the explicit `none_open` status that shows the most recent retos with a clear header.
- Heuristic mis-routing without a key — mitigated by ordering (overview/aggregate/event/reto checks before person/company), and `is_event`/`is_reto` guards so "how many … events" routes to events, not aggregate.
- Touching the scoring path — avoided by design: these are read-only retrieval/analysis tools, no change to matcher math.

## Rollback

Revert the `03-dataset-wide-chat` commit(s) to `backend_api/mvp_web_app.py`. The change is self-contained: removing the four new `tool_answer` branches and the corresponding router-prompt/heuristic entries disables the new behavior while the rest of the chat keeps working. The four new CSV loads are optional, so deleting/withholding the CSVs also neutralizes events/retos/overview/aggregate features at runtime without code changes (they return empty results gracefully). No env var, migration, or data change to undo.
