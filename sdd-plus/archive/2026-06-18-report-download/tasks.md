# Tasks

## Change

report-download

## Implementation

- [x] `report_engine.generate_bytes` (in-memory `.docx` + ASCII filename); exported from `__init__`.
- [x] `POST /api/report` (auth-gated, rate-limited "report" bucket, in-memory, streamed, error paths).
- [x] Make `report_engine` importable from the app (`sys.path` += repo root).
- [x] UI: download button in the tuner + `downloadReport` JS + `[report:ID]` / `[report-socio:NAME]`
      tokens (socio carried in an escaped `data-` attribute — no XSS).
- [x] Agent emits `[report:ID]` (person) and offers `[report-socio:NAME]` (socio).
- [x] Tests: `generate_bytes` valid-docx regression (15 total passing); live end-to-end endpoint test.
- [x] Verify: `sdd.py verify`; verifier subagent → VERIFIED; added 3 `/api/report` integration
      tests (auth gate 401, authenticated download, bad-type 400) — 18 tests total.
