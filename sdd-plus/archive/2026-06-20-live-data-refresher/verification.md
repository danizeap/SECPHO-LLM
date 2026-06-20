# Verification

## Change

live-data-refresher (P2)

## Automated Checks

- [x] `ast.parse` + `-W error::DeprecationWarning` on `mvp_web_app.py` and `live_data.py` → clean.
- [x] Full suite: 43 passed (40 + 3 P2), hermetic (slowest 0.37s; no network).
- [x] `tests/test_live_data.py` P2: `diff_frames` detects add/modify/remove by key+hash; refresh cycle
      baseline emits nothing then a re-pull with one new record records exactly one "added" on the feed;
      a failed re-pull emits nothing AND leaves the last-good view untouched (SWR).
- [x] Still off by default (P1 flag/token gate) → no test touches the network.

## Manual Checks

- [x] LIVE proof against the real API (token from `.env`, flag set): refresher loads retos 179 /
      proyectos 152 / casos 59; baseline cycle = 0 changes; an immediate stable re-pull = 0 changes
      (no false positives); freshness recorded. Persists nothing.
- [ ] OWNER: when going live, add a keep-warm ping on `/health` (UptimeRobot / Render cron / GitHub
      Action) so the in-RAM change-memory stays continuous across Render's HTTP-idle sleep.

## Documentation Updates

- [x] Capability delta synced into live-data-platform (refresher + change-feed requirements).
- [x] README / project context: no change needed.

## Result

PASS (static + hermetic suite + live no-false-positive proof). The in-RAM change-feed recovers the
change-alert capability with zero persistence. Keep-warm is an Owner ops step when enabling live.
