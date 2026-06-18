# Plan

## Change

report-generation

## Approach

Deterministic-first `report_engine/` package (full architecture in `blueprint.md`):

1. `data_access.py` — load members/socios/matches/events/registrations/retos; robust text
   and date normalization: pipe-split for member data; comma-aware, compound-preserving
   split for event/reto data; day-first event/reto dates; attendance dates extracted from
   the registration filenames.
2. `scoring.py` — deterministic event scoring (IVO weights ported) + reto scoring (TF-IDF
   over the existing scikit-learn stack + sector overlap). No embeddings dependency.
3. `sections.py` — display-ready builders per section; contact evidence recomputed cleanly
   from members (shared parent tech/sectors/ámbitos); Spanish dates.
4. `render_docx.py` — neutral programmatic styles, isolated so `plantilla4.docx` swaps in later.
5. `report.py` / `__main__.py` — assemble person/company reports; CLI.

## Files Expected To Change

- `report_engine/*` (new package), `tests/test_report_engine.py` (new), `requirements.txt` (+python-docx)
- `sdd-plus/changes/report-generation/{blueprint.md, specs/report-generation.md}`

## Risks

- Data freshness: reads CSV snapshots; the current snapshot has few future events and zero
  active retos (honestly reflected in the output). Live refresh is a later concern.
- Date/tokenization quirks (handled): day-first dates, comma-containing ámbitos.
- PII: reports embed member data → never committed; redact before any future LLM polish.

## Rollback

`report_engine/` is additive and not wired into the deployed app. Deleting the package (and
the `python-docx` pin) fully reverts it with no effect on the live service.
