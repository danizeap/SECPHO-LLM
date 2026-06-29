# Capability: live-data-platform (delta — financial sources)

## Requirements

### Requirement: Financial sources in the live layer (🔴, zero-copy)
The system SHALL live-load and normalize SECPHO's financial reports/v1 sources into canonical
in-memory frames, persisting nothing: `negocio_financiero` (datosnegocio → socio turnover +
investment), `cuotas` (altasbajas → cuota amount, join/leave dates, churn reason), `invoices`
(facturacion-total → per-socio invoice ledger with status/concept/due/paid/amount), and
`contributions` (financiacion → per-socio yearly contributions). These load only when the live layer
is enabled (flag + token); they are marked `SENSITIVE_SOURCES`; their EXPOSURE is gated at the tool
layer (the `access-control` capability), not at load. Larger financial endpoints use a longer fetch
timeout.

#### Scenario: Financial frames normalize from the live schema
- **WHEN** the live layer is on and a financial source is pulled
- **THEN** it is normalized into its canonical frame keyed for change detection
  (`socio`/`altabaja_id`/`invoice_id`), with every documented field mapped.

#### Scenario: A leave is a real date, not a placeholder
- **WHEN** `altasbajas` carries `Fecha de baja definitiva = "No consta"` (not recorded)
- **THEN** the socio is treated as ACTIVE (`status = activo`); only an actual date marks a `baja`.

### Requirement: Sensitive change-feed gating
The in-RAM change-feed SHALL record change COUNTS for every source but SHALL omit the changed-key
sample for `SENSITIVE_SOURCES`, so a surfaced feed can never reveal which socios had financial
changes to a non-granted caller.

#### Scenario: Financial change has counts but no key sample
- **WHEN** a financial source changes between pulls
- **THEN** the change entry carries added/modified/removed counts and `sensitive: true`, and its
  `keys` sample is empty.
