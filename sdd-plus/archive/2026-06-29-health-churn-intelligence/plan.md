# Plan

## Change

health-churn-intelligence (P5, slice 2). Full design in [blueprint.md](blueprint.md).

## Approach

- **P5h-a** — engagement signals from `actividades`: `_socio_engagement` (recency/totals/180d) +
  tools `at_risk_socios`, `socio_health`, `health_overview`, gated `data.socios`. DONE.
- **P5h-b** — churn from `cuotas`: `churn_breakdown` (reasons + recent leavers + tenure) gated
  `data.financiero`; `at_risk_socios` active-member filter (`_active_member_socios`). DONE.
- **P5h-c** — close-out: verify → verifier → adversarial security review (churn-reason leak focus) →
  LaunchGuardian → spec sync → archive + commit.

## Files Expected To Change

- `backend_api/mvp_web_app.py` — engagement helpers + `churn_breakdown` + 4 tools + `TOOL_REQUIRED_GRANT`
  (data.socios / data.financiero) + `AGENT_TOOL_SCHEMAS` + dispatch handlers.
- `tests/test_health_churn.py` — NEW hermetic coverage (today_utc pinned; gating; active-only filter).
- `sdd-plus/specs/capabilities/{agentic-conversation,access-control}.md` — synced at close-out.

## Risks

- Candid churn reasons leaking → gated `data.financiero`, fail-closed; never in the report/fallback;
  adversarial review at close-out.
- At-risk surfacing departed socios → active-only filter (default) via membership status.
- Threshold arbitrariness → default 120 days, surfaced in the answer, configurable.
- Hallucinated counts → deterministic pandas; LLM quotes them.

## Rollback

Additive and flag-gated: with the live layer off, the frames are empty and the tools return empty.
Reverting the commit removes the tools; nothing persisted, nothing to undo. `data.financiero` defaults
off, so churn reasons are unreachable unless explicitly granted.
