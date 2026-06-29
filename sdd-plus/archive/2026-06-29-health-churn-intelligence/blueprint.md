# Build Blueprint — health-churn-intelligence (P5, slice 2)

> Tier: STANDARD→FULL (member-engagement intelligence + a sensitivity/gating decision on candid
> churn reasons). No product code until the Owner signs off — especially on the gating question (§10).

## 1. Product Goal

Turn the live engagement + membership data into PROACTIVE retention intelligence: flag socios going
quiet *before* they churn, and surface *why* members have left — deterministically (math decides, the
LLM explains), reusing data already loaded (activities + cuotas), persisting nothing.

## 2. Users

- **Any staff with `data.socios`** (the baseline member grant) — see engagement health: who's going
  quiet, activity trends, at-risk socios to reach out to.
- **Admins/dev (and `data.financiero`-granted)** — additionally see the candid churn reasons
  ("No creen en secpho", "No les aportamos"…), which are sensitive internal assessments.

## 3. Core Workflows

1. **"Who's going quiet?"** → active socios with no recent activity, ranked by staleness, with their
   last-activity date and recent activity count — a call list for outreach.
2. **"How healthy is the cluster?"** → counts of active vs going-quiet, activity-trend summary, and
   (gated) churn count + reason breakdown.
3. **"How's [socio] doing?"** → one socio's last activity, activity-by-quarter trend, tenure, status.
4. **"Why do members leave?"** (gated) → churn broken down by reason category + recent leavers.

## 4. MVP Scope

- Deterministic engagement signals from the already-loaded `actividades` (recency = days since last
  activity; trend = activity count by quarter/`[QN]`) joined to socios.
- Membership tenure + churn from the already-loaded `cuotas` (join/leave dates, status, reason).
- Tools: `at_risk_socios`, `socio_health`, `health_overview` (engagement parts), and `churn_breakdown`
  (the gated reasons part).
- Two-tier gating (see §10). All counts/recency/trends deterministic; the LLM narrates + may suggest
  outreach, never invents a number.

## 5. Non-Goals (this slice)

- No predictive ML / churn-probability model — deterministic heuristics only (recency + trend).
- No new data sources — reuse `actividades` + `cuotas` (already live). No persistence.
- No automated outreach/emails — it produces a list; humans act.
- Network graph + the eval set are separate later slices.

## 6. System Components

- **`backend_api/mvp_web_app.py`** — deterministic health functions + 3–4 gated agent tools
  (`TOOL_REQUIRED_GRANT` + `AGENT_TOOL_SCHEMAS` + `dispatch_tool` + a short agent-prompt note).
- Reuses the live frames already in `DATA` (`actividades`, `cuotas`); no `live_data.py` changes
  expected beyond what's loaded. No new external service, no new secret.

## 7. Data Model Sketch

- Engagement (computed, not stored): per socio → `{socio, last_activity_date, days_since_last,
  activity_count_total, activity_count_recent, by_quarter}` from `actividades`.
- Churn (from `cuotas`): `{socio, status, join_date, leave_date, tenure, churn_reason_type,
  churn_reason}` — the reason fields are the sensitive ones.

## 8. Data Flow

Read `actividades`/`cuotas` from the in-memory live frames → compute recency/trend/churn in pandas →
tools return rows + an as-of stamp → the agent narrates. Nothing written to disk. A caller without
the required grant is refused by `dispatch_tool` before the tool runs.

## 9. API / Interface Boundaries

New agent tools (ride `/api/agent`; no new HTTP endpoints):
- `at_risk_socios(days?)` — active socios with no activity in `days` (default ~120), ranked stalest-first.
- `socio_health(socio)` — one socio's engagement + tenure + status.
- `health_overview()` — cluster engagement health (active vs quiet counts, trend) + (gated) churn summary.
- `churn_breakdown()` — leavers by reason category + recent leavers (gated).

## 10. Auth & Permissions Assumptions — THE KEY DECISION

