# Verification

## Change

data-sync-pipeline (Blueprint + Phase 1)

## Automated Checks

- [x] `ast.parse` + `-W error::DeprecationWarning` on `mvp_web_app.py` and `live_data.py` → clean.
- [x] Full suite: `python -m pytest tests/` → 40 passed (was 35; +5 live-data tests; no regression).
- [x] `tests/test_live_data.py` (hermetic, no network): retos normalizer == canonical schema (dates
      preserved, HTML stripped); proyectos/casos normalizers; casos repr-string lists/dicts parsed;
      live disabled (no token) → no request; one source failing → others load, failed absent, freshness stamped.
- [x] No-token default makes the whole suite hermetic (the background refresh is inert without the env token).

## Manual Checks

- [x] LIVE end-to-end against the real API (token set transiently, nothing committed):
      `live_data.load_all([...])` → retos 179 / proyectos 152 / casos-éxito 59 rows, retos columns
      exactly the canonical schema, freshness timestamps recorded, all in memory.
- [ ] OWNER: set `SECPHO_LIVE_DATA=1` in Render to flip the deploy to live (token already configured
      as `SECPHO_API_AUTH_TOKEN`; CSV until the flag is on); confirm proyectos/casos appear and retos is
      current. Rotate the token (WP guy).

## Documentation Updates

- [x] New capability spec: live-data-platform (zero-copy posture + live pull + best-effort fallback).
- [ ] PROJECT_CONTEXT to note the zero-copy posture (fold into the spec sync / a follow-up).

## Result

PASS (static + hermetic suite + live end-to-end proof). Phase 1 establishes the zero-copy live layer
and proves "live, not snapshot" on three sources; persists nothing. Remaining phases are follow-on
changes. One open item: Owner sets the token in Render to enable live on the deploy.
