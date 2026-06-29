# Capability: access-control (delta — health/churn gating)

## Requirements

### Requirement: Two-tier gating for health/churn
Engagement tools (`at_risk_socios`, `socio_health`, `health_overview`) SHALL require `data.socios`;
the churn-reason tool (`churn_breakdown`) SHALL require `data.financiero`, because the reasons are
candid internal assessments of why members left. Reading membership status to restrict
`at_risk_socios` to active members exposes no reason or amount and is permitted at the `data.socios`
tier.

#### Scenario: Churn reasons need the financial tier
- **WHEN** a `data.socios`-only caller invokes `churn_breakdown`
- **THEN** `dispatch_tool` returns `forbidden`; only a `data.financiero` holder (admin/dev-implicit or
  explicitly granted) reaches the candid churn reasons.
