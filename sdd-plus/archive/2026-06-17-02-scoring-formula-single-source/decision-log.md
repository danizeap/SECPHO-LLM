# Decision Log

## Change

02-scoring-formula-single-source

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-16 | Make `SCORING_WEIGHTS` / `SCORING_FORMULA_TEXT` the single source of truth for the in-app scoring formula | The app must never present a scoring formula that disagrees with the data it serves; one representation makes drift impossible | Leaving two literals and keeping them in sync by hand (rejected: already drifted once) |
| 2026-06-16 | Mirror the 6 weights (0.44/0.24/0.10/0.14/0.06/0.02) from the CSV-producing `WEIGHTS` dict; fix description only | Preserves the "math decides, the LLM explains" contract — the app describes, it does not recompute | Recomputing or re-tuning weights in the app (rejected: out of scope, would change rankings) |
| 2026-06-16 | Remove the stale 4-weight literal (0.50/0.25/0.10/0.15) from `llm_answer_question` rather than patch it | The literal omitted location and personal-affinity signals entirely; deleting it eliminates the divergent path | Updating the literal in place (rejected: leaves a second representation that can drift again) |
