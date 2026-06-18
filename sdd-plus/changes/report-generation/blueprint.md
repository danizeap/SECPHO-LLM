# Build Blueprint — report-generation

Result: **PASS WITH OPEN QUESTIONS** (2 owner assets + 1 format confirmation). No code starts until the owner approves this blueprint.

## Production posture (2026-06-17 update — supersedes the MVP framing below)
The owner declared the project past MVP: everything ships production-ready or as close as the inputs allow ([[secpho-production-ready-standard]]). This change therefore delivers the report engine **plus Sections 1–5 to production quality** (polished output, real date handling — `dayfirst` parsing + attendance dates from registration filenames to fix the IVO "Fecha desconocida" bug — edge-case handling, comprehensive tests, full verification + a production-readiness review). The only things that remain genuinely incomplete are **missing inputs, not shortcuts**: Section 6 (Proyectos) needs the projects data, and exact branding needs `plantilla4.docx`. No "(en preparación)" placeholders ship — a section is either production-complete or its blocking input is named and requested. The "MVP Scope / Phases" below are kept for history; the operative scope is Sections 1–5 production.

## 1. Product Goal
Automate SECPHO's member-facing report — the "Informe de Valor y Oportunidades" (`.docx`) that staff hand to socios — by reproducing the existing IVO format and filling the **"Contactos Recomendados"** section (which the IVO leaves empty) with our deterministic contact matchmaker. Make it consistent (same format every run), automatable (regular delivery), and fix the IVO event/attendance bugs.

## 2. Users
- SECPHO staff (Sergio, Elisabeth, owner) — generate a report for a person or a company, optionally tweak by chatting, download the `.docx`, send it to the socio.
- Indirect: the socio/member who receives the report.

## 3. Core Workflows
1. Pick a person or company → generate the full 6-section report → review → download `.docx`.
2. (Later) tweak wording conversationally — the LLM polishes prose inside fixed slots only — then re-download.
3. (Later) batch-generate many reports at once for regular delivery.

## 4. MVP Scope (first useful version)
A `report_engine/` module that produces a real `.docx` from our existing data, deterministic-first:
- Sections **1 (Introducción)**, **2 (Resumen/Ficha)**, **3 (Contactos Recomendados = our matchmaker)**.
- Person **and** company variants.
- Output a downloadable `.docx` via a CLI entrypoint and a `/api/report` endpoint.
- Uses a neutral built-in template (programmatic styles) until `plantilla4.docx` arrives.
Proves the format end-to-end with the unique value (the matchmaker) already in place.

## 5. Non-Goals (intentionally not yet)
- Section 6 Proyectos (blocked on projects data).
- Exact branding (blocked on `plantilla4.docx`) — neutral styles until provided.
- LLM prose-polishing (start fully deterministic; add as opt-in later).
- Scheduled/automated batch delivery.
- Emailing/distributing reports to socios (staff send manually).
- PDF export (`.docx` first).
- Live WordPress API wiring (use our existing CSV snapshots; live refresh later).

## 6. System Components
- `report_engine/` (new Python package):
  - `data_access.py` — load our normalized CSVs (read-only).
  - `scoring.py` — deterministic event/reto scoring (ports the IVO weights onto our clean data).
  - `sections/` — one builder per section (profile, contacts, events, retos, projects), person + company variants; each returns structured content, no rendering.
  - `render_docx.py` — load the template (`plantilla4.docx` or the neutral default), register custom styles, write the document from the structured content.
  - `__main__.py` — CLI for single + batch generation.
- Integration into the existing app: a `POST /api/report` handler in `backend_api/mvp_web_app.py` and a "Generate report" action in the chat UI (the existing `[tune:ID]` flow is the natural hook).
- External: OpenAI only for optional prose-polish (later); none for MVP.

## 7. Data Model Sketch
Inputs (read-only, from `data/processed` + `recommendation_engine/outputs`):
- Person → `members_normalized` (id, name, socio, role, province, technologies, sectors, ambitos).
- Company → `socios_normalized` + `official_socios_readiness`.
- Contacts → `people_matches_v1` (target→candidate, scores, shared tech) — **our matchmaker**.
- Events → `events_normalized` (real dates, tech/sector/ambito, location) + `event_registrations_matched` (who attended what) + `person/socio_event_interest`.
- Retos → `retos_normalized` (title, desc, sectors, issuing/applying entities, dates).
- Projects → **GAP**: `Datos de Proyectos.xlsx` (owner to provide).
Output: an in-memory `Report` (ordered sections → content blocks) → rendered `.docx` bytes.

