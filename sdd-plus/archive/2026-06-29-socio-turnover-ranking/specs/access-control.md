# Capability: access-control (delta)

Delta for change `socio-turnover-ranking`. Amends the financial-gate requirement; merged at `/drydock:sync`.

## Requirements

### Requirement: data.financiero gates the financial tools
The `data.financiero` grant SHALL gate the FIVE financial tools (`financial_overview`,
`socio_financials`, `cuota_status`, `list_invoices`, and `top_socios_by_turnover`), fail-closed in
`dispatch_tool`. The new ranking tool exposes turnover magnitude and so is the same sensitive tier.

#### Scenario: Turnover ranking needs data.financiero
- **WHEN** a caller without `data.financiero` invokes `top_socios_by_turnover`
- **THEN** `dispatch_tool` returns `forbidden` before the tool runs.
