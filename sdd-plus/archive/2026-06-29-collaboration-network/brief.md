# Brief

## Change

collaboration-network (P5, slice 3). Full design in [blueprint.md](blueprint.md).

## User Need

SECPHO wants to see its collaboration structure: who works with whom, who the hubs are, and how any
two members are connected — to spot central players, find collaborators, and understand the network.

## Problem

The project/reto co-participation data was loaded but never turned into a relationship graph. There
was no way to ask "who collaborates with X?" or "who are our most-connected socios?".

## Scope

In scope:

- Deterministic weighted co-participation graph from `proyectos.partners` + reto participant fields.
- Tools `socio_network`, `network_overview`, `connection_between`, gated `data.socios`.
- Textual/structured output (the LLM narrates ranked collaborators/hubs); legal-form name rejoin.

Out of scope:

- Rendered visual graph (textual v1; visual is a follow-on off the same graph).
- Event co-attendance edges (noisy); heavy centrality (betweenness); name normalization across
  sources; persistence. The eval set is the final P5 slice.

## Acceptance Criteria

- [x] Deterministic graph from projects + retos; legal-form names ("Lasercare, SL") kept whole.
- [x] `socio_network`/`network_overview`/`connection_between` return ranked, deterministic results.
- [x] All three gated `data.socios` (fail-closed); LLM narrates, doesn't derive metrics.
- [x] Live-proven: 208 socios / 1413 connections; hubs match real tech-transfer centres.
- [ ] Verify + verifier + adversarial review + LaunchGuardian at close-out.

## Impact Areas

- Backend: `mvp_web_app.py` (graph builder + 3 tools + gating + schemas + dispatch).
- Frontend: none.
- Data model: in-memory graph derived from `proyectos`/`retos`; nothing persisted.
- API: 3 new agent tools (ride `/api/agent`).
- AI/model behavior: deterministic graph metrics; LLM narrates.
- Documentation: delta specs (agentic-conversation, access-control).
- Operations/security: non-sensitive relationship data; gated `data.socios`; zero-copy.

## Open Questions

- Visual rendering — deferred to a follow-on (off the same deterministic graph).
- Cross-source socio-name normalization — a future enhancement (v1 matches as-recorded).
