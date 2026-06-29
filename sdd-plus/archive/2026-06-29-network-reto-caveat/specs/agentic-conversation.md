# Capability: agentic-conversation (delta)

Delta for change `network-reto-caveat`. Adds a scenario to the collaboration-network requirement;
merged at `/drydock:sync`.

## Requirements

### Requirement: Collaboration network tools

#### Scenario: Cluster overview is honest about reto-dominance
- **WHEN** `network_overview` summarizes the cluster graph
- **THEN** it reports the split of connections via projects vs retos and a note when the graph is
  reto-dominated (or entirely reto-based) because project partner data is sparse — so the agent does
  not imply rich project collaboration that the data doesn't support.
