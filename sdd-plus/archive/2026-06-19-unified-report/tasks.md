# Tasks

## Change

unified-report

## Implementation

- [x] Confirm scope + Owner decisions (LLM prose in both, tuned download matches, flagship for prose, benign affinity in / sensitive out, paragraph-per-contact + exec summary).
- [x] P1: one report model + shared `layout.blocks`; `render_docx` rewritten on it; new `render_html`.
- [x] P1: matcher source switched to `people_matches_v1_1_events.csv` (report == chat).
- [x] P1: affinity evidence (hobbies/sports/languages/university); sensitive fields excluded by allowlist.
- [x] P1/P3: weights flow into both endpoints; tuned download matches the preview.
- [x] P2: flagship prose (`exec_summary` + per-contact `rationale`), strict-JSON, deterministic fallback.
- [x] P2: prose cache keyed (kind, ident, weighting, lang) so preview and download reuse the same prose.
- [x] Removed the free-form WEIGHTED report functions that fed the tuned report (weighting_text,
      report_for_person_weighted, llm_payload_for_person_weighted, llm_report_for_person_weighted).
      Note (verifier): a separate non-weighted `llm_report_for_person` / `/api/llm-report` briefing
      still exists, used only by the INDEX_HTML demo page — out of scope here; see follow-up to retire it.
- [x] Tests: html==docx (person/company/with-prose), injected-order honored, privacy allowlist, tuned download, report-tuned HTML; suite green (33).
- [x] Docs/specs: report-generation delta spec.
- [x] Verification: AST + escape clean, esprima JS clean, full suite, LIVE flagship end-to-end (prose + chat==download via cache).
- [ ] Owner live browser test on the deploy (cannot run here): generate a tuned report, confirm it reads well and the download matches.
