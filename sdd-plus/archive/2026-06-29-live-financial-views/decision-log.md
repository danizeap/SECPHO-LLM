# Decision Log

## Change

live-financial-views

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-29 | Schema-only probe (field names + masked amount formats, no values) to map normalizers exactly. | The 🔴 sources were never pulled offline; the Owner's production-ready standard forbids guessed field mappings. Keeps real financial values out of the session. | Guess Spanish field names (rejected — silent wrong mapping); pull full values (rejected — needless exposure). |
| 2026-06-29 | Use `facturacion-total` (4779-row ledger, has Socio/Estado/Vencimiento/Total) as the invoice source; skip `facturas-sistema`. | Richer + has per-socio status/dates for cuota_status + list_invoices; `facturas-sistema` lacks status and uses `Cliente` not `Socio`. | `facturas-sistema` (rejected — thinner); both (rejected — duplication). |
| 2026-06-29 | Invoice status from the `Estado` field (Pagada/Vencida/Enviada/Cancelada); outstanding = Vencida+Enviada, excludes Cancelada. | Authoritative status vocabulary confirmed via a semantics probe; matches reality (overdue count = 42 = Estado=Vencida). | Date-only derivation (rejected — vocabulary is authoritative and clearer). |
| 2026-06-29 | `Fecha de baja definitiva = "No consta"` means ACTIVE, not a leave; status keys on a real date. | Live proof exposed all 318 cuotas as "left" under the naive non-empty check; the source uses "No consta" as the not-recorded placeholder. 140 active / 178 left after the fix. | Non-empty = left (rejected — wrong; the bug the live proof caught). |
| 2026-06-29 | Deterministic euro math (`_parse_eur` handles Spanish `1.234,56 €`, plain `7500000`, negatives, `No definido`); LLM quotes figures verbatim, never computes them. | "Math decides, the LLM explains" — no hallucinated finances; same discipline as the report. | LLM-computed figures (rejected — hallucination risk). |
| 2026-06-29 | Gate all 4 financial tools behind `data.financiero` (fail-closed); financial stays out of the report and the heuristic fallback. | The whole point of the slice is safe exposure; P4's fail-closed machinery enforces it. | Open to all chat users (rejected — sensitive). |
| 2026-06-29 | Zero-copy holds: financial data only ever in RAM, never persisted. | Owner's TFM/non-custodian constraint. | A financial datastore (rejected). |
