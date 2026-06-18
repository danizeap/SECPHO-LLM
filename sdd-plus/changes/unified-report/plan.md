# Plan — Build Blueprint (unified-report)

## Change

unified-report

## 1. Product Goal
One trustworthy report: identical in chat and download, numbers from the math, matchmaking
*explained* (per-contact "why it's a good match"), so SECPHO can collect member feedback on it.

## 2. Users
SECPHO staff (generate/curate/download), and members (the report's subject + recipient).

## 3. Core Workflow
Ask in chat → see the report inline → optionally tune the weighting → download the **same** report
as `.docx`. What's on screen == the file.

## 4. Architecture: one model, two renderers, LLM in fixed slots
```
report_engine.build_report(subject, weights?) ──► ReportModel  (deterministic: ficha, ranked
        │  reads people_matches_v1_1_events.csv     contacts+scores, shared-item bullets, events, retos)
        ▼
generate_prose(ReportModel, lang) ──► PROSE  (LLM, bounded JSON: exec_summary + per-contact
        │   fallback: deterministic prose          rationale[]; never numbers/order/structure)
        ▼
ReportModel + PROSE ──► render_html()  (chat)        ◄─ same inputs, identical content
                    └─► render_docx()  (download)
PROSE cached by (subject, weighting-signature, lang) so download reuses the on-screen prose.
```

## 5. Data Flow
1. `/api/report-tuned?id&weights&lang` (chat "generar reporte"): build model (weights) → generate prose
   → cache prose under the signature → `render_html` → return HTML. (Replaces the free-form LLM doc.)
2. `/api/report` (download): build the same model (same weights+lang) → look up cached prose (regenerate
   if absent) → `render_docx` → stream `.docx`. Identical to the chat render.
3. Numbers, ranking, contacts, shared-item detection: 100% deterministic from the matcher; the LLM only
   receives them as context and writes prose around them.

## 6. Fields surfaced (governance — Owner-approved)
- Professional: technologies, sectors, ámbitos, needs, role, municipality/province.
- Benign personal-affinity: shared hobbies, sports, languages, university (icebreaker angle for the
  rationale).
- EXCLUDED everywhere: children, gender, food_preferences (sensitive). patents/publications: out for now.

## 7. LLM prose contract (fixed slots, bounded)
- `exec_summary`: 2–3 sentences.
- `rationale[i]`: one short paragraph per contact — why this match works, weaving professional overlap +
  shared needs + location + benign affinity. No invented facts, no numbers, no reordering.
- Returned as STRICT JSON keyed by contact id → so a slow/garbled/oversized LLM response can't truncate
  or restructure the document; on any failure we drop to deterministic per-contact prose and still emit a
  COMPLETE report. (This kills the truncation bug structurally.)

## 8. Implementation Phases
- **P1 — Deterministic unification (no LLM):** report_engine reads the events matcher file; add
  `render_html`; add optional `weights` to `build_report` (reuse the app's `rerank_for_person`); chat
  "generar reporte" + download both render the same model. Fixes consistency, wrong-contacts (#14),
  wrong-numbers (#15), truncation — immediately. Prose = deterministic evidence bullets for now.
- **P2 — LLM prose slots:** add `generate_prose` (exec summary + per-contact rationale), the prose cache,
  and the deterministic fallback. Wire both renderers to include prose.
- **P3 — Tuned download:** `/api/report` accepts the weighting signature; verify chat==download under
  custom weights end-to-end.

## 9. Testing Strategy
- Golden: `render_html` text-content == `render_docx` text-content for the same (subject, weights, lang).
- Numbers: rendered scores/order == `rerank_for_person` output (asserts no LLM-typed numbers).
- Consistency: report contacts/order == chat `recommend_contacts` for a sample person.
- Privacy: no children/gender/food_preferences token appears in any rendered output.
- Robustness: with the LLM forced unavailable, the report still renders complete (no truncation/blank).
- i18n: Spanish render has no English weighting line and no mojibake.
- Inline-JS guard (esprima) still green for any chat-page changes.

## 10. Risks & Mitigations
- **LLM nondeterminism breaks chat==download** → prose generated once + cached; download reuses it;
  deterministic fallback. Render compares text-content in a test.
- **LLM latency/truncation** → bounded JSON slots + fallback; structure is never LLM-driven.
- **Matcher file column mismatch** (v1 vs v1.1_events) → verify columns in `contacts_for_person`; add a
  load-time check; test contact-order parity with the chat.
- **PII leak** → in-memory only, sensitive fields excluded by allowlist (render only known-safe fields),
  `.gitignore` already guards generated docs.
- **Scope creep** → Proyectos/branding stay out; phased so P1 alone already removes every current bug.

## Files Expected To Change
- `report_engine/` — `data_access.py` (matcher source), `report.py`/`sections.py` (model + weights +
  field allowlist + prose slots), new `render_html.py`, `render_docx.py` (prose slots).
- `backend_api/mvp_web_app.py` — `/api/report-tuned` returns unified HTML + primes cache; `/api/report`
  accepts weights+lang and reuses cache; retire/redirect `llm_report_for_person_weighted` free-form path;
  prose cache; localized weighting text.
- `tests/` — golden HTML==docx, numbers-from-math, consistency, privacy, robustness, i18n.
- Delta specs: `report-generation.md`, `agentic-conversation.md`.

## Rollback
Phased and additive. P1 can ship alone (deterministic, no LLM) and already fixes the bugs; P2/P3 layer on
top. Revert is per-phase: restore the old `/api/report-tuned` handler and the old report_engine source
path; no data migration. Feature is behind the existing report endpoints.

## Tier
FULL — architecture + member-facing deliverable + LLM in the path. Verifier subagent before done;
LaunchGuardian not required (no new external surface), but run it if the API shape changes materially.
