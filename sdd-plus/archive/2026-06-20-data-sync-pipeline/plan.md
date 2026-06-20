# Plan — Build Blueprint (zero-copy live intelligence layer)

## Change

data-sync-pipeline

## 1. Product Goal
Turn SECPHO's live operational data into an LLM-queryable intelligence layer **that stores none of
it** — the platform owns understanding, not data. WordPress stays the system of record.

## 2. Users
SECPHO staff (chat over the live cluster data); admins (also the financial/PII data).

## 3. Core Workflows
Ask the chat anything across the cluster → grounded, current, freshness-stamped answer. Proactive
change-feed ("what shifted since the last refresh"). Reports (already built) now over live data.

## 4. Architecture — zero-copy
```
SECPHO WordPress (/wp-json/reports/v1/*, the ONLY store)
        │  live fetch (env token, server-side, parallel)
        ▼
In-memory normalized view  ──►  deterministic tools (SQL-style over in-RAM tables)
   (replaces static CSVs)   ──►  in-memory RAG index (text-rich sources)
        │  background refresher diffs new vs previous (in RAM)
        ▼
Live change-feed (alerts)            Persist NOTHING confidential
```

## 5. Data Flow
1. On startup: app serves immediately; a background worker fetches all 17 sources concurrently;
   each becomes queryable as it lands (progressive availability).
2. Normalize each source in memory into canonical entities (extend the existing normalizers).
3. Build the in-memory RAG index over text-rich sources (casos-éxito, project/reto descriptions, newsletters).
4. Refresher re-pulls on a tiered cadence; serves last-good (stale-while-revalidate); diffs vs the
   in-RAM previous snapshot → change-feed.
5. The LLM answers via deterministic tools (numbers from the in-memory tables) + RAG (text, cited);
   every answer carries freshness + provenance.

## 6. Data Model (from the live schema scan — schema only, no values pulled)
Sensitivity: 🔴 financial/PII · 🟡 mixed · 🟢 low.
| Source | Shape / key | ~Size | Sens | Notes |
|---|---|---|---|---|
| datoscontacto | list / `ID` | 2451 | 🔴 | names, emails, phones, NIF, addresses |
| datoscontacto-inversion | list / `ID` | 80 | 🔴 | investor PII |
| datosnegocio | list / `Socio` | 195 | 🔴 | turnover, investment; has `Fecha ult. act.` |
| altasbajas | dict / id-keyed | 318 | 🔴 | cuota amounts, join/leave dates, churn reasons |
| facturas-sistema | list / `Número` | 454/yr | 🔴 | invoices (year-param → multi-year history) |
| facturacion-pdte / -total, estado-cuotas, financiacion, suscriptores | (slow; re-fetch w/ longer timeout) | — | 🔴 | finances / subscribers |
| actividades | list (no id → hash) | 6131 | 🟡 | engagement log w/ dates — churn/health gold |
| proyectos | dict / id-keyed | 152 | 🟡 | 24 fields incl. budgets, partners, tech/sectors |
| members | (slow; re-fetch) | — | 🟡 | already normalized today |
| retos | dict / id-keyed | 179 | 🟢 | challenges (already handled) |
| casos-exito | list / `Título` | 59 | 🟢 | text-rich → RAG |
| fidelizacion | list | 12 | 🟢 | monthly retention % |
| newsletters | (slow; re-fetch) | — | 🟢 | text → RAG |

Change key per source = natural id (`ID`/`Número`/dict key/`Socio`) else content-hash. No `ETag`/
`Last-Modified` on responses (confirmed) → full-pull + in-RAM diff, not conditional requests.

## 7. API / Interface Boundaries
Outbound only: GET the 17 `reports/v1` endpoints with the env token, server-side. No new inbound API,
no new persistent store. Token never reaches the browser, never logged, never committed.

## 8. Auth & Permissions
Chat is staff-authenticated (today). NEW: financial/PII sources (🔴) are **admin-only** — the agent's
tools check role before answering from them. Non-admins get cluster/activity/project intelligence, not
the books.

## 9. External Services
SECPHO WordPress `reports/v1` (their infra, their custody). No DB vendor. OpenAI (existing) for
flagship reasoning + embeddings (RAG).

## 10. Tradeoffs → Mitigations (the design's spine)
- **No long-term history we own** → mine the source's own timestamps (activities/invoices/altas-bajas/
  fidelización carry dates → trends from one pull); year-param endpoints give multi-year finance; and
  push a **digest to SECPHO** so history accumulates on THEIR side.
- **No cross-restart change memory** → the refresher's **in-RAM diff** is the change-feed (works while
  running); **keep-warm** makes uptime continuous so this is effectively always-on.
- **Cold-start latency** → instant start + parallel/progressive background load.
- **Resilience to their API being down/slow** → **stale-while-revalidate** in RAM (serve last-good).
- **Their slow API** → tiered cadence (hours), parallel fetch. (No 304s available.)

## 11. Risks
- The app's RAM transiently holds confidential data while running (irreducible to reason over it) —
  processor not controller, nothing persisted; the only zero-RAM option is running in SECPHO's infra (prod).
- Render free-tier sleep → cold-start re-pull; mitigated by keep-warm + progressive load.
- Their API slow/flaky → SWR + retries; worst case a cold start during their outage (rare).
- PII/financial exposure via chat → the admin-only access model is mandatory, not optional.
- Token leakage → env-only, server-only, never logged/committed (WP-side hardening is their guy's job).

## 12. Implementation Phases (each drydocked end-to-end)
- **P0** — finish the schema map (re-fetch the slow endpoints w/ longer timeout) + capability spec.
- **P1** — live-pull + in-memory normalize for 3 safe sources (retos, proyectos, casos-éxito), replacing
  their CSV path; parallel/progressive load; freshness stamp. Prove "live, not snapshot" end-to-end.
- **P2** — refresher (tiered cadence, SWR) + in-RAM change-diff feed + keep-warm.
- **P3** — normalizers for all 17 + new LLM tools (projects, activities, finances) + in-memory RAG.
- **P4** — access model (admin-only 🔴) + freshness/provenance on every answer.
- **P5** — intelligence layer (health/churn, financial, network) + the eval set (the mixed-concept stress
  questions) + optional digest-to-SECPHO.

## 13. Testing Strategy
Hermetic by default (mock the endpoints with captured *schemas*, never real confidential values in tests).
Per phase: normalizer golden tests; tool-accuracy tests (numbers == in-memory query); RAG retrieval +
citation tests; access-model negative tests (non-admin cannot get financials); the eval set as a living
accuracy harness; esprima/AST guards for any served-page change.

## 14. LaunchGuardian Handoff
Before any deploy that exposes financial data: LaunchGuardian pass focused on the access model, the
token handling (env/secret, no logging), and no-persistence verification.

## 15. Files Expected To Change (P1+)
`backend_api/` new `live_data/` module (fetch, normalize, refresh, diff); `mvp_web_app.py` swaps the
CSV `DATA` load for the in-memory live view; new tools + RAG; tests; new capability spec.

## 16. Next Skill / Approval
This is FULL-tier. **Owner approval of this blueprint is the gate before P1 code.** Then implement phase
by phase with the verifier subagent per increment. PROJECT_CONTEXT updated to record the zero-copy posture.

## Rollback
Each phase is additive and behind a flag: if the live source is unreachable or disabled, the app falls
back to the existing CSV load. No data migration (there is no store).
