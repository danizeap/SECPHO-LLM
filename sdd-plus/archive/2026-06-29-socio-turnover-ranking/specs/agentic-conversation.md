# Capability: agentic-conversation (delta)

Delta for change `socio-turnover-ranking`. Amends the financial-tools requirement; merged at `/drydock:sync`.

## Requirements

### Requirement: Deterministic, gated financial tools
The agent SHALL also expose `top_socios_by_turnover` — a deterministic ranking of socios by
self-reported company turnover (`negocio_financiero.revenue`), highest first, gated `data.financiero`
— so a "biggest/highest-revenue members" question can be answered and chained into the
collaboration-network tools. Unparseable turnover values are excluded; ordering is deterministic.

#### Scenario: Biggest members and their collaborators
- **WHEN** a `data.financiero` holder asks who the highest-revenue socios are (optionally, who they
  collaborate with)
- **THEN** `top_socios_by_turnover` ranks socios by turnover (highest first), which can be composed
  with `socio_network`; a caller without `data.financiero` is refused before the tool runs.
