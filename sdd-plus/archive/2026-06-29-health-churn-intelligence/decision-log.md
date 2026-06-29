# Decision Log

## Change

health-churn-intelligence

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-29 | Two-tier gating: engagement (`at_risk_socios`/`socio_health`/`health_overview`) → `data.socios`; churn reasons (`churn_breakdown`) → `data.financiero`. | Owner decision. Engagement is operational (who's quiet); churn reasons are candid internal assessments ("No creen en secpho", "No les aportamos") and warrant the same bar as financials. Reuses existing grants — no new grant. | Admin-only churn (rejected — too rigid); new `data.churn` grant (rejected — grant sprawl); all under `data.socios` (rejected — exposes candid judgments too broadly). |
| 2026-06-29 | `at_risk_socios` restricts to ACTIVE members by default (cross-ref cuotas status), `active_only=false` to include departed. | The naive recency list surfaced socios gone for ~13 years; the actionable list is current members who recently went quiet (178 → 11 in the live proof). Reading membership status exposes no reason/amount, so it's fine at the `data.socios` tier. | List everyone by staleness (rejected — not actionable); require `data.financiero` for at-risk (rejected — status isn't sensitive). |
| 2026-06-29 | "Going quiet" threshold default 120 days, configurable + surfaced in the answer. | Sensible default; transparent so users see the cutoff. | Hard-coded hidden threshold (rejected — opaque). |
| 2026-06-29 | Deterministic engagement/churn math; LLM quotes counts, may suggest outreach, never invents. | "Math decides, the LLM explains" — consistent with the rest of the system. | LLM-estimated risk scores (rejected — non-deterministic). |
