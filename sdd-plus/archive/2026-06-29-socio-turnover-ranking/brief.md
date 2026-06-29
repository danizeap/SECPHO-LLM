# Brief

## Change

socio-turnover-ranking

## User Need

Answer "who are our biggest/highest-revenue members, and who do they collaborate with?" — a
network×financial question the agent could not answer in the live test (it correctly declined rather
than fabricate a ranking).

## Problem

No tool ranked socios by turnover/billing (live-test finding #2). The financial tools gave a cluster
overview and per-socio detail, but nothing produced a "top socios by revenue" list to chain into the
collaboration-network tools. So a perfectly reasonable composed question had no path.

## Scope

In scope:

- New deterministic tool `top_socios_by_turnover(limit)` — ranks socios by self-reported company
  turnover (`negocio_financiero.revenue`), highest first; gated `data.financiero`.

Out of scope:

- Ranking by SECPHO billing (invoiced total) — turnover answers the "biggest members" question; a
  billing-rank variant can follow if asked.
- Network reto-only caveat (#4) — separate change.

## Acceptance Criteria

- [x] `top_socios_by_turnover` returns socios sorted by turnover desc, unparseable values excluded.
- [x] Gated `data.financiero` (fail-closed in `dispatch_tool`); registered in the schema + grant map.
- [x] The eval-set gating-matrix snapshot includes it (drift caught deliberately).

## Impact Areas

- Backend: new `top_socios_by_turnover`; `TOOL_REQUIRED_GRANT`; `dispatch_tool`.
- Frontend: none.
- Data model: none.
- API: one new agent tool (schema added).
- AI/model behavior: the agent can now rank by revenue and chain to the network tools.
- Documentation: agentic-conversation + access-control deltas.
- Operations/security: financial-tier gate (same as the other financial tools).

## Open Questions

- None.
