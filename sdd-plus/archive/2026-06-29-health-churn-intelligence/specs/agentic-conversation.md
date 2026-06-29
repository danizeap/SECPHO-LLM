# Capability: agentic-conversation (delta — health/churn tools)

## Requirements

### Requirement: Health/churn intelligence tools
The agent SHALL expose deterministic health/churn tools: `at_risk_socios` (active socios going quiet,
ranked stalest-first, threshold default 120 days, active-members-only by default), `socio_health`
(one socio's engagement: last activity, recency, totals, recent 180-day trend), `health_overview`
(cluster active-recently vs going-quiet counts), and `churn_breakdown` (leavers grouped by reason
category + recent leavers + tenure-at-leave). Recency, counts, and trends SHALL be computed
deterministically; the LLM SHALL quote the numbers and MAY suggest outreach, never inventing a count.
Engagement tools require `data.socios`; `churn_breakdown` (candid reasons) requires `data.financiero`.

#### Scenario: Who's going quiet (actionable)
- **WHEN** a `data.socios` holder asks who to reach out to
- **THEN** `at_risk_socios` returns ACTIVE members with no recent activity, stalest first (long-departed
  socios excluded unless `active_only=false`), each with last-activity date and days-since.

#### Scenario: Why members leave (gated)
- **WHEN** a `data.financiero` holder asks why members churn
- **THEN** `churn_breakdown` returns leavers grouped by candid reason category plus recent leavers; a
  caller without `data.financiero` is refused before the tool runs.
