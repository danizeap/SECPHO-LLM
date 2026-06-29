# Capability: agentic-conversation (delta)

Delta for change `financial-turnover-robust-stat`. Adds one scenario to the existing
"Deterministic, gated financial tools" requirement; merged at `/drydock:sync`.

## Requirements

### Requirement: Deterministic, gated financial tools

#### Scenario: Cluster turnover reported as robust stats, not a misleading sum
- **WHEN** `financial_overview` summarizes member-reported turnover (`negocio_financiero`)
- **THEN** it reports robust statistics — `socios_with_turnover` (count), `median_turnover`, and
  `max_turnover` — and SHALL NOT report a raw `total_turnover` sum, because self-reported turnover is
  heavy-tailed (a few members report group/global figures) so a sum is dominated by outliers and
  misleads as a cluster total.
