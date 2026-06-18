# Plan

## Change

conversation-history

## Approach

Pure client-side, in the served chat HTML/JS — no backend touched.

1. CSS: add `.conv-list` / `.conv-item` (+ hover/active/delete) before the chat page `</style>`.
2. Markup: add `<div class="conv-list" id="convList">` to the `<aside>` after Sign out.
3. JS conversation model (localStorage):
   - keys `secpho_convs` (array, cap 40) and `secpho_active` (id); capture `WELCOME_HTML`.
   - `snapshotMessages()` clones `#messages`, strips `#welcome`, `[id^="tuner-"]`, `.thinking`.
   - `saveActive()` upserts the active conversation (html, last-12 `history`, selected-person, ts).
   - `renderConvList()` / `loadConversation()` / `deleteConversation()` / `restoreInto()`.
   - `initConversations()` restores the active conversation on load.
   - rewrite `newChat()` to snapshot-then-clear instead of just clearing.
4. Persist on the two navigation paths that leave the page: `saveActive()` in `sendMessage`'s
   `finally` and in `generateTunedReport`'s `finally` (the tuner is the reported loss path).
5. Call `initConversations()` at script end after `setModel(MODEL)`.

## Files Expected To Change

- `backend_api/mvp_web_app.py` (chat page CSS + markup + JS only).
- `sdd-plus/changes/conversation-history/specs/agentic-conversation.md` (delta spec).

## Risks

- localStorage quota / disabled → mitigated: try/catch everywhere, store shrinks on quota error.
- XSS via restored HTML: restored content is the same sanitized HTML the chat itself rendered
  (titles are `esc()`-escaped; conversation ids are generated `c<timestamp>`, not user input).
- No JS runtime here to unit-test the browser logic → mitigated by Python AST parse, served-page
  assertions, and an explicit hand-off for the Owner's live browser test.

## Rollback

Single-file, additive. Revert the `mvp_web_app.py` chat-page edits (CSS block, `#convList`
div, conversation JS, the two `saveActive()` calls, the `initConversations()` call). No data
migration; stale `secpho_convs`/`secpho_active` keys in a browser are harmless and self-cap.
