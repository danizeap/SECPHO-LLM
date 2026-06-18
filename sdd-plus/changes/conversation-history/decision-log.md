# Decision Log

## Change

conversation-history

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-18 | Persist in client `localStorage`, not server/DB | Render free tier disk is ephemeral; the app already stores lang/model prefs client-side; conversations are per-user and need no sharing | Server-side store (rejected: ephemeral disk, would need a DB + auth-scoped storage for a UX nicety); `sessionStorage` (rejected: dies on tab close, doesn't survive the reported tuner round-trip reliably) |
| 2026-06-18 | "New chat" snapshots-then-clears instead of discarding | Owner wants Claude-style history; the old clear-on-new-chat destroyed prior conversations | Keep clear-only (rejected: that is the bug) |
| 2026-06-18 | Cap store at 40 + shrink on quota error | Bound localStorage growth; never let a full quota break the chat | Unbounded (rejected: quota exceptions); tiny cap (rejected: loses useful history) |
| 2026-06-18 | Title from first user message, `esc()`-escaped; ids are `c<timestamp>` | Readable list without an LLM call; escaping + generated ids keep restored HTML/markup injection-safe | LLM-generated titles (rejected: cost/latency for a label) |
| 2026-06-18 | Owner runs the live browser test | No browser/JS runtime here; static + served-page + test verification is the ceiling of what can be checked locally | Claim done without browser test (rejected: dishonest evidence) |
| 2026-06-18 | DEFECT (found in Owner live test): chat fully dead — Enter newlined, send button inert | `renderConvList` built `onclick="loadConversation(\'…\')"` inside a Python `"""` string; Python collapses `\'`→`'` before the browser, yielding `loadConversation('' + id + '')` — a JS SyntaxError that kills the whole `<script>`, so `sendMessage` was never defined and no listeners attached | — |
| 2026-06-18 | Fix: data-attributes + one delegated listener, no inline onclick | Eliminates the entire quote-escaping minefield; matches the existing safe `downloadReportSocio` pattern | Double-escape `\\'` (rejected: fragile, same trap next time) |
| 2026-06-18 | Also fixed a pre-existing twin: tuner "Descargar .docx" `onclick="downloadReport(\'person\',…)"` had the same collapse | Same bug class, shipped earlier this session; it alone broke the script before conversation-history even ran | Added `downloadPersonReport(id)` helper so no inner quotes need escaping |
| 2026-06-18 | Systemic guard: `tests/test_inline_js_syntax.py` parses every served page's inline JS with esprima | `ast.parse` cannot see JS-in-a-Python-string; this bug shipped twice. The test fails CI on any such error and asserts esprima rejects the exact collapse pattern | Manual review only (rejected: already failed twice) |
