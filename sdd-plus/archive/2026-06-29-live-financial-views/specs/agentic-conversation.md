# Capability: agentic-conversation (delta — financial tools)

## Requirements

### Requirement: Deterministic, gated financial tools
The agent SHALL expose four financial tools — `financial_overview` (cluster aggregates),
`socio_financials` (one socio's billing/cuota/turnover/contributions), `cuota_status` (socios
overdue/pending, sorted by amount outstanding), and `list_invoices` (invoices by socio/year/status,
newest first). Every monetary figure SHALL be computed deterministically in the data layer (parsing
Spanish-formatted and plain amounts); the LLM SHALL quote those figures VERBATIM and SHALL NOT
compute, sum, estimate, convert, or round a euro figure itself. Each tool SHALL require the
`data.financiero` grant (fail-closed) and SHALL return empty when the live layer is off. Every
financial answer SHALL carry a freshness/as-of stamp.

#### Scenario: Financial question is answered from the tools
- **WHEN** a granted user asks a financial question (e.g. "who is behind on payments?")
- **THEN** the agent calls the matching financial tool and answers from the deterministic figures it
  returns, quoting amounts verbatim, with an as-of stamp.

#### Scenario: Ungranted caller is refused
- **WHEN** a caller without `data.financiero` triggers a financial tool
- **THEN** `dispatch_tool` returns `forbidden` before the tool runs and the agent says it cannot
  access financial data — it does not guess a figure.

#### Scenario: Invoice status comes from the source status
- **WHEN** invoices are aggregated
- **THEN** status is derived from the `Estado` field (Pagada/Vencida/Enviada/Cancelada); outstanding
  excludes Cancelada and totals only Vencida (overdue) + Enviada (sent).
