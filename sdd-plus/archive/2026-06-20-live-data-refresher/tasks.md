# Tasks

## Change

live-data-refresher (P2)

## Implementation

- [x] `diff_frames` + `_row_hash` + per-source `KEY_COLUMNS`; in-RAM `_LAST` + bounded `_CHANGES`.
- [x] `_refresh_once` (load → diff → emit → apply; SWR on failure) + cadence (`_due`, intervals).
- [x] `start_refresher` (immediate load then tick loop) + `changes()`.
- [x] Wire `mvp_web_app._start_live_refresh` to the refresher (DATA apply, CSV fallback, off by default).
- [x] Tests: diff add/modify/remove; baseline→change cycle; SWR-on-failure (hermetic).
- [x] Live proof: refresher runs against the real API; baseline + stable re-pull = 0 changes (no false positives).
- [x] Capability delta (refresher + change-feed) + verify + verifier + sync + archive.
- [ ] Owner: when going live, set up a keep-warm ping on `/health` (external uptime service) so the
      in-RAM change-memory stays continuous.
