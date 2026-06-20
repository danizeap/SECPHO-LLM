# Tasks

## Change

data-sync-pipeline — delivers the Build Blueprint + Phase 1 (the live layer foundation). Later
phases (refresher, all sources + tools, RAG, access model, intelligence) are follow-on changes.

## Implementation

- [x] Build Blueprint written + Owner-approved ("ok lets go").
- [x] Live schema scan of the 17 endpoints (schema only; no values persisted).
- [x] `backend_api/live_data.py`: env-gated fetch, parallel best-effort load, freshness, and
      normalizers for retos / proyectos / casos-éxito (retos → canonical schema).
- [x] Wire into the app: new `proyectos`/`casos_exito` DATA keys + non-blocking background live
      refresh that swaps live data into DATA, with CSV fallback (no token → inert, no network).
- [x] Hermetic tests (`tests/test_live_data.py`): normalizers, disabled-no-network, failure isolation,
      freshness — fixtures use real field shapes with fake values.
- [x] Live end-to-end proof against the real API (retos 179 / proyectos 152 / casos 59; canonical
      schema; freshness stamped; nothing persisted).
- [x] Capability spec: live-data-platform (zero-copy posture, live pull, best-effort fallback).
- [x] Verification: AST/escape clean, full suite 40 passed.
- [ ] Owner: set `SECPHO_LIVE_DATA=1` in the Render env to flip the deploy to live (the token is
      already configured as `SECPHO_API_AUTH_TOKEN`; until the flag is on it serves the CSV snapshot).
      Token stays env-only; rotate it (their WP guy).
- [ ] Follow-on changes: P2 refresher + change-feed + keep-warm; P3 all 17 sources + LLM tools + RAG;
      P4 access model; P5 intelligence layer + eval set.
