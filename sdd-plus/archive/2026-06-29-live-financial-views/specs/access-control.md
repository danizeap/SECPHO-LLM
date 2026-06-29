# Capability: access-control (delta — financial tools gated)

## Requirements

### Requirement: data.financiero gates the financial tools
The `data.financiero` grant (sensitive, default-off, admin/dev-implicit, user only if granted) SHALL
gate the four financial tools (`financial_overview`, `socio_financials`, `cuota_status`,
`list_invoices`) via `TOOL_REQUIRED_GRANT`, enforced fail-closed in `dispatch_tool`. Financial data
SHALL NOT be reachable through any non-gated path: the heuristic fallback does not surface it, and it
is excluded from the matchmaking report.

#### Scenario: Granted vs ungranted
- **WHEN** the same financial tool is invoked by a caller with `data.financiero` and by one without
- **THEN** the granted caller gets the computed result; the ungranted caller gets `forbidden` and the
  tool never executes.
