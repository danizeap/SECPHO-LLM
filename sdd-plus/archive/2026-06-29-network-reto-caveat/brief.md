# Brief

## Change

network-reto-caveat

## User Need

When someone asks how connected the cluster is, the answer must be honest about WHAT the connections
are — so a reto-co-participation graph isn't mistaken for rich project+reto collaboration.

## Problem

The collaboration network is reto-dominated: on live data the `proyectos.partners` source is sparse
(the known Proyectos data gap), so almost every edge comes from shared retos (e.g. Eurecat showed
`via_projects: 0` for every collaborator). The per-socio tools already expose the via-projects /
via-retos split, but `network_overview` (the cluster summary) reported only total connections — so
the cluster-level answer overclaimed project collaboration (live-test finding #4). The builder code
is correct; the gap is honesty in the summary (and the underlying data is SECPHO's to enrich).

## Scope

In scope:

- `network_overview` reports `connections_via_projects` / `connections_via_retos` and a `note` that
  flags when the graph is reto-dominated (or entirely reto-based).

Out of scope:

- Enriching `proyectos.partners` — that's SECPHO's WordPress data, not ours to fix (zero-copy).
- Per-socio tools (already expose the split).

## Acceptance Criteria

- [x] `network_overview` returns the project-vs-reto edge counts.
- [x] A `note` flags reto-dominance / reto-only when projects contribute few/no edges; empty otherwise.

## Impact Areas

- Backend: `network_overview` (edge-source split + note); schema description.
- Frontend: none.
- Data model: none.
- API: `network_overview` output gains `connections_via_projects` / `connections_via_retos` / `note`.
- AI/model behavior: the agent can state honestly that the graph is reto-dominated.
- Documentation: agentic-conversation delta.
- Operations/security: none (the data-completeness root cause is on SECPHO's side).

## Open Questions

- None. (Whether SECPHO enriches project partner data is their call; the tool is honest either way.)
