# Capability: agentic-conversation (delta)

Delta for change `intelligence-stat-followups`. Adds scenarios to existing requirements; merged at
`/drydock:sync`.

## Requirements

### Requirement: Deterministic, gated financial tools

#### Scenario: Per-socio contribution total reconciles with the yearly figures
- **WHEN** `socio_financials` reports a socio's contributions
- **THEN** `contributions.total` is the euro sum of the per-year figures (not the source `"TOTAL"`
  field, which is not a euro amount), so the total reconciles with the per-year breakdown.

### Requirement: Health/churn intelligence tools

#### Scenario: At-risk includes active members with no recorded activity
- **WHEN** `at_risk_socios` runs in active-members-only mode
- **THEN** it includes active members whose recency is None — including those with NO activity record
  at all — surfaced first as the most dormant, so its total reconciles with
  `health_overview.going_quiet` (rows may carry `days_since_last: null`).

#### Scenario: No ungrounded trend claims
- **WHEN** answering about churn or engagement
- **THEN** the agent does not assert a temporal trend, a "recent pattern", or which factor is most
  common/recent unless a tool returned that breakdown — it describes only what the tools returned.