Two tiers, reusing existing grants (no new grant proposed):
- **Engagement** (`at_risk_socios`, `socio_health`, the engagement parts of `health_overview`) → gate
  `data.socios`. It's operational member-engagement data (activity recency/trend) — useful to most
  staff, no euros, no candid assessments.
- **Churn reasons** (`churn_breakdown`, and the reason fields wherever they appear) → gate
  `data.financiero`. The reasons are candid internal judgements about why members left and come from
  the 🔴 `cuotas` source; treating them as sensitive (same bar as financials) is the safe default.

**Open question for the Owner:** is `data.financiero` the right gate for churn *reasons*, or do you
want them (a) admin/dev-only regardless of grant, (b) a new dedicated `data.churn` grant, or (c)
folded under `data.socios` with the rest? My recommendation: `data.financiero` (no new grant; the
data is already in the financial source; admins who'd act on churn already hold it).

## 11. External Services / Integrations

None new. Reuses the live layer (`SECPHO_LIVE_DATA` + token) and the P4 grant model.

## 12. Risks & Tradeoffs

- **Candid churn reasons leaking** → the gating decision above; fail-closed enforcement; never in the
  report or the heuristic fallback.
- **Threshold arbitrariness** ("going quiet" = N days) → sensible default (~120 days), configurable;
  surface the threshold in the answer so it's transparent.
- **Date-quality** (some activity/leave dates malformed) → robust `dayfirst` parsing; rows with no
  parseable date handled explicitly (counted as "unknown", not silently dropped).
- **Hallucinated counts** → deterministic pandas; LLM quotes the numbers.
- **Zero-copy** holds — reuses in-RAM frames, persists nothing.

## 13. Implementation Phases

- **P5h-a — engagement signals** (gate `data.socios`): recency/trend helpers + `at_risk_socios`,
  `socio_health`, `health_overview` (engagement parts). Hermetic tests (exact recency/trend + gating).
- **P5h-b — churn analysis** (gate `data.financiero`): `churn_breakdown` + reason fields; reason data
  refused to non-granted callers. Hermetic tests.
- **P5h-c — close-out**: verify → verifier subagent → adversarial security review (churn-reason leak
  focus) → LaunchGuardian → spec sync → archive + commit.

## 14. Testing Strategy

Hermetic (inject synthetic `actividades`/`cuotas` frames into `DATA`): exact days-since-last and
by-quarter trend; at-risk ranking + threshold; tenure; churn-reason breakdown; and the gating (a
caller without `data.socios` is refused engagement; without `data.financiero` is refused churn
reasons). New/updated delta specs for the `agentic-conversation` + `access-control` capabilities.

## 15. LaunchGuardian Handoff

P5h-c: local scan (Linux/CI for semgrep), focused on the churn-reason gating (no candid reason leaks
to non-granted callers).

## 16. Next Skill Recommendation

On approval → implementation (P5h-a first), each phase verified, archived before the next P5 slice
(network graph), then the eval set across all of P5.

---

### Evidence note

- **Requirements:** flag socios going quiet (deterministic recency + trend) + surface churn reasons;
  reuse loaded data; zero-copy; gated.
- **Key decision:** two-tier gating — engagement behind `data.socios`, churn reasons behind
  `data.financiero` (Owner to confirm/adjust).
- **Assumptions:** `actividades` carries usable dates + `[QN]`; `cuotas` carries status/leave/reason
  (confirmed during the financial slice).
- **Open questions:** (a) churn-reason gate (above); (b) "going quiet" default threshold (~120 days?);
  (c) at-risk on activity-recency+trend only for v1, or also weight event/reto interest?
- **Rejected alternatives:** a churn-probability ML model (rejected — non-deterministic, off-thesis);
  a new data source (rejected — reuse loaded frames); putting churn reasons under `data.socios`
  (flagged — may be too open for candid internal assessments).
- **Result:** PASS WITH OPEN QUESTIONS — ready to build on approval; the open questions refine scope.
