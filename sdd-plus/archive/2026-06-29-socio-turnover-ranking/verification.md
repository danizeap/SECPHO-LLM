# Verification

## Change

socio-turnover-ranking

## Automated Checks

- [x] `python -m pytest tests/test_financial_tools.py tests/test_eval_set.py` — 19 passed.
  - `test_top_socios_by_turnover_ranks_desc`: BIG > MID > SMALL by turnover; "No definido" excluded; limit honored.
  - `test_top_socios_by_turnover_gated`: `data.socios`-only caller → `forbidden`; `data.financiero` → ranked.
  - `test_gating_matrix_snapshot` + `test_every_schema_tool_is_gated`: the new tool is in both the grant
    map and the schema (snapshot updated deliberately).
- [x] `python -m pytest tests/` — 168 passed (no regression; +2 new).

## Manual Checks

- [ ] Post-deploy: "¿con quién colaboran nuestros socios de mayor facturación?" → ranks by turnover,
      then names collaborators (chains `top_socios_by_turnover` + `socio_network`).

## Documentation Updates

- [x] Specs updated: agentic-conversation (new tool + scenario) + access-control (gate now covers 5 financial tools).
- [x] No README change needed. Reason: additive agent capability, no new user-facing workflow.

## Result

Implementation + automated verification COMPLETE (168 passed). Pending only the post-deploy spot-check.
