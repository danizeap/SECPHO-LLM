# Capability: access-control (delta)

Delta for change `chat-history-isolation`. Adds one requirement; merged into the living capability
spec at `/drydock:sync`.

## Requirements

### Requirement: Conversation history is isolated per user on a shared browser
Client-side conversation history (kept in browser `localStorage`, by design — the platform persists
nothing server-side) SHALL NOT be visible across user accounts on the same browser. The server SHALL
embed in the served chat page an opaque per-user tag derived from the session identity, keyed by the
session secret so it cannot be enumerated from a known email and never carries the email itself. The
client SHALL, before loading any stored history, compare the page's tag to the stored owner tag and,
on mismatch (including the legacy un-tagged state), CLEAR (`removeItem`) the conversation history
keys — cleared, not merely hidden, because the content may be sensitive (financial figures, churn
reasons, PII). This closes the data-at-rest path around the RBAC tool gates without introducing any
server-side persistence.

#### Scenario: A different user inherits no history
- **WHEN** user B logs in on a browser where user A previously used the chat
- **THEN** the page carries B's tag, which differs from the stored owner tag, so the client clears
  `secpho_convs`/`secpho_active` before rendering — B sees an empty history, never A's conversations.

#### Scenario: The same user keeps their own history
- **WHEN** the same user returns (same logged-in identity, same browser)
- **THEN** the page tag matches the stored owner tag, no purge occurs, and their own history loads.

#### Scenario: The per-user tag never exposes the email
- **WHEN** the chat page is served to a logged-in user
- **THEN** the embedded tag is a fixed-length opaque hash keyed by the session secret; the raw email
  never appears in the DOM or in `localStorage`, and the tag is not reproducible without the secret.

#### Scenario: Legacy global history is purged on upgrade
- **WHEN** a user first loads the chat after this change ships, with pre-existing un-tagged
  `secpho_convs`/`secpho_active` from before per-user isolation
- **THEN** the absent owner tag counts as a mismatch and the legacy keys are cleared on that first load.
