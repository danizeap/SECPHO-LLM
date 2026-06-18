# Brief

## Change

report-download

## User Need

SECPHO staff need to download the branded `.docx` report from the live web app so they can
start giving feedback on real documents. The report engine exists (`report-generation`,
archived) but is CLI-only; nothing in the deployed app exposes it.

## Problem

`report_engine` is a standalone package/CLI. The web app has no endpoint or button to
generate and download a report, so staff cannot self-serve from the live app.

## Scope

In scope:

- A `POST /api/report` endpoint (auth-gated, rate-limited) that streams a `.docx` for a
  person (`id`) or socio (`socio`), generated in memory — no PII written to the server disk.
- A download affordance in the chat: a "Descargar .docx" button in the weighting tuner
  (person) and inline `[report:ID]` / `[report-socio:NAME]` tokens rendered as download buttons.
- `report_engine.generate_bytes()` (in-memory generation + a safe ASCII filename).

Out of scope:

- Branding (still needs `plantilla4.docx`), Section 6, PDF export, LLM prose polish.

## Acceptance Criteria

- [ ] Authenticated staff can download a person and a company `.docx` from the app.
- [ ] Unauthenticated → 401; bad input → 400; not found → 404; rate-limited → 429.
- [ ] The report is generated in memory and never written to the server disk.
- [ ] No PII report committed; no XSS via the socio-name token.

## Impact Areas

- Backend: new `POST /api/report`; `report_engine.generate_bytes`; a `report` rate bucket
- Frontend: download button + token-rendered download buttons + `downloadReport` JS
- Data model: none
- API: new `POST /api/report` (additive, behind the existing auth gate)
- AI/model behavior: agent emits `[report:ID]` / `[report-socio:NAME]` tokens to offer downloads
- Documentation: `report-generation` delta spec (download capability)
- Operations/security: PII deliverable behind staff auth (same posture as the on-screen report); sharpens the open Gate 14 (GDPR) for any broader exposure

## Open Questions

- None blocking; company-download relies on the agent emitting the socio token.
