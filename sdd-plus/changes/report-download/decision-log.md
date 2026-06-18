# Decision Log

## Change

report-download

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-18 | Generate the report in memory (`BytesIO`) and stream it; never write to the server disk | Reports contain member PII and the server disk is ephemeral — PII should not be persisted there | Write to a temp file then stream (rejected: PII on disk) |
| 2026-06-18 | `POST /api/report` (not GET) behind the existing `/api` auth gate + a dedicated `report` rate bucket | Avoids PII identifiers in URLs/caches, reuses the automatic auth gate, and bounds a CPU-heavier operation | GET with query params (rejected: ids/names in the URL + cacheable) |
| 2026-06-18 | Carry the socio name in an escaped `data-socio` attribute, not in `onclick` | A socio name with quotes/markup interpolated into an event handler would be an XSS vector | Inline the name in `onclick` (rejected: XSS); numeric-only tokens (rejected: socios have no numeric id in the UI) |
| 2026-06-18 | Offer downloads via `[report:ID]` / `[report-socio:NAME]` tokens + a tuner button | Reuses the existing token/button pattern; person download is guaranteed via the tuner, company via the agent token | A separate report page/form (deferred: heavier; tokens fit the conversational UI) |
