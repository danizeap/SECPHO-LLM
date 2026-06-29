# Plan

## Change

financial-turnover-robust-stat

## Approach

In `financial_overview`, replace the `total_turnover` raw `.sum()` with robust stats: keep
`socios_with_turnover` (count) and `median_turnover`, add `max_turnover` (surfaces the outlier), drop
the sum. A code comment records why (heavy-tailed self-reported turnover → a sum misleads). The
anti-derivation AGENT_INSTRUCTIONS already stop the LLM from re-computing a total.

## Files Expected To Change

- `backend_api/mvp_web_app.py` — `financial_overview` turnover block.
- `tests/test_financial_tools.py` — update the exact-overview assertion; add an outlier-injection test.
- `sdd-plus/changes/financial-turnover-robust-stat/specs/agentic-conversation.md` — delta scenario.

## Risks

- Output-shape change: any consumer expecting `total_turnover` breaks. Only consumer is the LLM
  (quotes whatever fields are present); no other code reads it (grep-confirmed: one test). Low risk.

## Rollback

Pure deterministic code; revert the commit. No data, schema, env, or migration.
