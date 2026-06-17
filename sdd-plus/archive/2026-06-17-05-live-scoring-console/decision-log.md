# Decision Log

## Change

05-live-scoring-console

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-16 | Re-ranking is 100% deterministic with no LLM (`custom_score = sum(weight_i/100 * signal_i)`). | It literally is "math decides" made visible and interactive; preserves trust that the LLM never reorders. | Letting an LLM re-rank or narrate the order (rejected: breaks the principle and is non-reproducible). |
| 2026-06-16 | Sliders are 0-100 and normalized inside the scorer (divide by 100). | Intuitive whole-number range for non-technical curators while signals stay in [0, 1]. | Exposing raw 0-1 fractional weights (rejected: less intuitive to drag). |
| 2026-06-16 | Default slider weights derived from `SCORING_WEIGHTS` x100. | At defaults the console reproduces the model's own ranking, anchoring trust before any tuning. | Arbitrary equal or hand-picked defaults (rejected: would not match the live model). |
| 2026-06-16 | Re-score the existing precomputed candidate pool from `DATA["matches"]` rather than recomputing matches. | Fast, deterministic, and reuses verified model output; foundation the later in-chat tune->report flow builds on. | Recomputing the full matcher per slider change (rejected: slow and out of scope). |
