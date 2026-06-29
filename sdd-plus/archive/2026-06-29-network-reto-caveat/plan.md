# Plan

## Change

network-reto-caveat

## Approach

In `network_overview`, walk the unique undirected edges of the cached graph and count how many involve
a shared project vs a shared reto (an edge can involve both). Return `connections_via_projects` /
`connections_via_retos`, and a `note`: "entirely from shared retos" when projects contribute 0 edges,
"predominantly … sparse" when < 10%, else empty. Update the tool's schema description so the agent
knows the split + caveat exist. No change to the graph builder (it is correct) or the per-socio tools
(they already expose the split).

## Files Expected To Change

- `backend_api/mvp_web_app.py` — `network_overview` (edge-source split + note); its schema description.
- `tests/test_collaboration_network.py` — split assertions on the hubs test; a reto-only caveat test.
- `sdd-plus/changes/network-reto-caveat/specs/agentic-conversation.md` — delta.

## Risks

- Output-shape addition only (new keys); existing consumers/tests unaffected (the hubs test keeps its
  prior assertions and gains the new ones). The note is descriptive text the LLM relays verbatim.

## Rollback

Revert the commit (one function + schema string + tests). No data, schema, env.
