# Tasks

## Change

06-tuned-weighting-reports

## Implementation

- [x] Change `TOP_K` 10 -> 50 in `recommendation_engine/build_people_matcher_v1_1_events.py` and regenerate `people_matches_v1_1_events.csv` (19500 rows).
- [x] Verify the regeneration preserves each sampled person's existing top-5 exactly while deepening the pool to 50.
- [x] Add `weighting_text(weights)` — plain-English custom-weighting statement (or the model-default sentence), with an `or 1.0` guard against all-zero weights.
- [x] Add `report_for_person_weighted(member_id, weights, limit=5)` — deterministic one-page markdown from the tuned top-5.
- [x] Add `llm_payload_for_person_weighted` and `llm_report_for_person_weighted` — the LLM writes the briefing from the human-curated ranking and states the weighting; the order stays the math's.
- [x] Add the `GET /api/report-tuned` handler (auth-gated, "llm" rate bucket; 400 on bad id) returning markdown + chat HTML.
- [x] Make `markdown_to_chat_html` convert `[tune:ID]` into an "Adjust weighting & report" button (after `html.escape`).
- [x] Append `[tune:ID]` to recommendation answers in `tool_answer` (recommend_contacts) and `chat_flow` (rec_intent).
- [x] Add tuner CSS and the `openTuner`/`buildTunerSliders`/`tunerRerank`/`resetTuner`/`generateTunedReport` JS so the inline panel re-ranks live against `/api/rerank` and generates a report via `/api/report-tuned`.
- [x] Run verification (py_compile, rerank buried-match check, HTTP checks) and an independent verifier review.
