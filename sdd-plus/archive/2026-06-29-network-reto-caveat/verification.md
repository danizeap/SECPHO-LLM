# Verification

## Change

network-reto-caveat

## Automated Checks

- [x] `python -m pytest tests/test_collaboration_network.py` — 9 passed.
  - `test_network_overview_hubs`: with projects present, `connections_via_projects == 4`,
    `connections_via_retos == 3`, `note == ""`.
  - `test_network_overview_flags_reto_dominated`: with no project partners, `connections_via_projects
    == 0`, reto edges ≥ 1, and a non-empty note mentioning retos.
- [x] `python -m pytest tests/` — 169 passed (no regression; +1 new).

## Manual Checks

- [ ] Post-deploy: "¿quiénes son los más conectados?" → the answer notes the network is reto-dominated
      (project co-participation sparse) rather than implying rich project collaboration.

## Documentation Updates

- [x] Specs updated: agentic-conversation delta (network overview reports the split + reto-dominance note).
- [x] No README change needed. Reason: honest-output refinement, no new user workflow.

## Result

Implementation + automated verification COMPLETE (169 passed). Pending only the post-deploy spot-check.
The root cause (sparse `proyectos.partners`) is SECPHO's data to enrich; the tool is honest either way.
