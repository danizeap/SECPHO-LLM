# Brief

## Change

06-tuned-weighting-reports

## User Need

A SECPHO curator wants to human-curate the matchmaking for one person directly in the chat — adjust how much each signal counts — and then turn that curated ranking into a shareable one-page value report.

## Problem

Packet 05 gave us a scoring console (`rerank_for_person`, `TUNING_SIGNALS`, `/api/rerank`) but (a) tuning was a detached lab with no deliverable, and (b) the precomputed pool held only each person's top-10, so re-ranking could only reshuffle 10 already-good matches. Cranking a weight could not surface a genuinely better-but-buried match that the default weighting had filtered out, which would make any "report from tuned weights" misleading.

## Scope

In scope:

- Deepen the precomputed candidate pool from top-10 to top-50 per person and regenerate `people_matches_v1_1_events.csv`, preserving each person's existing top-5 exactly.
- Backend functions for a tuned report: `weighting_text`, `report_for_person_weighted`, `llm_payload_for_person_weighted`, `llm_report_for_person_weighted`.
- A `GET /api/report-tuned` endpoint (auth-gated, "llm" rate bucket).
- In-chat flow: a `[tune:ID]` token on recommendation answers that renders an "Adjust weighting & report" button, plus the inline tuner panel (six sliders, live re-rank, generate-report button).

Out of scope:

- The model's deterministic scoring/ranking logic itself (math is unchanged; only the pool depth and report layer are added).
- A report download / file export, and the ES/EN/both download-language picker (deferred to a future export feature; reports currently render only in the chat).

## Acceptance Criteria

- [x] Each person's candidate pool is 50-deep, and every sampled person's pre-existing top-5 is byte-for-byte unchanged (`people_matches_v1_1_events.csv` regenerated to 19500 rows).
- [x] Tuning can surface genuinely buried matches: `rerank_for_person(74449, needs_overlap=100)` brings Patricia Valero (model rank #18) and Joan Labal Abad (model rank #35) into the top.
- [x] Recommendation answers (both `tool_answer` recommend_contacts and `chat_flow` rec_intent) carry a `[tune:ID]` token that renders an "Adjust weighting & report" button.
- [x] `GET /api/report-tuned` returns a 200 LLM report that states the curator's custom weighting in plain language; a bad id returns 400.
- [x] The report's ranking is produced by deterministic math (`rerank_for_person`); the LLM only explains it and never reorders it.

## Impact Areas

- Backend: New report-layer functions and the `/api/report-tuned` handler in `backend_api/mvp_web_app.py`.
- Frontend: `CHAT_HTML` tuner CSS, `[tune:]` token rendering in `markdown_to_chat_html`, and the `openTuner`/`buildTunerSliders`/`tunerRerank`/`resetTuner`/`generateTunedReport` JS.
- Data model: `people_matches_v1_1_events.csv` regenerated at 50-deep (`TOP_K` 10 -> 50); schema/columns unchanged.
- API: New `GET /api/report-tuned` (auth-gated, "llm" rate bucket); existing `/api/rerank` now operates against the 50-deep pool.
- AI/model behavior: The LLM writes the briefing from the human-curated ranking and states the weighting; the ranking stays pure math.
- Documentation: This change packet and the `recommendation-reports` capability spec.
- Operations/security: None new — reuses existing auth gate and rate-limit buckets.

## Open Questions

None.
