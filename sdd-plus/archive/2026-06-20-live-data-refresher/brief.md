# Brief

## Change

live-data-refresher (data pipeline P2)

## User Need

P1 pulled the live data once at startup. To stay current we need it to refresh on a cadence, and to
recover the "change-alert" capability we gave up by not owning a database — without persisting anything.

## Problem

A one-shot load goes stale; and with no stored history we have no "before" to detect changes against.

## Scope

In scope (P2):
- Background refresher: immediate first load, then periodic per-source re-pulls; stale-while-revalidate
  in RAM (a failed pull keeps the last-good view).
- In-RAM change-feed: diff each new pull against the previous in-memory pull (by record key + content
  hash) → bounded change list; baseline emits nothing; a stable re-pull emits nothing (no false positives).
- Keep-warm: documented ops step (external uptime ping on the existing public `/health`) so the in-RAM
  change-memory stays continuous — not code (Render's HTTP-idle sleep can't be beaten from inside the process).

Out of scope:
- Surfacing the change-feed as user-facing alerts (P5).
- The remaining sources / tools / RAG (P3); the access model (P4); persistence of any kind.

## Acceptance Criteria

- [x] Refresher re-pulls on a per-source cadence, non-blocking, persists nothing; failed pull keeps last-good.
- [x] Change-feed: baseline silent, real add/modify/remove detected, stable re-pull silent.
- [x] Hermetic tests + a live proof (no false positives on a stable re-pull).
- [x] Off by default (the flag/token gate from P1); full suite green.

## Impact Areas

- Backend: `live_data.py` refresher + diff + change-feed; `mvp_web_app.py` swaps the one-shot load for the refresher.
- Frontend / API / data model: none (in-memory only).
- AI/model behavior: none yet (the change-feed feeds P5 alerts).
- Documentation: live-data-platform capability delta (refresher + change-feed).
- Operations/security: keep-warm ops note; still zero persistence; token still env-only.

## Open Questions

- Keep-warm pinger choice (UptimeRobot / Render cron / GitHub Action) — Owner's pick when going live.
