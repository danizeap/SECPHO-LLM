# Plan

## Change

05-live-scoring-console

## Approach

Concrete steps taken:

1. Declare `TUNING_SIGNALS`: the six signals with default weights (profile_similarity 44, structured_overlap 24, event_interest_overlap_score 14, needs_overlap 10, location_overlap_score 6, personal_affinity_score 2) and display colors. Defaults are `SCORING_WEIGHTS` x100; underlying signals are normalized to [0, 1].
2. Add `to_float(value, default=0.0)` helper for robust query-param parsing.
3. Implement `rerank_for_person(member_id, weights, limit=10)`: pull the person's candidate pool from `DATA["matches"]` (rows where `target_member_id == member_id`), establish the default model rank from `final_score`, then compute `custom_score = sum(weight_i/100 * signal_i)` per candidate, attach per-signal contributions, shared-evidence fields, re-sort by `custom_score`, and record `new_rank` plus `movement = default_rank - new_rank`. Pure math, no LLM.
4. Add the auth-gated `GET /api/rerank` handler: parse `id` and the six signal weights from query params, return `rerank_for_person(...)` as JSON.
5. Build `TUNING_HTML` (person search box, six 0-100 sliders, live re-ranked list with contribution bars and up/down movement markers) and serve it at the auth-gated `GET /tuning` route; the page calls `/api/rerank` on slider input (debounced).
6. Add a "Scoring console" sidebar block linking to `/tuning` in `CHAT_HTML`.

## Files Expected To Change

- `backend_api/mvp_web_app.py`
  - `TUNING_SIGNALS` constant
  - `to_float` helper
  - `rerank_for_person(member_id, weights, limit)`
  - `GET /api/rerank` handler
  - `TUNING_HTML` page + `GET /tuning` route
  - "Scoring console" sidebar block in `CHAT_HTML`

## Risks

- Custom re-ranking diverging from the model so users distrust the console. Mitigated by deriving slider defaults from `SCORING_WEIGHTS` and verifying that default weights reproduce the model's top candidate for person 74449.
- Exposing scoring internals to unauthenticated users. Mitigated: both `/tuning` and `/api/rerank` sit behind `is_authenticated()`; `/api/rerank` also passes through the API rate-limit bucket.
- Bad query params crashing the endpoint. Mitigated: `to_int` for `id` (returns 400 on invalid), `to_float` for weights (defaults to 0.0).

## Rollback

Pure additive change. To disable, remove the `GET /tuning` and `GET /api/rerank` route branches and the "Scoring console" sidebar block (the link 404s harmlessly if left). To fully revert, `git revert` the commit that introduced `TUNING_SIGNALS`, `rerank_for_person`, `TUNING_HTML`, and the two route handlers. No data, schema, or model state to undo.
