# Brief

## Change

05-live-scoring-console

## User Need

SECPHO staff need to see and trust *how* the recommendation ranking is produced. They want to explore which signals drive each introduction and adjust the weights interactively, so the "math decides" principle is visible instead of a black box.

## Problem

The scoring weights were fixed in code (`SCORING_WEIGHTS`) and invisible to users. There was no way to inspect per-signal contributions, no way to see how a different weighting would re-order a person's candidate pool, and therefore no way to build trust in the deterministic ranking.

## Scope

In scope:

- A `TUNING_SIGNALS` constant declaring the six tunable signals, default weights, and display colors.
- A pure-math `rerank_for_person(member_id, weights, limit)` re-scoring of a person's precomputed candidate pool with per-signal contribution breakdown and movement vs. the default model rank.
- An auth-gated `GET /api/rerank` JSON endpoint.
- An auth-gated `GET /tuning` standalone "Scoring console" page (person search, six sliders, live re-ranked list).
- A sidebar "Scoring console" link in the chat UI.

Out of scope:

- The deeper candidate pool and the in-chat tune-to-report flow (a later packet that reuses `rerank_for_person`).
- Any change to the underlying matcher model or precomputed match scores.
- Any LLM involvement in re-ranking.

## Acceptance Criteria

- [x] Re-ranking with the default weights reproduces the model's own top candidate for a person (74449 -> Carlos Alberto Castano Moraga).
- [x] Re-ranking is 100% deterministic with no LLM call: `custom_score = sum(weight_i/100 * signal_i)`.
- [x] `GET /api/rerank` returns each candidate with per-signal contributions, `new_rank`, `default_rank`, `movement`, and shared-evidence fields.
- [x] `GET /tuning` serves the Scoring console page (HTTP 200) for an authenticated user.
- [x] Both `/tuning` and `/api/rerank` are gated behind authentication.
- [x] The chat sidebar exposes a "Scoring console" link to `/tuning`.

## Impact Areas

- Backend: `TUNING_SIGNALS`, `to_float`, `rerank_for_person`, `GET /api/rerank` and `GET /tuning` handlers in `backend_api/mvp_web_app.py`.
- Frontend: `TUNING_HTML` console page and the sidebar "Scoring console" link in `CHAT_HTML`.
- Data model: None (reads existing `DATA["matches"]` columns).
- API: New auth-gated `GET /api/rerank` and `GET /tuning` routes.
- AI/model behavior: None (re-ranking is pure math, no LLM).
- Documentation: None.
- Operations/security: New routes inherit the existing `is_authenticated()` gate and API rate-limit bucket.

## Open Questions

None.
