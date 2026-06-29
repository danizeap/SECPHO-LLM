# Tasks

## Change

collaboration-network (P5, slice 3). Full design in [blueprint.md](blueprint.md).
Owner decision: textual/structured surfacing for v1; gate `data.socios`; edges from projects + retos.

## Implementation

- [x] **P5n-a — graph + tools** (gate `data.socios`). `_split_entities` (comma/pipe split with
      legal-form rejoin so "Lasercare, SL" stays whole), `_build_network` (weighted co-participation
      from `proyectos.partners` + reto participants, cached on frame identity), and 3 tools:
      `socio_network`, `network_overview`, `connection_between`. Gated + schemas + dispatch. Tests:
      `tests/test_collaboration_network.py` (5). Suite 144. Live proof: 208 socios / 1413 connections;
      hubs Eurecat (77)/CEIT/HAMAMATSU/Leitat/Tekniker; no spurious legal-form nodes.
- [x] **P5n-b — close-out.** verify → verifier subagent (PASS) → adversarial security review (3
      dimensions → 2 findings FIXED: cross-grant reto/project label leak in `connection_between`, and
      `_net_find` determinism) → LaunchGuardian (0 findings; semgrep-Windows aside) → spec sync →
      archive + commit. Suite 147.

## Delta specs

- [x] Synced into living capabilities: `specs/agentic-conversation.md` (the 3 network tools) +
      `specs/access-control.md` (`data.socios` gates them).

## Verification

- [x] `python scripts/sdd.py verify collaboration-network` ✓; full evidence in `verification.md`
      (147 tests, verifier PASS, adversarial review 2 findings fixed).
