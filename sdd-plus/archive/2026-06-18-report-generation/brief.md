# Brief

## Change

report-generation

## User Need

SECPHO staff hand socios a "Informe de Valor y Oportunidades" — a branded, member-ready
report. They want it automated and consistent, with our deterministic matchmaker filling
the "Contactos Recomendados" section their existing (IVO) generator left empty.

## Problem

The matchmaker only lived in the chat; there was no way to produce the deliverable
document. The IVO generator also had event/attendance bugs (past-event recommendations,
"Fecha desconocida", miscounted attendance) and no contacts section.

## Scope

In scope (this change — production quality, Sections 1–5):

- A `report_engine/` package producing a deterministic `.docx` for a person or socio.
- Section 1 Introducción, 2 Resumen/Ficha, 3 Contactos (our matchmaker), 4 Eventos
  (recommended + attended, real dates), 5 Retos (recommended + emitted + applied).
- CLI + golden/behaviour tests. Deterministic-first; no LLM in the structural path.

Out of scope (named asset blockers / later phases, NOT shortcuts):

- Section 6 Proyectos — needs the projects data source.
- Exact SECPHO branding — needs `plantilla4.docx` (neutral styling until then).
- `/api/report` endpoint + UI button + LLM prose polish + PDF + batch/scheduled delivery.

## Acceptance Criteria

- [x] Deterministic `.docx` for person and socio; same input → identical document.
- [x] Contacts come only from `people_matches_v1`, order unchanged, with clean evidence.
- [x] Events/retos use correctly-parsed dates; attendance dates from registration filenames
      (IVO "Fecha desconocida" bug fixed).
- [x] Correct accents (no mojibake); compound ámbitos preserved.
- [x] Golden/behaviour tests pass; production-readiness review clean.

## Impact Areas

- Backend: new `report_engine/` package (no change to the deployed web app)
- Frontend: none (UI integration is a later phase)
- Data model: none (reads existing normalized CSVs)
- API: none yet (`/api/report` is a later phase)
- AI/model behavior: none in the structural path; LLM prose polish is a later phase
- Documentation: `blueprint.md` + `report-generation` delta spec
- Operations/security: new dependency `python-docx`; generated reports carry member PII and are NOT committed

## Open Questions

- `plantilla4.docx` (branding) and the projects data — requested from the owner.
- Confirm `.docx`-first is sufficient (PDF later?).
