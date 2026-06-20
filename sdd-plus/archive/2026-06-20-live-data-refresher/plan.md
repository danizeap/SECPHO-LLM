# Plan

## Change

live-data-refresher (P2)

## Approach

1. `live_data.py`: add `_row_hash`, `diff_frames(old, new, key)`, per-source `KEY_COLUMNS`, an in-RAM
   `_LAST` (previous pull) + bounded `_CHANGES` deque, `_refresh_once(names, apply_fn)` (load → diff vs
   previous → emit change → apply), `_due`/`REFRESH_INTERVALS`/`DEFAULT_REFRESH_SECONDS` for cadence,
   `start_refresher(apply_fn)` (immediate load then tick loop), and `changes(limit)`.
2. `mvp_web_app.py`: replace the one-shot `_start_live_refresh` body with `start_refresher`, applying
   loaded frames into `DATA` (CSV fallback / SWR retained).
3. Keep-warm: documented as an external uptime ping on the existing `/health` (ops, not code).

## Files Expected To Change

- `backend_api/live_data.py`, `backend_api/mvp_web_app.py`, `tests/test_live_data.py`, capability delta.

## Risks

- A failed pull wiping data → mitigated: `_refresh_once` only applies on success (SWR); test covers it.
- False-positive churn → mitigated: content-hash diff; live proof shows a stable re-pull emits nothing.
- Render sleep pausing the refresher/change-memory → keep-warm ping (ops); honestly out of code's reach.
- Change-feed leaking sensitive values for 🔴 sources → N/A in P2 (3 safe sources); P3/P4 must gate it.

## Rollback

Revert the `live_data.py`/`mvp_web_app.py` hunks; the refresher is off unless `SECPHO_LIVE_DATA` is set.
No data/migration (nothing persisted).
