# Capability: access-control (delta — collaboration network gating)

## Requirements

### Requirement: data.socios gates the collaboration-network tools
The collaboration-network tools (`socio_network`, `network_overview`, `connection_between`) SHALL
require `data.socios` via `TOOL_REQUIRED_GRANT`, enforced fail-closed in `dispatch_tool`. Collaboration
structure is non-sensitive member-relationship data (no euros, PII, or candid reasons), so the
baseline member grant is the appropriate tier.

#### Scenario: Network tools need data.socios
- **WHEN** a caller without `data.socios` invokes a network tool
- **THEN** `dispatch_tool` returns `forbidden` before the tool runs.
