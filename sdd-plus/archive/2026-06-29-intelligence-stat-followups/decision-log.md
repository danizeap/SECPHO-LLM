# Decision Log

## Change

intelligence-stat-followups

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-29 | `contributions.total` = sum of parsed per-year euros | The source `"TOTAL"` isn't the euro sum (180 vs a 27.410 € year on live data); summing the years is honest and reconciles with the per-year display. The tool computes it deterministically (LLM still quotes verbatim) | Pass through source `"TOTAL"` (wrong); drop `total` and show only by-year (loses a useful figure) |
| 2026-06-29 | `at_risk_socios` includes no-activity active members, surfaced first | A member with zero activity is the MOST dormant and the top outreach priority, yet it was invisible; including it makes the list reconcile with `health_overview.going_quiet` (was 11 vs 13) | Make `health_overview` exclude no-activity members instead (wrong — no engagement signal IS dormancy); leave the discrepancy (confusing + hides the highest-priority members) |
| 2026-06-29 | Forbid ungrounded temporal-trend claims in AGENT_INSTRUCTIONS | The LLM asserted a churn "recent pattern" the tools never returned; the anti-derivation rule covered numbers but not qualitative trends | Leave as-is (lets the LLM invent trends) |
