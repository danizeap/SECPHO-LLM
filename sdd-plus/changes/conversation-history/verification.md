# Verification

## Change

conversation-history

## Automated Checks

- [x] `ast.parse(mvp_web_app.py)` → AST OK (no Python syntax breakage from the embedded edits).
- [x] Boot the real server, log in, GET `/` → chat page served (47208 bytes) containing
      `id="convList"`, `initConversations`, `snapshotMessages`, `loadConversation`, `CONV_KEY`,
      `.conv-item`.
- [x] Referenced JS symbols all resolve in chat-page scope: `t('newchat')`/`t('status_default')`
      (i18n keys present), `esc()` (4108), `history` (4235), `selectedMemberId` (4012),
      `applyLang`/`LANG` (4076-4078).
- [x] CSS `.conv-list`/`.conv-item`/`.active`/`.del` present (3910-3916).
- [x] Full test suite: `python -m pytest tests/ -q` → 24 passed (18 original + 6 new JS-syntax checks).
- [x] NEW: `tests/test_inline_js_syntax.py` parses every served page's inline JS with esprima
      (CHAT/ADMIN/INDEX/LOGIN/TUNING) and asserts esprima rejects the escape-collapse pattern.
      This caught the dead-chat defect below (and a pre-existing twin) that `ast.parse` could not.

## Defect found in Owner live test (fixed, commit cef1d9b)

- [x] Symptom: chat fully dead — Enter inserted a newline, send button did nothing.
- [x] Root cause: JS built as `onclick="loadConversation(\'…\')"` inside a Python `"""` string;
      Python collapses `\'`→`'`, so the browser received `loadConversation('' + id + '')` — a JS
      SyntaxError that broke the whole `<script>` (no `sendMessage`, no key listener).
- [x] Fix: `renderConvList` now emits `data-id`/`data-del` + one delegated `onConvListClick`
      listener (no inline onclick). Twin defect in the tuner "Descargar .docx" button fixed via a
      `downloadPersonReport(id)` helper. esprima now parses all served scripts clean.

## Manual Checks

- [ ] OWNER (live browser, cannot run here — no browser/JS runtime):
      mid-chat → open tuner → back → conversation restored; sidebar lists conversations;
      click switches; delete works; new-chat archives; reload restores active; private-mode /
      storage-disabled still chats.

## Documentation Updates

- [x] Specs updated: agentic-conversation delta (ADDED persistent history, MODIFIED memory req).
- [x] README / user docs: no update needed (internal chat UX, no setup/API change).
- [x] Project context: no update needed (no new architecture/data/deploy assumption).

## Result

PASS (server-side/static verification + tests green; verifier subagent reviewed).
One open manual check delegated to the Owner: the live browser test of the JS behavior.
