# Tasks

## Change

05-live-scoring-console

## Implementation

- [x] Add `TUNING_SIGNALS` constant (six signals, default weights, display colors).
- [x] Add `to_float(value, default=0.0)` query-param helper.
- [x] Implement `rerank_for_person(member_id, weights, limit)` pure-math re-scoring with per-signal contributions, default-rank, `new_rank`, `movement`, and shared-evidence fields.
- [x] Add auth-gated `GET /api/rerank` JSON handler.
- [x] Build `TUNING_HTML` console (person search, six 0-100 sliders, live contribution bars, movement markers) and serve it at auth-gated `GET /tuning`.
- [x] Add the "Scoring console" sidebar link to `/tuning` in `CHAT_HTML`.
- [x] Run verification (py_compile, import smoke test, live HTTP checks).
