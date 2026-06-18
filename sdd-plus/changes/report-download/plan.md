# Plan

## Change

report-download

## Approach

1. `report_engine`: add `generate_bytes(kind, ident) -> (bytes, filename)` (build report → render
   → BytesIO; never touches disk) + a slugified ASCII filename. Export from `__init__`.
2. `mvp_web_app.py`: make `report_engine` importable (`sys.path` += repo-root `BASE_DIR`) via a
   lazy loader; add `RATE_LIMITS["report"] = (20, 60)`.
3. `POST /api/report` (in `_do_POST`, after the `/api/*` auth gate): rate-limit `report`; parse
   `{type, id|socio}`; validate; `report_engine.generate_bytes`; stream the `.docx`
   (`Content-Type` docx, `Content-Disposition: attachment`, security headers). `ValueError` → 404;
   other → 500.
4. UI: `downloadReport(kind, key)` (POST → blob → `<a download>`); `downloadReportSocio(btn)`
   reading a safe `data-socio` attribute; "Descargar .docx" button in the tuner;
   `[report:ID]` / `[report-socio:NAME]` token rendering (socio via an `html.escape`'d data
   attribute, never interpolated into `onclick` → no XSS).
5. Agent: `recommend_contacts` returns a `report_token`; `AGENT_INSTRUCTIONS` + the heuristic
   router append `[report:ID]`; the agent offers `[report-socio:NAME]` for socios. i18n label.

## Files Expected To Change

- `report_engine/report.py`, `report_engine/__init__.py`
- `backend_api/mvp_web_app.py`
- `sdd-plus/changes/report-download/specs/report-generation.md` (delta)

## Risks

- PII: the report is streamed to authenticated staff only, generated in memory, never persisted
  to disk, and never committed — same posture as the existing on-screen report.
- XSS: the socio-name token MUST be escaped into a data attribute, not interpolated into `onclick`.
- Import path: `report_engine` must be importable from the app (`sys.path` += repo root).

## Rollback

Remove the `/api/report` handler + the UI button/tokens; revert the `report_engine.__init__`
export. Additive; no data/schema change.
