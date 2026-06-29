# Verification

## Change

collaboration-network (P5, slice 3)

## Automated Checks

- [x] Full suite green: `python -m pytest -q` → **147 passed**. New: `tests/test_collaboration_network.py`
      (8: edge/weight construction, legal-form rejoin, ranking, gating, label-withholding,
      deterministic resolver).
- [x] `python scripts/sdd.py verify collaboration-network` → artifacts verified.

## Manual Checks

- [x] **Verifier subagent (independent):** PASS WITH CONCERNS → 144/144 at run time; all 3 tools gate
      `data.socios` fail-closed; metrics pure-Python deterministic; legal-form rejoin keeps
      "Lasercare, SL" whole; no financial/PII leak even with budget/email columns injected. Concerns
      were housekeeping (verification.md pending; no network-specific prompt line — the general
      no-derive rule covers counts).
- [x] **Adversarial security review (workflow):** 3 dimensions. **2 findings found + FIXED:**
      (1) MEDIUM — `connection_between` leaked `data.retos`-gated reto titles (candid member problem
      statements) to a `data.socios`-only caller → now the via labels are withheld unless the caller
      holds `data.retos`/`data.proyectos` (grants threaded via `dispatch_tool`); (2) LOW — `_net_find`
      non-deterministic tie-break → now `(len, name)` + exact-match preference. +3 regression tests.
- [~] **LaunchGuardian local scan:** gitleaks 0, trivy 0, api_surface 0, frontend_exposure 0, 0
      blockers. INCOMPLETE only for semgrep-on-Windows; run on Linux/CI for the SAST gate.
- [x] **Live proof (counts/structure only):** 208 socios, 1413 connections; top hubs Eurecat (77) /
      CEIT / HAMAMATSU / Leitat / Tekniker; no spurious legal-form nodes.

## Documentation Updates

- [x] Delta specs synced into living capabilities: `agentic-conversation.md` (network tools) +
      `access-control.md` (`data.socios` gates the network tools).
- [x] Decision log records the surfacing choice, edge sources, the legal-form rejoin, and the gating.
- [ ] No README/PROJECT_CONTEXT change required beyond the specs.

## Result

PASS — 147 tests green; verifier PASS; adversarial review 2 findings found + fixed (cross-grant label
leak closed, resolver determinism); deterministic, gated, non-sensitive, zero-copy. Going-LIVE
prerequisite (already met): `SECPHO_LIVE_DATA` + token on Render. Follow-up: LaunchGuardian on Linux/CI
for the semgrep SAST gate.
