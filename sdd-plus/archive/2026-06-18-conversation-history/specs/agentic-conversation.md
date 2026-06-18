# Spec Delta: conversation-history

Capability: agentic-conversation

## ADDED Requirements

### Requirement: Persistent client-side conversation history
The system SHALL persist chat conversations entirely on the client (browser `localStorage`, no server or database), so that navigating away from the chat page (e.g. to the weighting tuner) and back, or reloading, does NOT lose the in-progress conversation. The chat SHALL show a conversation list in the sidebar; selecting an entry restores that conversation's messages, agent `history`, and selected-person context; a per-entry control deletes it. The store SHALL be capped (40 conversations) and SHALL degrade gracefully when `localStorage` is full or unavailable (it shrinks the store, and on hard failure the chat still works without history). Conversations hold only what the chat already renders/holds client-side; no new personal data is persisted beyond the existing message text and the capped (≤12) history array.

#### Scenario: Conversation survives navigation to the tuner and back
- **WHEN** the user is mid-conversation, opens the weighting tuner, then returns to the chat page
- **THEN** the active conversation's messages and context are restored from `localStorage`, not wiped.

#### Scenario: Switching conversations
- **WHEN** the user clicks a different conversation in the sidebar list
- **THEN** the current conversation is saved, and the selected one's messages, `history`, and selected-person are restored.

#### Scenario: localStorage unavailable degrades safely
- **WHEN** `localStorage` is full, disabled, or throws
- **THEN** persistence is skipped or the store is shrunk, and the chat continues to function without raising to the user.

## MODIFIED Requirements

### Requirement: Conversation memory from client history
The system SHALL build the agent input from the last ~6 client-supplied conversation turns plus an optional selected-person context line and the new message, so multi-turn follow-ups resolve against prior turns. Conversation state is not stored server-side (`store: False`); the client maintains the history array (capped at 12). On "new chat" the current conversation is first snapshotted into the persisted conversation store and then the message area and `history` are cleared for a fresh conversation (the prior conversation remains retrievable from the sidebar rather than being discarded).

#### Scenario: New chat archives rather than discards
- **WHEN** the user starts a new chat with messages already present
- **THEN** the current conversation is saved to the sidebar list before the message area and `history` are cleared, so it can be reopened later.
