# Decision Log

## Change

data-sync-pipeline

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-20 | Persist NOTHING confidential — zero-copy live layer over SECPHO's WP API | Owner (TFM, may leave) must not become custodian of SECPHO's financial/PII data; WordPress already is the custodian | Postgres/Supabase store (rejected: creates a data-governance burden to own/hand off); Render PG; files of their data |
| 2026-06-20 | Replace static CSV load with a live in-memory pull, refreshed on a tiered cadence | Directly fixes the original "frozen snapshot" problem; always current; no stored copy to keep in sync | A sync-loop + database with change-detection (rejected: reintroduces a store + custody) |
| 2026-06-20 | Change-feed via in-RAM diff between refresh cycles (not a persisted diff store) | Recovers proactive change-alerts with zero persistence while the app runs | Persist content-hashes for cross-restart memory (deferred: still a small store; revisit only if alerts must survive restarts) |
| 2026-06-20 | Long-term history comes from the source's own timestamps + optional digest pushed to SECPHO | Most trends are already dated in the data; true longitudinal memory accumulates on THEIR side, not ours | We store history (rejected: custody) |
| 2026-06-20 | Full-pull + in-RAM diff (no conditional requests) | Confirmed the endpoints send no ETag/Last-Modified; data volume is small (≤6k rows) so full pulls are cheap | 304 conditional GETs (not supported by the plugin) |
| 2026-06-20 | Financial/PII (🔴) sources are admin-only in the chat | Putting the company's books behind a staff-wide chatbot is unacceptable; role-gating is mandatory | All-staff access (rejected) |
| 2026-06-20 | Resilience via stale-while-revalidate in RAM + keep-warm + progressive/parallel load | The app inherits WP's uptime/speed; SWR serves last-good, keep-warm avoids cold-start re-pulls | Persistent cache for resilience (rejected: custody); accept slow/empty cold starts (rejected: bad UX) |
| 2026-06-20 | Posture: we are a processor, not a controller; RAM-transit is the irreducible minimum | To reason over data the app must see it transiently; nothing is written down we control; zero-RAM only via running in SECPHO's infra (a production handoff) | — |
