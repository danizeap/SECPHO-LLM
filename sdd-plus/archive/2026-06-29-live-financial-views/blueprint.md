# Build Blueprint — live-financial-views (P5, slice 1)

> Tier: FULL (sensitive financial data, fail-closed gating, hallucination risk on numbers). No
> product code until the Owner signs off on this blueprint.

## 1. Product Goal

Make SECPHO's **financial picture** queryable and insightful through the chat — turnover, the
membership economics (cuotas), and invoicing — **deterministically** (math decides, the LLM only
explains), **live and zero-copy** (persist nothing), and **gated** so only `data.financiero`-granted
users (admins/dev by default) ever see a euro figure. This is the first P5 intelligence slice and the
first time the platform touches the 🔴 sources.

## 2. Users

- **Admins / dev** (implicitly hold `data.financiero`) — Sergio, Eli, Daniel: ask the chat about
  cluster revenue, who's behind on cuotas, a socio's financial summary, invoice history.
- **A `user` an admin explicitly grants `data.financiero`** — e.g. a finance staffer.
- **Everyone else** — never sees financial data; the tools refuse fail-closed.

## 3. Core Workflows

1. **Cluster financial overview** — "¿cuánto facturamos en cuotas este año?" / "resumen financiero" →
   deterministic aggregates (total cuota revenue, # socios by cuota tier, outstanding vs paid,
   turnover distribution), LLM narrates.
2. **Per-socio financials** — "muéstrame las finanzas de ACME" → that socio's turnover, cuota, and
   invoice/payment status.
3. **Cuota / payment status** — "¿quién está pendiente de pago?" → socios with outstanding/overdue
   cuotas (from `estado-cuotas` / `facturacion-pendiente`).
4. **Invoice lookup** — "facturas de ACME en 2025" → invoices filtered by socio/year/status, newest
   first.

## 4. MVP Scope

- Live-load (zero-copy) the financial sources into memory: `datosnegocio` (turnover/investment),
  `altasbajas` (cuotas, join/leave, churn reasons), `facturas-sistema` (invoices, year-param),
  and the `facturacion-pendiente`/`-total` + `estado-cuotas` summaries.
- Normalize each into a canonical in-memory frame (new `normalize_*` + `SOURCES`/`KEY_COLUMNS`
  entries in `live_data.py`), same pattern as the 4 existing sources.
- Four gated agent tools: `financial_overview`, `socio_financials`, `cuota_status`, `list_invoices`
  — each requiring `data.financiero` in `TOOL_REQUIRED_GRANT`, fail-closed.
- All figures computed deterministically in pandas; the LLM never types a number (mirrors the report
  rule). Every financial answer carries a freshness/as-of line.
- The financial sources join the background refresher, but their change-feed key samples are gated
  (no 🔴 record keys leak to non-granted callers).

## 5. Non-Goals (this slice)

- **Contact PII** (`datoscontacto`, NIF/phones/addresses, `-inversion` investor PII) — that's
  `data.contactos`, a separate concern; NOT loaded here.
- No financial data in the matchmaking **report** (the report stays non-financial, per prior
  decisions) — financial is chat-only and gated.
- No persistence, no financial datastore, no export — zero-copy holds.
- No forecasting/projections yet — descriptive aggregates only.
- The **eval set** and the other P5 slices (health/churn, network graph) are separate later slices.

## 6. System Components

- **`backend_api/live_data.py`** — add the financial `normalize_*` functions + `SOURCES`/
  `KEY_COLUMNS` entries; they load only when `live_enabled()` (flag + token), exactly like today.
  The slow `facturacion-*` endpoints get a longer fetch timeout / lazy load.
- **`backend_api/mvp_web_app.py`** — the four deterministic financial aggregate functions + their
  agent-tool wrappers, `TOOL_REQUIRED_GRANT` entries (`data.financiero`), `AGENT_TOOL_SCHEMAS`
  entries, and `dispatch_tool` handlers. Plus the change-feed key-gating for 🔴 sources.
- **No new external service**, no new secret — reuses `SECPHO_LIVE_DATA` + the existing WP token.

## 7. Data Model Sketch (canonical in-memory frames)

- `datosnegocio` → `{socio, turnover, investment, last_updated}` (key: `socio`).
- `altasbajas` → `{socio, cuota_amount, join_date, leave_date, status, churn_reason}` (key: id).
- `facturas` (from `facturas-sistema`) → `{invoice_no, socio, date, amount, status, year}` (key:
  `invoice_no`).
- `cuotas_estado` (from `estado-cuotas` / `facturacion-pendiente`) → `{socio, due, paid, outstanding,
  status}`.
- Exact source field names confirmed against the live endpoints at build time (same as the existing
  normalizers were).

## 8. Data Flow

Live-pull WP `reports/v1/{datosnegocio,altasbajas,facturas-sistema,facturacion-*,estado-cuotas}` →
normalize in memory → the gated tools read the frames, compute deterministic aggregates, and return
rows + an as-of timestamp → the agent narrates. Nothing is written to disk. A caller without
`data.financiero` never reaches the data: `dispatch_tool` returns `forbidden` before the tool runs.

