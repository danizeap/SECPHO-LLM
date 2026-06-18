# Decision Log

## Change

report-generation

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-17 | Deterministic-first report engine; the LLM is never in the structural path | Eli requires "siempre el mismo formato"; matches our "math decides, the LLM explains" principle | LLM-generated documents (rejected: non-deterministic format) |
| 2026-06-17 | Reuse our normalized CSVs + the matchmaker (`people_matches_v1`) for Section 3 | The matchmaker is the unique value and is already deterministic; the IVO left this slot empty | Re-run matching inside the report (rejected: duplicates logic) |
| 2026-06-17 | Reto recommendations via TF-IDF + sector overlap, not sentence-transformers | Reuses the existing scikit-learn stack; avoids a heavy torch/embeddings dependency | sentence-transformers like the IVO (rejected: large dependency) |
| 2026-06-17 | Neutral programmatic styling, isolated in `render_docx` | Branding is blocked on `plantilla4.docx`; isolating the renderer makes the template swap trivial | Block the whole change on the template (rejected: nothing else needs it) |
| 2026-06-18 | Attendance dates come from the events table, not the registration filename | Production review proved the filename date is the export timestamp (always Apr 2025), not the event date — fabricated dates | Use the filename date (rejected: fabricates data); drop attendance entirely (rejected: loses real value) |
| 2026-06-18 | Reto entity matching by whole-token (parenthetical qualifiers stripped), not substring | Substring matching fabricated participation ("Roca" matched "ProCareLight") | Naive `str.contains` (rejected: invents data); strict exact-equality (rejected: drops legitimate variants like "Repsol S.A.") |
| 2026-06-18 | Canonicalize tech/sector vocabulary (accent-strip, `&`→`y`, alias map) before overlap | Member vs event spellings diverge ("Robótica & Drones" vs "y Drones"; "Farmaceutico" vs "Farmacéutico"), silently zeroing scores | Pre-normalize the source CSVs (deferred: normalizing at read time is contained) |
| 2026-06-18 | Don't surface online events with zero topical overlap; show the real city in location | Review found the flat online bonus produced "22% de afinidad" with no real match | Keep online-only recommendations (rejected: misleading) |
