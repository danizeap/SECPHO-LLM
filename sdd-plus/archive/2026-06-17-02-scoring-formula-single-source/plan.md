# Plan

## Change

02-scoring-formula-single-source

## Approach

1. Add a module-level `SCORING_WEIGHTS` dict near the top config block holding
   the 6 weights (profile_similarity 0.44, structured_overlap 0.24,
   needs_overlap 0.10, event_interest_overlap_score 0.14, location_overlap_score
   0.06, personal_affinity_score 0.02) — matching the `WEIGHTS` dict that
   produced the served CSV.
2. Add a `SCORING_FORMULA_TEXT` constant: a one-line plain-English statement of
   the same formula, for the chat scoring branch.
3. Point `llm_payload_for_person` at `SCORING_WEIGHTS`.
4. Replace the stale 4-weight literal in `llm_answer_question` with
   `SCORING_WEIGHTS`.
5. Have `answer_question`'s scoring branch return `SCORING_FORMULA_TEXT`.
6. Verify: `py_compile`, grep for any remaining stale literal, and a live chat
   "explain the score logic" check.

## Files Expected To Change

- `backend_api/mvp_web_app.py`
  - New constants `SCORING_WEIGHTS` and `SCORING_FORMULA_TEXT` (top config block).
  - `llm_payload_for_person` — `scoring_formula` set to `SCORING_WEIGHTS`.
  - `llm_answer_question` — `scoring_formula` set to `SCORING_WEIGHTS` (stale
    4-weight literal removed).
  - `answer_question` — scoring branch returns `SCORING_FORMULA_TEXT`.

## Risks

- A drifted weight value would silently mislead users. Mitigated by mirroring the
  values that produced the CSV (`build_people_matcher_v1_1_events.py` `WEIGHTS`)
  and by a grep confirming no second representation survives.
- A typo could break import. Mitigated by `py_compile`.

## Rollback

`git revert` the commit, or restore the prior bodies of the three functions and
remove the two new constants. The change is description-only: it touches no
scores, data files, or response shapes, so reverting cannot affect rankings.
