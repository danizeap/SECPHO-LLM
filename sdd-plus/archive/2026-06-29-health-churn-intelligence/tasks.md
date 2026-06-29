# Tasks

## Change

health-churn-intelligence (P5, slice 2). Full design in [blueprint.md](blueprint.md).
Owner decision: engagement → `data.socios`; churn reasons → `data.financiero`. Defaults: quiet = 120 days.

## Implementation

- [x] **P5h-a — engagement signals** (gate `data.socios`). `_socio_engagement` (recency/totals/180d
      from the activity feed), `_live_as_of`, and three tools: `at_risk_socios` (going quiet, stalest
      first, threshold default 120d), `socio_health` (one socio's engagement), `health_overview`
      (active-recently vs going-quiet counts). Gated `data.socios` in `TOOL_REQUIRED_GRANT` +
      schemas + dispatch. Tests: `tests/test_health_churn.py` (6, today_utc pinned). Suite 134. Live
      proof: 317 with activity, 139 active / 178 quiet (≈ the 140/178 membership split).
- [x] **P5h-b — churn analysis** (gate `data.financiero`). `churn_breakdown` (leavers by reason
      category + recent leavers + tenure-at-leave) from `cuotas`, fail-closed `data.financiero`.
      Actionability fold-in: `_active_member_socios` + `at_risk_socios(active_only=True)` default
      restricts to current members. Tests +3. Suite 137. Live proof: 178 leavers grouped by reason
      (Económico 59 / No creen en secpho 41 / No les aportamos 39 / …); at_risk 178 → 11 actionable
      active members going quiet.
- [x] **P5h-c — close-out.** verify → verifier subagent (**VERIFIED**) → adversarial security review
      (4 dimensions → 1 MEDIUM found + fixed: euro-only anti-fabrication rule generalized + correctly-
      denominated `going_quiet_pct`) → LaunchGuardian (0 findings; semgrep-Windows aside) → spec sync
      → archive + commit. Suite 139.

## Delta specs

- [x] Synced into living capabilities: `specs/agentic-conversation.md` (health/churn tools +
      no-derived-rate rule) + `specs/access-control.md` (two-tier `data.socios` / `data.financiero`).

## Verification

- [x] `python scripts/sdd.py verify health-churn-intelligence` ✓; full evidence in `verification.md`
      (139 tests, verifier VERIFIED, adversarial review 1 MEDIUM fixed).
