# Decision Log

## Change

live-activities-tool (P3 activities slice)

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-20 | Synthetic `activity_id` = content hash (sha1 of socio|date|type|author|description) | actividades has no stable id, but the change-feed needs a key; an opaque hash is a key, not data | Composite natural key (rejected: not unique enough); no change-detection for this source (rejected) |
| 2026-06-20 | Treat actividades as 🟡 (staff-queryable), not 🔴 | It's internal engagement/CRM notes, not financials or PII (emails/NIF); staff-appropriate | Gate behind the access model (deferred: revisit in P4 if descriptions prove sensitive) |
| 2026-06-20 | Most-recent-first with `dayfirst=True, errors="coerce"` | Robust to date-format variance without crashing; recency is what "what's X been up to" needs | Fixed `%d/%m/%Y` (rejected: brittle if a row varies) |
| 2026-06-20 | Mirror `list_retos`/`list_projects` (deterministic filter over the in-memory table) | Consistency; math decides, the LLM explains; empty when live is off | — |
