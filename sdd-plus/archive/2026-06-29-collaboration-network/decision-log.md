# Decision Log

## Change

collaboration-network

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-29 | Textual/structured surfacing for v1 (tools return ranked data, LLM narrates); a rendered visual is a follow-on. | Owner decision. Fits the chat, fully deterministic, ships fast, answers every workflow; the same deterministic graph is exactly what a future visual would render. | Build the in-app visual now (rejected for v1 — bigger render-path lift; data answers the questions without it). |
| 2026-06-29 | Edges from shared projects (`proyectos.partners`) + retos (applying/issuing/beneficiary); NOT event co-attendance in v1. | Projects + retos are explicit collaboration and rich (62/152 projects ≥2 partners, 70/179 retos ≥2 applicants). Event co-attendance links many socios at once (noisy). | Include events (rejected v1 — noisy); projects only (rejected — retos add real edges). |
| 2026-06-29 | Split participant fields on comma/pipe/semicolon but RE-JOIN bare legal-form suffixes ("SL", "S.L.", "S.A."…) to the preceding name. | Real data is comma-delimited and contains "Lasercare, SL" / ", S.L." — a naive split would shatter names into spurious nodes connected to everyone. Live proof: no spurious legal-form nodes among the hubs. | Split on pipe/semicolon only (rejected — misses comma-delimited retos); split on comma naively (rejected — spurious "SL" nodes). |
| 2026-06-29 | Gate the network tools `data.socios`; deterministic degree/weighted-degree only. | Collaboration structure is non-sensitive member-relationship data (no euros/PII/candid reasons); degree metrics are deterministic and the LLM only narrates. | A financial/admin gate (rejected — not sensitive); heavy centrality/betweenness (rejected — overkill for v1). |
