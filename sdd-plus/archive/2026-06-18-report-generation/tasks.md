# Tasks

## Change

report-generation

## Implementation

- [x] Build Blueprint (architect) approved; production posture (Sections 1–5).
- [x] `report_engine` package: data_access, scoring, sections, render_docx, report, CLI.
- [x] Section 3 contacts from the matchmaker with clean, consistently-cased evidence.
- [x] Section 4 events: recommendations (day-first dates) + attended history (dates from
      registration filenames) — IVO date bug fixed.
- [x] Section 5 retos: recommended (TF-IDF + sector) + emitted + applied.
- [x] Compound-ámbito tokenization fix; encoding/accents verified.
- [x] Golden/behaviour tests (tests/test_report_engine.py) — 10 passing.
- [x] `python-docx` pinned in requirements.txt.
- [x] Production-readiness review (multi-agent, 25 agents): 21 confirmed findings; all 16 code
      issues fixed (incl. 2 critical data-fabrication bugs — export-timestamp dates and
      substring entity matching) + 4 regression tests; 1 data-freshness item flagged to owner.
- [x] `sdd.py verify` + verifier subagent (PASS WITH FOLLOW-UP; the two doc-only follow-ups —
      stale test count and a delta-spec line that still described the pre-fix behavior — fixed).
