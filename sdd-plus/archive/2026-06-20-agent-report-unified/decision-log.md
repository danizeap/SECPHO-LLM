# Decision Log

## Change

agent-report-unified

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-19 | Render the unified report HTML for in-chat report requests and pass it through as `answer_html` | The chat report must equal the tuner/download report; the unified model is HTML, so it bypasses `markdown_to_chat_html` to avoid double-escaping | Keep markdown + re-render (rejected: that's the old free-form path) |
| 2026-06-19 | Only the two heuristic sites needed migrating; the agent path unchanged | The agent has no `generate_report` tool — it presents recommendations + the `[report]` token (→ unified download); only `tool_answer`/`chat_flow` produced the free-form report | Add a terminal agent report tool (rejected: unnecessary — the agent already routes to the unified download) |
| 2026-06-19 | Remove `llm_report_for_person`; keep `llm_payload_for_person` | After migration the report function is unreferenced (the last free-form path); the payload helper still feeds recommendations | — |
| 2026-06-19 | Test sets `OPENAI_API_KEY=""` before import (not pop) | The app's `load_dotenv()` on import restores a popped key from `.env`; an existing empty var is left alone → hermetic, no real LLM calls | Pop the key (rejected: load_dotenv re-added it → 15s real calls) |
