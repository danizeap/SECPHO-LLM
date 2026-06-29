# Brief

## Change

live-financial-views (P5, slice 1). Full design in [blueprint.md](blueprint.md).

## User Need

SECPHO's admins/finance need the cluster's financial picture queryable through the chat — turnover,
membership economics (cuotas), and invoicing/payments — deterministically and gated, so they can ask
"how much cuota revenue this year?", "who is behind on payments?", "show me ACME's financials".

## Problem

The 🔴 financial sources were deliberately never loaded (no access model existed). With P4's
`data.financiero` grant now in place, the financial data can be exposed safely — but only computed
deterministically (no LLM-typed figures), gated fail-closed, and zero-copy (never persisted, given
the Owner's non-custodian constraint).

## Scope

In scope:

- Live-load + normalize the financial sources (`negocio_financiero`, `cuotas`, `invoices`,
  `contributions`) zero-copy.
- Four gated chat tools: `financial_overview`, `socio_financials`, `cuota_status`, `list_invoices`.
- Deterministic euro math (Spanish/plain parsing); LLM quotes figures verbatim; as-of provenance.
- Sensitive change-feed gating.

Out of scope:

- Contact PII (NIF/phones — separate `data.contactos` concern); financials in the matchmaking
  report; persistence/export; forecasting; the other P5 slices (health/churn, network graph) and the
  eval set.

## Acceptance Criteria

- [x] Financial sources load + normalize zero-copy; exact field mapping (live-proven).
- [x] Four tools return deterministic aggregates; LLM never types a figure.
- [x] Every financial tool gated `data.financiero`, fail-closed (ungranted → forbidden).
- [x] Invoice status from `Estado`; `"No consta"` = active, not a leave.
- [x] Change-feed omits key samples for sensitive sources.
- [ ] Verify + verifier + adversarial security review + LaunchGuardian pass at close-out.

## Impact Areas

- Backend: `live_data.py` (4 normalizers, registry, change-feed gating), `mvp_web_app.py` (parsers,
  4 tools, dispatch, schemas, grants, prompt, DATA keys).
- Frontend: none.
- Data model: 4 new live-only in-memory frames; no persisted schema.
- API: 4 new agent tools (ride `/api/agent`); no new HTTP endpoints.
- AI/model behavior: financial figures quoted verbatim from tools only.
- Documentation: delta specs (live-data-platform, agentic-conversation, access-control).
- Operations/security: 🔴 data gated behind `data.financiero`; zero-copy; needs `SECPHO_LIVE_DATA`.

## Open Questions

- Full invoice history vs current+prior year (default current+prior; full on request) — confirmed.
- Whether to add `facturacion-pdte` (slow pending ledger) later — deferred (Estado covers it).
