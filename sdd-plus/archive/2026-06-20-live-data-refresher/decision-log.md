# Decision Log

## Change

live-data-refresher (P2)

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-20 | The change-feed is the in-RAM diff between successive pulls (no persisted snapshots) | Recovers proactive change-alerts while honoring the zero-copy posture; works continuously while the app runs | Persist content-hashes for cross-restart memory (deferred: still a store + custody) |
| 2026-06-20 | Diff by record key + content hash; baseline pull emits nothing | Stable change detection without timestamps; first pull is the reference, not a flood of "added" | Diff by modified-timestamp only (rejected: most sources lack one) |
| 2026-06-20 | Stale-while-revalidate: apply to DATA only on a successful pull | A failed re-pull (their API down) must not wipe the working view | Clear on failure (rejected: outage = empty app) |
| 2026-06-20 | Per-source cadence (default hours), tick-checked | Tiered-capable for when P3 adds 17 sources of differing volatility; cheap for low-volatility reference data | One global interval (kept the map so it's tiered-ready) |
| 2026-06-20 | Keep-warm is an Owner ops step (external ping on /health), not code | Render's HTTP-idle sleep can't be prevented from inside the process; an external pinger keeps it warm | Self-ping/background-thread keepalive (rejected: doesn't stop HTTP-idle sleep) |