## 8. Data Flow
`member_id`/`socio` → `data_access` loads rows → section builders compute deterministic content (contacts from `people_matches`; future-event recs from `scoring` over `events_normalized`; attended history from `event_registrations_matched` joined to real dates; retos from `retos_normalized`) → `render_docx` fills the template → `.docx` returned (API) or written (CLI). Nothing leaves the system except optional LLM prose calls, which pass through `redact_pii` first.

## 9. API / Interface Boundaries
- `POST /api/report` `{type: "person"|"company", id}` → `.docx` (auth-gated like all `/api/*`).
- CLI: `python -m report_engine --type person --id <N> --out <file.docx>` (and `--batch`).
- `report_engine` is a library; the app and CLI both call it. No other module depends on its internals.

## 10. Auth & Permissions Assumptions
- `/api/report` sits behind the existing session auth gate (staff only) and the `llm` rate bucket if prose-polish is used. Reports embed member PII → same closed-pilot posture as the app; no new auth model. Generated reports are NEVER committed to the repo.

## 11. External Services / Integrations
- OpenAI (existing `OPENAI_API_KEY` + `LLM_DAILY_BUDGET`) — only for optional prose polish in a later phase. MVP has zero external dependencies.
- No new accounts or credentials.

## 12. Risks & Tradeoffs
- **PII**: reports are the member-PII deliverable → handle as sensitive (no committing outputs; redact before any LLM; sharpen Gate 14 GDPR before any non-staff exposure).
- **Template dependency**: branding blocked on `plantilla4.docx` → MVP uses neutral styles, isolated in `render_docx` so swapping the template later is low-risk.
- **Data freshness**: CSV snapshots, not live WordPress → reports reflect the last data pull; surface the snapshot date; live refresh is a later phase.
- **Event-bug parity**: must verify our event recs/attendance actually fix the IVO bugs (real dates from `events_normalized` + matched registrations, no "Fecha desconocida").
- **Scope creep**: the full report is large → phase strictly; Section 3 (our unique value) ships first.
- **Determinism**: structure + data stay deterministic; LLM only touches prose → guarantees "siempre el mismo formato."

## 13. Implementation Phases
- **Phase 1 (STANDARD)** — `report_engine` scaffold + `.docx` render + Sections 1–3 (intro, ficha, **contactos/matchmaker**), person + company, neutral template, CLI + `/api/report`. *No owner assets needed.*
- **Phase 2 (STANDARD)** — Sections 4–5 (events with real dates + attended history; retos recommend/emitted/applied). Verify the IVO event bugs are fixed.
- **Phase 3 (STANDARD)** — Section 6 Proyectos (needs projects data) + real branding via `plantilla4.docx`.
- **Phase 4 (STANDARD)** — "Generate report" UI action + optional LLM prose polish + PDF export.
- **Phase 5 (FULL)** — batch/scheduled generation for regular delivery (touches automation/ops/deployment).

## 14. Testing Strategy
- Golden-output tests: generate for known members/socios; assert section structure, that contacts come only from `people_matches` (math decides), dates are real (no "Fecha desconocida"), and determinism (same input → identical output).
- Structure-parity check against the 4 IVO example reports.
- Unit tests per section builder + scoring function.
- Manual: open generated `.docx`, eyeball against the IVO examples.

## 15. LaunchGuardian Handoff
Run LaunchGuardian before exposing `/api/report` beyond staff or shipping batch delivery — reports ARE the PII deliverable, so this directly sharpens the open Gate 14 (GDPR notice/retention/DSR) follow-up.

## 16. Next Skill Recommendation
On approval → `drydock:backend` to implement Phase 1 (`report_engine` + `/api/report`), with `drydock:testing` for the golden tests. Each phase is its own STANDARD change packet.

## Open Questions (need owner)
1. **`plantilla4.docx`** — the branded template (needed Phase 3; MVP uses neutral styles).
2. **Projects data** (`Datos de Proyectos.xlsx` or a source) — needed for Section 6 (Phase 3).
3. **Format confirmation** — `.docx`-first is assumed; is PDF needed for delivery, and when?
