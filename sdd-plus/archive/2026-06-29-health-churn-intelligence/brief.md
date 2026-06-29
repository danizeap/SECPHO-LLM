# Brief

## Change

health-churn-intelligence (P5, slice 2). Full design in [blueprint.md](blueprint.md).

## User Need

SECPHO needs to retain members: spot socios *going quiet* before they churn (an outreach call-list)
and understand *why* members leave — deterministically, gated, reusing data already loaded.

## Problem

The live activity + cuotas data was loaded but no intelligence sat on top of it. There was no way to
ask "who's disengaging?" or "why do members leave?", and a naive recency list surfaces socios who
left years ago instead of actionable active members.

## Scope

In scope:

- Engagement signals from `actividades` (recency, totals, 180-day trend); tools `at_risk_socios`,
  `socio_health`, `health_overview` (gated `data.socios`).
- Churn analysis from `cuotas`: `churn_breakdown` (leavers by reason category + recent leavers +
  tenure), gated `data.financiero` (candid reasons).
- Actionability: `at_risk_socios` restricts to ACTIVE members by default (cross-ref cuotas status).

Out of scope:

- Predictive ML / churn-probability; new data sources; persistence; automated outreach; the network
  graph + eval set (later slices).

## Acceptance Criteria

- [x] Engagement signals deterministic + live-proven (139 active / 178 quiet ≈ membership split).
- [x] `at_risk_socios` active-only narrows 178 → 11 actionable active members going quiet.
- [x] `churn_breakdown` groups the 178 leavers by reason (Económico 59, No creen en secpho 41, …).
- [x] Engagement gated `data.socios`; churn reasons gated `data.financiero` (fail-closed).
- [ ] Verify + verifier + adversarial review + LaunchGuardian pass at close-out.

## Impact Areas

- Backend: `mvp_web_app.py` (engagement helpers + 4 tools, gating, schemas, dispatch).
- Frontend: none.
- Data model: reuses `actividades`/`cuotas` live frames; nothing new persisted.
- API: 4 new agent tools (ride `/api/agent`).
- AI/model behavior: deterministic counts; LLM quotes them, may suggest outreach.
- Documentation: delta specs (agentic-conversation, access-control).
- Operations/security: churn reasons gated `data.financiero`; engagement `data.socios`; zero-copy.

## Open Questions

- "Going quiet" threshold default 120 days (configurable) — confirmed.
- Could later weight event/reto interest into the at-risk score — deferred to a future enhancement.
