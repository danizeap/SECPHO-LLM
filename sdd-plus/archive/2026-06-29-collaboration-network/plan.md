# Plan

## Change

collaboration-network (P5, slice 3). Full design in [blueprint.md](blueprint.md).

## Approach

- **P5n-a** — `_split_entities` (delimiter split + legal-form rejoin), `_build_network` (weighted
  co-participation graph from `proyectos.partners` + reto participants, cached on frame identity),
  and 3 tools `socio_network` / `network_overview` / `connection_between`, gated `data.socios`. DONE.
- **P5n-b** — close-out: verify → verifier → adversarial security review → LaunchGuardian → spec sync
  → archive + commit.

## Files Expected To Change

- `backend_api/mvp_web_app.py` — `_split_entities`, `_build_network`, `_net_add`, `_net_find`, the 3
  tools, `TOOL_REQUIRED_GRANT` (data.socios), `AGENT_TOOL_SCHEMAS`, dispatch handlers.
- `tests/test_collaboration_network.py` — NEW hermetic coverage.
- `sdd-plus/specs/capabilities/{agentic-conversation,access-control}.md` — synced at close-out.

## Risks

- Cross-source socio-name inconsistency (e.g. "AIMEN" vs "AIMEN Centro Tecnológico") → v1 matches
  as-recorded; legal-form suffixes rejoined to avoid spurious nodes. Normalization is a future pass.
- Hallucinated metrics → degrees/weights deterministic; the no-derive agent rule applies.
- Performance → small graph (~150 projects, ~180 retos), cached on frame identity; trivial.

## Rollback

Additive: with the live layer off, the frames are empty and the tools return empty/unavailable.
Reverting the commit removes the tools; nothing persisted, nothing to undo. `data.socios` is in the
default grant set, so the network is visible to ordinary staff by design (non-sensitive).
