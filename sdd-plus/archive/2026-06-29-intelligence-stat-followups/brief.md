# Brief

## Change

intelligence-stat-followups

## User Need

The intelligence figures must be correct and reconcile across tools, and the assistant must not
editorialize beyond what the tools returned — so the team can trust every number in the feedback round.

## Problem

Three deterministic-stat findings from the live test: (#3) `socio_financials.contributions.total`
passed through the source `"TOTAL"` field, which isn't euros (Eurecat showed `180` next to a
`27.410 €` year); (#5) `at_risk_socios` (11) under-counted vs `health_overview.going_quiet` (13)
because it dropped ACTIVE members with no activity record — the most dormant, and the highest-priority
outreach; (#6) the LLM editorialized a churn "recent pattern" the tools never returned.

## Scope

In scope:

- `contributions.total` = euro sum of the per-year figures (not the source `"TOTAL"`).
- `at_risk_socios` includes active members with no (or undated) activity, surfaced first; the total
  reconciles with `health_overview.going_quiet`.
- AGENT_INSTRUCTIONS: forbid asserting a temporal trend / "recent pattern" no tool returned.

Out of scope:

- The billing-rank tool (#2) and network reto-only caveat (#4) — separate changes.

## Acceptance Criteria

- [x] `contributions.total` is the summed yearly euros (Eurecat-style 180 vs 27.410 € resolved).
- [x] `at_risk_socios` surfaces no-activity active members first; `total == health_overview.going_quiet`.
- [x] AGENT_INSTRUCTIONS contains the no-ungrounded-trend rule.

## Impact Areas

- Backend: `socio_financials` (contributions), `at_risk_socios`.
- Frontend: none.
- Data model: none.
- API: `at_risk_socios` rows may now carry `days_since_last: null` (no recorded activity).
- AI/model behavior: AGENT_INSTRUCTIONS extended (no ungrounded trends).
- Documentation: agentic-conversation delta.
- Operations/security: none.

## Open Questions

- None.
