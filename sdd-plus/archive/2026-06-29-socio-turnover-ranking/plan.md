# Plan

## Change

socio-turnover-ranking

## Approach

Add `top_socios_by_turnover(limit=10)`: parse `negocio_financiero.revenue` with `_parse_eur`, drop
unparseable, sort by revenue desc (deterministic tiebreak by socio name), return the top `limit` with
turnover (formatted) + employees + an as-of stamp. Register it: `TOOL_REQUIRED_GRANT` →
`data.financiero`, a `dispatch_tool` case, an `AGENT_TOOL_SCHEMAS` entry, and the eval-set
`EXPECTED_GRANTS` snapshot. The existing fail-closed gate in `dispatch_tool` enforces the grant.

## Files Expected To Change

- `backend_api/mvp_web_app.py` — `top_socios_by_turnover`, grant map, dispatch, schema.
- `tests/test_financial_tools.py` — ranking + gating tests.
- `tests/test_eval_set.py` — add the tool to the gating-matrix snapshot.
- `sdd-plus/changes/socio-turnover-ranking/specs/{agentic-conversation,access-control}.md` — deltas.

## Risks

- Adding a tool widens the agent surface; mitigated by the same fail-closed `data.financiero` gate as
  the other financial tools, snapshot-tested. No new data source (reuses `negocio_financiero`).

## Rollback

Revert the commit (function + 4 registration points + tests). No data, schema, env.
