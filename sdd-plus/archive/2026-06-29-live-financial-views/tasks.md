# Tasks

## Change

live-financial-views (P5, slice 1). Full design in [blueprint.md](blueprint.md).

## Implementation

- [x] **P5f-a — load + normalize the financial sources** (`live_data.py`, hermetic). Schema-only
      probe confirmed the exact live field names. Four normalizers + registry: `negocio_financiero`
      (datosnegocio → turnover/investment), `cuotas` (altasbajas → cuota/join/leave/churn), `invoices`
      (facturacion-total → per-socio status/due/paid/amount), `contributions` (financiacion → per-year
      contributions). Added `SENSITIVE_SOURCES`, `SLOW_SOURCES` (longer timeout), `_join_list`,
      `_fetch_json(timeout=)`, `KEY_COLUMNS`. Tests: `tests/test_financial_normalizers.py` (6,
      synthetic exact-field payloads). Suite 116. Live proof: 195/318/4779/171 rows, every column
      populated (shapes only, no values).
- [x] **P5f-b — gated financial tools.** `_parse_eur` (Spanish/plain/negatives/'No definido') +
      `_fmt_eur` + `_inv_status` (Pagada/Vencida/Enviada/Cancelada) + `_fin_as_of` (provenance). Four
      deterministic tools `financial_overview` / `socio_financials` / `cuota_status` / `list_invoices`,
      all gated `data.financiero` in `TOOL_REQUIRED_GRANT` (fail-closed) + schemas + dispatch handlers.
      Agent prompt: financial figures quoted verbatim from tools, never computed by the LLM. Fixed a
      real-data bug the live proof caught: `Fecha de baja definitiva = "No consta"` means ACTIVE, not
      a leave (status keys on a real date now) → 140 active / 178 left. Tests:
      `tests/test_financial_tools.py` (10). Suite 126. Live proof: 4779/4779 amounts parsed, overdue
      count matches `Estado=Vencida`, year filter = 454 for 2025 (shapes/coverage only).
- [x] **P5f-c — provenance + change-feed gating.** Provenance: every financial tool returns an
      `as_of` stamp (`_fin_as_of`). Change-feed: `_change_entry` omits the changed-key sample for
      `SENSITIVE_SOURCES` (keeps counts only) so a surfaced feed can't reveal which socios had
      financial changes. Test in `tests/test_financial_normalizers.py`. Suite 127. (The feed isn't
      exposed by any endpoint/tool today — this is defensive for digests / future surfacing.)
- [x] **P5f-d — close-out.** verify → verifier subagent (PASS, one concern fixed: multi-value
      `Estado`) → adversarial security review (5 dimensions → **0 confirmed findings**) →
      LaunchGuardian (gitleaks/trivy/api/frontend 0; semgrep-Windows aside) → spec sync → archive +
      commit. Suite 128.

## Delta specs

- [x] Synced into living capabilities: `specs/live-data-platform.md` (financial sources + sensitive
      change-feed gating), `specs/agentic-conversation.md` (the 4 financial tools + LLM-quotes-only),
      `specs/access-control.md` (`data.financiero` gates the financial tools).

## Verification

- [x] `python scripts/sdd.py verify live-financial-views` ✓; full evidence in `verification.md`
      (128 tests, verifier PASS, adversarial review 0 findings).