## 9. API / Interface Boundaries

Four new agent tools (no new HTTP endpoints; they ride the existing `/api/agent` loop):
- `financial_overview()` → cluster aggregates.
- `socio_financials(socio)` → one socio's turnover + cuota + invoice status.
- `cuota_status(status?)` → socios pending/overdue/paid.
- `list_invoices(socio?, year?, status?)` → invoices, newest first.
Each is gated by `data.financiero`; results carry freshness. Bulk results never include contact PII.

## 10. Auth & Permissions Assumptions

- `data.financiero` (sensitive, default-off, admin/dev-settable) is the single gate, enforced via
  `TOOL_REQUIRED_GRANT` (fail-closed) — built and tested in P4.
- The heuristic fallback already requires `data.socios` + redacts PII; financial tools are agent-only
  and gated, so the fallback never surfaces financial data.
- Admin/dev hold `data.financiero` implicitly; a `user` only if an admin ticked it.

## 11. External Services / Integrations

WP `reports/v1` financial endpoints (already inventoried, 🔴). Reuses `SECPHO_LIVE_DATA` +
`SECPHO_API_AUTH_TOKEN`. No new secret, no new vendor. The slow `facturacion-*` endpoints need a
longer timeout (noted in the original data-pipeline plan).

## 12. Risks & Tradeoffs

- **Financial leakage to non-granted users** → fail-closed `data.financiero` gating on every tool;
  bulk responses carry no contact PII; the fallback is already gated. Adversarial security review at
  close-out will specifically hunt financial-leak paths.
- **Change-feed key leak** → gate the change-feed sample for 🔴 sources (only granted callers see
  financial record keys).
- **Hallucinated figures** → math-decides: all sums/counts computed in pandas; the LLM is instructed
  never to emit a number it wasn't handed (same discipline as the report).
- **Slow endpoints / timeouts** → longer fetch timeout + stale-while-revalidate (already in the
  refresher).
- **Custody** → still zero-copy (persist nothing); consistent with the Owner's TFM/non-custodian
  constraint. Financial data only ever lives transiently in RAM.

## 13. Implementation Phases

- **P5f-a — load + normalize** (hermetic): financial `normalize_*` + `SOURCES`/`KEY_COLUMNS` in
  `live_data.py`; unit tests parse sample payloads; off by default (no network in tests).
- **P5f-b — gated tools** : the four deterministic aggregate functions + tool wrappers +
  `data.financiero` gating + schemas; tests prove correct aggregates AND that an ungranted caller is
  refused.
- **P5f-c — provenance + change-feed gating**: freshness/as-of on financial answers; gate 🔴
  change-feed key samples.
- **P5f-d — close-out**: verify → verifier subagent → adversarial security review (financial-leak
  focus) → LaunchGuardian → spec sync → archive.

## 14. Testing Strategy

All hermetic (no network, no LLM): normalizers parse representative financial payloads; deterministic
aggregates are exact (golden numbers); `data.financiero` gating (ungranted → `forbidden`); bulk
results omit contact PII; change-feed key-gating; freshness line present. A couple of financial eval
questions seed the later eval-set slice.

## 15. LaunchGuardian Handoff

P5f-d, before exposing financial data: a LaunchGuardian pass focused on the access model and
financial-leak paths (the original plan flags this as mandatory before any deploy that exposes
financial data). Run on Linux/CI so semgrep actually runs.

## 16. Next Skill Recommendation

On Owner approval → implementation (P5f-a first), each phase verified, the change archived before the
next P5 slice (health/churn or network graph).

---

### Evidence note

- **Requirements extracted:** queryable + insightful financials (turnover, cuotas, invoicing),
  deterministic, live/zero-copy, gated behind `data.financiero`.
- **Key decisions:** load `datosnegocio`/`altasbajas`/`facturas-sistema`/`facturacion-*`/
  `estado-cuotas`; four gated tools; math-decides on every figure; contact PII (NIF) explicitly out
  of scope (separate `data.contactos` concern); financial stays out of the report.
- **Assumptions:** `SECPHO_LIVE_DATA` + token already set on Render (they are); exact field names
  confirmed at build time against the live endpoints.
- **Open questions (for the Owner):** (a) which views matter most / first — overview, per-socio,
  cuota-status, invoices (I propose all four)? (b) how many years of invoices to pull (current +
  prior, or full history)? (c) cluster overview to all `data.financiero` users, or per-socio detail
  for admins only? (d) confirm comfort with financial data flowing through app RAM (zero-copy, gated,
  never persisted).
- **Rejected alternatives:** loading contact PII in the same slice (rejected — different gate,
  bigger surface); persisting a financial store (rejected — zero-copy); LLM-computed figures
  (rejected — hallucination risk).
- **Result:** PASS WITH OPEN QUESTIONS — ready to build on approval; the open questions refine scope,
  they don't block.
- **Next skill:** implementation (P5f-a).
