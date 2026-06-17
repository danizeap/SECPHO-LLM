# Verification

## Change

06-tuned-weighting-reports

## Automated Checks

- [x] `python -m py_compile` passes on the changed modules.
- [x] Pool regeneration verified to preserve each sampled target's existing top-5 exactly while deepening the pool 10 -> 50 (`people_matches_v1_1_events.csv` now 19500 rows).
- [x] `rerank_for_person(74449, needs_overlap=100)` surfaces buried matches: Patricia Valero (model rank #18, up 17) and Joan Labal Abad (model rank #35, up 33) — genuinely buried candidates appear, proving the deepened pool makes tuning honest.

## Manual Checks

- [x] Over HTTP: a recommendation answer carries the `openTuner` "Adjust weighting & report" button.
- [x] `GET /api/rerank` with `needs_overlap=100` returns Patricia Valero on top.
- [x] `GET /api/report-tuned` returns a 200 LLM report (~2904 chars) that states the curator's custom weighting in plain language.
- [x] `GET /api/report-tuned` with a bad id returns 400.
- [x] `GET /tuning` returns 200.
- [x] Independent drydock verifier review returned VERIFIED: all-zero weights cannot divide-by-zero (guarded), a missing signal column cannot `KeyError`, report HTML is escaped before token substitution (no XSS), the model never reorders scores, and there is no regression to the default report path.

## Documentation Updates

- [ ] README or user-facing docs updated, if needed.
- [ ] Project context updated, if needed.
- [x] Specs updated, if needed. (delta + living `recommendation-reports` capability spec)
- [ ] No documentation update needed. Reason:

## Result

PASS — deepened the pool to 50 so tuning is honest, and the in-chat tuner generates an LLM report from the curator's math-ranked weighting; verifier review VERIFIED.
