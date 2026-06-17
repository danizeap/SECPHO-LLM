# Plan

## Change

06-tuned-weighting-reports

## Approach

1. Deepen the pool so tuning is honest: change `TOP_K` from 10 to 50 in `recommendation_engine/build_people_matcher_v1_1_events.py` and regenerate `people_matches_v1_1_events.csv`. Verify the regeneration preserves each sampled person's existing top-5 exactly while adding ranks 6–50.
2. Add a tuned-report layer in `backend_api/mvp_web_app.py`:
   - `weighting_text(weights)` — a plain-English statement of the curator's weighting, or a fixed default-weighting sentence when the sliders are untouched.
   - `report_for_person_weighted(member_id, weights, limit=5)` — deterministic one-page markdown built from `rerank_for_person`'s tuned top-5 (target header, per-candidate custom score, model-rank movement, evidence, "How To Read This").
   - `llm_payload_for_person_weighted` — JSON payload (person + tuned ranking + `weighting_text`) for the LLM.
   - `llm_report_for_person_weighted` — calls the LLM to write the briefing from the human-curated ranking, falling back to the deterministic report if the LLM is unavailable.
3. Expose `GET /api/report-tuned` — auth-gated, "llm" rate bucket; parse `id` (400 on bad id) and the six signal weights, return `report_markdown` + `report_html` (via `markdown_to_chat_html`).
4. Wire the in-chat flow:
   - `markdown_to_chat_html` converts `[tune:ID]` into an `onclick="openTuner(ID)"` "Adjust weighting & report" button (after `html.escape`, so the report HTML is escaped before token substitution).
   - Append `[tune:ID]` to recommendation answers in both `tool_answer` (recommend_contacts) and `chat_flow` (rec_intent).
   - Add tuner CSS and the `openTuner`/`buildTunerSliders`/`tunerRerank`/`resetTuner`/`generateTunedReport` JS so an inline six-slider panel re-ranks live against `/api/rerank` (50-deep pool) and "Generate report from this weighting" calls `/api/report-tuned`.

## Files Expected To Change

- `recommendation_engine/build_people_matcher_v1_1_events.py` — `TOP_K = 50`.
- `recommendation_engine/outputs/people_matches_v1_1_events.csv` — regenerated, 19500 rows.
- `backend_api/mvp_web_app.py` — `weighting_text`, `report_for_person_weighted`, `llm_payload_for_person_weighted`, `llm_report_for_person_weighted`; `[tune:]` rule in `markdown_to_chat_html`; the `[tune:ID]` append in `tool_answer` recommend_contacts and `chat_flow` rec_intent; the `GET /api/report-tuned` handler; `CHAT_HTML` tuner CSS and the tuner JS.

## Risks

- Regeneration silently changing existing top-5 results — mitigated by verifying each sampled target's top-5 is unchanged before/after.
- All-zero weights causing divide-by-zero in `weighting_text` — mitigated by the `or 1.0` guard on the weight total.
- A missing signal column causing `KeyError` in scoring — mitigated by `row.get(sig["key"], 0)` defaults in `rerank_for_person`.
- XSS via report content injected into chat HTML — mitigated by `html.escape` running before `[tune:]`/markdown substitution in `markdown_to_chat_html`.
- LLM reordering or inventing the ranking — mitigated by keeping the ranking in `rerank_for_person` (pure math) and prompting the LLM only to explain and keep the exact order.

## Rollback

- Revert the `weighting_text` / `report_for_person_weighted` / `llm_payload_for_person_weighted` / `llm_report_for_person_weighted` functions and the `/api/report-tuned` handler; remove the `[tune:]` rule in `markdown_to_chat_html` and the `[tune:ID]` appends — the chat returns to plain recommendation answers with no tuner button and no tuned report.
- Pool depth can be reverted independently by setting `TOP_K` back to 10 and regenerating; the existing top-5 (and the default report/recommendation paths) are unaffected either way.
