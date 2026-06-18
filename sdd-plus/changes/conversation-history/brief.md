# Brief

## Change

conversation-history

## User Need

Staff use the chat, then open the weighting tuner (or reload) and come back — and the
conversation is gone. The Owner called this "a huge issue." They want Claude-style
persistent conversations: a sidebar list, click to resume, nothing lost on navigation.

## Problem

The chat held its state only in live DOM + an in-memory `history` array. Any full-page
navigation (tuner link, reload, returning to chat) destroyed it. "New chat" simply
cleared everything with no way to get a prior conversation back.

## Scope

In scope:

- Client-side conversation persistence in `localStorage` (no server/DB — Render free disk is ephemeral).
- Sidebar conversation list: title from first user message, switch, delete, active highlight.
- Restore active conversation on page load; snapshot before navigation/new-chat.
- Capped store (40) with graceful degradation when storage is full/unavailable.

Out of scope:

- Server-side or cross-device conversation storage.
- Search within conversations, rename, export.
- Any backend/API/auth/data-model change.

## Acceptance Criteria

- [x] Mid-conversation → open tuner → back to chat: conversation restored, not wiped.
- [x] Sidebar lists conversations; clicking one restores its messages, `history`, selected-person.
- [x] "New chat" archives the current conversation (still reachable) before clearing.
- [x] Delete removes a conversation; deleting the active one resets to a fresh welcome.
- [x] `localStorage` full/disabled does not break the chat (store shrinks or is skipped).
- [x] App still parses, serves the chat page with the new elements, and all 18 tests pass.

## Impact Areas

- Backend: none.
- Frontend: chat page CSS (`.conv-list`/`.conv-item`), sidebar `#convList`, conversation JS model.
- Data model: none (client `localStorage` only).
- API: none.
- AI/model behavior: none (agent input building unchanged; `history` still capped at 12).
- Documentation: agentic-conversation delta spec.
- Operations/security: no new server-side PII; conversations live only in the user's browser.

## Open Questions

- None blocking. Live browser test is the Owner's (no browser/JS runtime available here).
