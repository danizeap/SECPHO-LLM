# Plan

## Change

intelligence-stat-followups

## Approach

1. **#3 contributions total** — in `socio_financials`, compute `total` as `_fmt_eur(sum of
   _parse_eur(v) over contributions_by_year.values())` instead of passing through the non-euro source
   `"TOTAL"`. Reconciles with the per-year breakdown.
2. **#5 at-risk under-count** — rewrite `at_risk_socios` so, in active-only mode, "going quiet" =
   active members whose recency is None (incl. members with NO activity record at all) OR ≥ threshold.
   No-record members sort first (most dormant). This makes the list total equal
   `health_overview.going_quiet`. Non-active-only mode keeps feed-based behavior. Rows may carry
   `days_since_last: null` / `last_activity: ""`.
3. **#6 instruction** — extend the anti-derivation AGENT_INSTRUCTIONS bullet to forbid asserting a
   temporal trend / "recent pattern" / most-common-or-recent factor unless a tool returned that breakdown.

## Files Expected To Change

- `backend_api/mvp_web_app.py` — `socio_financials` contributions block; `at_risk_socios`; AGENT_INSTRUCTIONS.
- `tests/test_financial_tools.py` — contributions-total-from-years test.
- `tests/test_health_churn.py` — zero-activity at-risk + reconciliation test; trend-rule test.
- `sdd-plus/changes/intelligence-stat-followups/specs/agentic-conversation.md` — delta.

## Risks

- `at_risk_socios` output now allows `days_since_last: null`; the LLM must render it as "no recorded
  activity". Existing tests (`active_only` filter, threshold ranking) preserved and re-run green.

## Rollback

Pure deterministic code + an instruction string; revert the commit. No data, schema, env.
