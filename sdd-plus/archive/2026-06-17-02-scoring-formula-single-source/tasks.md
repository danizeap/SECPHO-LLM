# Tasks

## Change

02-scoring-formula-single-source

## Implementation

- [x] Add module-level `SCORING_WEIGHTS` dict (0.44 / 0.24 / 0.10 / 0.14 / 0.06 /
      0.02) as the single source of truth, matching the CSV-producing `WEIGHTS`.
- [x] Add `SCORING_FORMULA_TEXT` plain-English one-line statement of the same
      formula.
- [x] Point `llm_payload_for_person` `scoring_formula` at `SCORING_WEIGHTS`.
- [x] Replace the stale 4-weight literal in `llm_answer_question` with
      `SCORING_WEIGHTS`.
- [x] Return `SCORING_FORMULA_TEXT` from `answer_question`'s scoring branch.
- [x] Run verification: `py_compile`, grep for stale literal, live chat check.
