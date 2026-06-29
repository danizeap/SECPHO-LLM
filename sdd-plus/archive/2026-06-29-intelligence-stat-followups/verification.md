# Verification

## Change

intelligence-stat-followups

## Automated Checks

- [x] `python -m pytest tests/test_health_churn.py tests/test_financial_tools.py tests/test_eval_set.py`
      — 30 passed.
  - #3: `test_contributions_total_is_sum_of_years` — `contributions.total` = 30.000 € (27.410 + 0 +
    2.590), not the source `180`.
  - #5: `test_at_risk_includes_zero_activity_active_members` — a no-activity active member appears
    first with `days_since_last: null`; `at_risk.total == health_overview.going_quiet`. Existing
    `test_at_risk_socios_threshold_and_ranking` and `test_at_risk_active_only_filters_departed` still green.
  - #6: `test_prompt_forbids_ungrounded_trend_claims` — the rule is present.
- [x] `python -m pytest tests/` — 166 passed (no regression; +3 new).

## Manual Checks

- [ ] Post-deploy: ask a socio's financials → contributions total matches the year sum; ask "¿a quién
      contactar?" → any zero-activity members appear; "¿por qué se van?" → no invented "recent pattern".

## Documentation Updates

- [x] Specs updated: agentic-conversation delta (contributions total, at-risk reconciliation, no-trend).
- [x] No README change needed. Reason: internal correctness/instruction fixes, no new user workflow.

## Result

Implementation + automated verification COMPLETE (166 passed). Pending only the post-deploy spot-check.
