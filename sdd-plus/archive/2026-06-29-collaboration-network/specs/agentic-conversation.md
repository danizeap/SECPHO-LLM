# Capability: agentic-conversation (delta — collaboration network tools)

## Requirements

### Requirement: Collaboration network tools
The agent SHALL expose three deterministic collaboration-network tools, gated `data.socios`:
`socio_network` (a socio's collaborators ranked by shared project/reto count, with via-what and its
degree), `network_overview` (most-connected socios by weighted degree, plus total nodes and edges),
and `connection_between` (the shared projects/retos linking two socios, or that they are not linked).
The graph is an undirected weighted co-participation graph built deterministically from
`proyectos.partners` and reto participant fields; participant names are split on comma/pipe/semicolon
with bare legal-form suffixes ("SL", "S.L.", "S.A."…) re-joined so a name is not shattered into
spurious nodes. The LLM SHALL quote the deterministic figures and SHALL NOT derive its own metric.

#### Scenario: Who does a socio collaborate with
- **WHEN** a `data.socios` holder asks who a socio works with
- **THEN** `socio_network` returns its collaborators ranked by shared project/reto count, each with
  the breakdown (via projects / via retos), and its degree.

#### Scenario: How two socios connect
- **WHEN** a user asks how two socios are linked
- **THEN** `connection_between` returns the shared projects/retos, or that there is no direct
  collaboration.
