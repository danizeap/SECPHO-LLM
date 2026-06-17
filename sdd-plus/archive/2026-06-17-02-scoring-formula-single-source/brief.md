# Brief

## Change

02-scoring-formula-single-source

## User Need

When a user asks the SECPHO assistant to explain how matches are scored, it must
always describe the exact formula that produced the scores it serves. A formula
that disagrees with the data undermines trust in the recommendations.

## Problem

`backend_api/mvp_web_app.py` held two scoring-weight representations that
disagreed. `llm_payload_for_person` used the correct 6-weight formula, but
`llm_answer_question` advertised a stale 4-weight formula (0.50 / 0.25 / 0.10 /
0.15) that omitted the location and personal-affinity signals. Depending on the
code path, the assistant could quote a scoring formula that did not match the
precomputed scores in
`recommendation_engine/outputs/people_matches_v1_1_events.csv`.

## Scope

In scope:

- Introduce a single source of truth for the in-app scoring-formula description.
- Make both the per-person payload and the question-answer paths describe the
  same 6-weight formula that the served CSV was computed with.

Out of scope:

- Changing any numeric weight or recomputing scores. The CSV and
  `build_people_matcher_v1_1_events.py` `WEIGHTS` dict are unchanged.
- Frontend tuning-console signals (already aligned at 44/24/14/10/6/2).

## Acceptance Criteria

- [x] One module-level `SCORING_WEIGHTS` dict (0.44 / 0.24 / 0.10 / 0.14 / 0.06
      / 0.02) is the only weight representation used by the app's LLM paths.
- [x] `llm_payload_for_person` and `llm_answer_question` both set
      `scoring_formula = SCORING_WEIGHTS`.
- [x] The chat scoring branch returns the plain-English `SCORING_FORMULA_TEXT`
      describing the same 6 weights.
- [x] No stale 0.50 / 0.25 / 0.15 formula literal remains in the app.
- [x] The 6-weight formula matches the `WEIGHTS` dict in
      `build_people_matcher_v1_1_events.py` that produced the served CSV.

## Impact Areas

- Backend: `backend_api/mvp_web_app.py` constants and three functions.
- Frontend: None.
- Data model: None.
- API: None (response shapes unchanged; only the formula values are corrected).
- AI/model behavior: Assistant now describes a single consistent scoring formula
  on every path; preserves the "math decides, the LLM explains" contract.
- Documentation: This change packet and the recommendation-scoring capability spec.
- Operations/security: None.

## Open Questions

None.
