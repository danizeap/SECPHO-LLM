# Plan

## Change

live-financial-views (P5, slice 1). Full design in [blueprint.md](blueprint.md).

## Approach

Phased, each hermetic (see [tasks.md](tasks.md)):

- **P5f-a** — 4 financial normalizers + registry in `live_data.py` (exact live field names confirmed
  via a schema-only probe). DONE.
- **P5f-b** — deterministic aggregate layer (`_parse_eur`/`_fmt_eur`/`_inv_status`/`_fin_as_of`) + 4
  gated tools (`data.financiero`) + schemas + dispatch + agent-prompt rule. DONE.
- **P5f-c** — provenance (`as_of`) + change-feed gating for sensitive sources. DONE.
- **P5f-d** — close-out: verify → verifier → adversarial security review (financial-leak focus) →
  LaunchGuardian → spec sync → archive.

## Files Expected To Change

- `backend_api/live_data.py` — financial normalizers, `SOURCES`/`KEY_COLUMNS`/`SENSITIVE_SOURCES`/
  `SLOW_SOURCES`, `_join_list`, `_fetch_json(timeout=)`, `_change_entry` (sensitive-key gating).
- `backend_api/mvp_web_app.py` — `_parse_eur`/`_fmt_eur`/`_inv_status`/`_fin_as_of`, the 4 tools,
  `dispatch_tool` handlers, `AGENT_TOOL_SCHEMAS`, `TOOL_REQUIRED_GRANT`, agent prompt, DATA keys.
- `tests/test_financial_normalizers.py`, `tests/test_financial_tools.py` — NEW hermetic coverage.
- `sdd-plus/specs/capabilities/{live-data-platform,agentic-conversation,access-control}.md` — synced.

## Risks

- Financial leakage to ungranted users → fail-closed `data.financiero` gating; agent-only tools; no
  fallback/report path; adversarial security review at close-out.
- Hallucinated figures → deterministic pandas math; LLM forbidden from typing euros.
- Wrong amount parsing → `_parse_eur` handles Spanish/plain/negatives/`No definido`; live proof:
  4779/4779 parsed.
- Data-semantics traps (e.g. `"No consta"`) → caught by the live proof; status keys on a real date.

## Rollback

Additive and flag-gated: with `SECPHO_LIVE_DATA` off, the financial frames stay empty and the tools
return empty. Reverting the commit removes the tools/sources entirely; nothing is persisted, so there
is no data to undo. The `data.financiero` grant defaults off, so even with live on, no user sees
financials unless explicitly granted.
