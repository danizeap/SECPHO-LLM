# Tasks

## Change

conversation-history

## Implementation

- [x] Confirm scope and standards (STANDARD tier: bounded frontend behavior, no auth/schema/API).
- [x] Add CSS + sidebar `#convList` markup.
- [x] Implement the localStorage conversation model and rewrite `newChat()`.
- [x] Persist on the navigation paths (`sendMessage` + `generateTunedReport` finally blocks).
- [x] Restore active conversation on load (`initConversations()`).
- [x] Update docs/specs (agentic-conversation delta spec).
- [x] Run verification (AST parse, served-page assertions, full test suite, verifier subagent).
- [ ] Owner live browser test (cannot be done here — no browser/JS runtime).
