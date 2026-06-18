# Brief

## Change

unified-report

## User Need

Owner (and SECPHO staff about to collect member feedback) need ONE report they can trust:
what you see in the chat must be byte-for-byte the same as what you download, with real
matchmaking *reasoning* — not a data dump. Reports are going out for feedback, so report
credibility is the priority.

## Problem

There are two independent report generators that disagree:
- In chat ("generar reporte") → `llm_report_for_person_weighted`: the LLM writes the whole
  document free-form. Structure varies, it **retypes the scores** (already produced a wrong
  number — Francisco 0.21783 under custom weights = his default score), and it **truncates**
  when the model hits its output cap mid-document.
- Download `.docx` → `report_engine`: deterministic fixed structure, but reads a **different
  (older) matcher file** (`people_matches_v1.csv`) than the live app
  (`people_matches_v1_1_events.csv`), so the contacts/order differ from the chat.

Result: chat vs download differ in structure, contacts, and numbers; one truncates; and the
"matchmaking" is just a list of shared attributes with no explanation of *why* a match is good.

## Scope

In scope:

- One canonical **report model** (deterministic: structure, contacts, ranking, scores, shared-item
  detection) sourced from the SAME matcher file the live app uses (`people_matches_v1_1_events.csv`).
- Two renderers over that one model: **HTML** (chat preview) and **.docx** (download) — identical by
  construction.
- **LLM prose in fixed slots only**: a short executive summary + a per-contact "why this is a good
  match" paragraph. The LLM never types numbers, never reorders, never restructures.
- Prose generated **once** and reused for both renders (cache keyed by person+weighting+lang), so the
  download equals what's on screen.
- **Tuned weighting flows into the download** — what you see is what you download, including custom weights.
- Report surfaces professional overlap (tech, sector, needs, role, city) + benign personal-affinity
  (shared hobbies, sports, languages, university). EXCLUDES sensitive fields (children, gender,
  food_preferences) entirely.
- Absorbs tasks #14 (matcher source) and #15 (LLM must not type numbers).

Out of scope:

- Section 6 Proyectos (no data source yet), branded plantilla4.docx (owner to provide) — later phases.
- Company/socio report parity beyond what already exists (kept working; same model treatment).
- Changing the matcher math itself.

## Acceptance Criteria

- [ ] Chat report and downloaded `.docx` are identical in structure, contacts, order, scores, and prose
      for the same person + weighting + language.
- [ ] Every score/rank/contact in the report comes verbatim from the deterministic engine; a test
      asserts rendered scores == `rerank_for_person` output (no LLM-typed numbers).
- [ ] Report contacts/order match the chat's `recommend_contacts` for the same person (same matcher file).
- [ ] Each recommended contact has an LLM "why this is a good match" paragraph; a brief executive summary
      leads the report. If the LLM is unavailable/slow, deterministic fallback prose renders a COMPLETE
      report (never truncated, never blank).
- [ ] Tuning the weights and downloading reflects those exact weights and order.
- [ ] No sensitive fields (children, gender, food_preferences) appear anywhere in the output.
- [ ] Spanish report is fully Spanish (weighting line localized); no mojibake.

## Impact Areas

- Backend: report_engine gains an HTML renderer + prose slots + custom-weighting input; the in-chat
  report path switches to render the unified model; a short-lived prose cache.
- Frontend: "generar reporte" renders the unified HTML; the download button reuses the same generated report.
- Data model: none (read-only; new matcher-file source for report_engine).
- API: `/api/report` accepts optional weighting + lang; `/api/report-tuned` returns the unified HTML and
  primes the cache. (Backward-compatible defaults.)
- AI/model behavior: LLM constrained to bounded prose slots (exec summary + per-contact rationale); never
  numbers/order/structure; deterministic fallback.
- Documentation: report-generation + agentic-conversation delta specs.
- Operations/security: member PII still generated in memory, never written to disk, never committed;
  sensitive fields explicitly excluded; prose cache is in-memory and short-lived.

## Open Questions

- Prose cache key + TTL (proposed: `(member_id|socio, weighting signature, lang)`, small LRU, minutes-long).
- Whether company/socio reports also get per-member rationale now or in a follow-up (proposed: same
  treatment, but verify scope during build).
