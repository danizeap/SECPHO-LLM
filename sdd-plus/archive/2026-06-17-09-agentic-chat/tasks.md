# Tasks

## Change

09-agentic-chat

## Implementation

- [x] Probe the live OpenAI Responses API twice to confirm the function-calling wire format and a full stateless round-trip.
- [x] Write `AGENT_INSTRUCTIONS` grounding prompt (no invention, math-decides ranking rule, Phase-1 scope, event-interest caveat, no bulk emails, preserve `[person:ID]`, append `[tune:ID]`, act with sensible defaults).
- [x] Define `AGENT_TOOL_SCHEMAS` with 11 function tools wrapping the deterministic data functions.
- [x] Implement `dispatch_tool(name, args, ctx)` with whole-body try/except returning `{"error": ...}`.
- [x] Add `_agent_compact_person` (drops email for privacy) and `_agent_resolve_member_id` (resolve by id or name).
- [x] Implement `call_agent_step` (Responses API POST, flagship token headroom, `store: False`).
- [x] Implement `run_agent(input_items, ctx, max_steps=6)` — the bounded loop with final capped call and empty-string return on None/error.
- [x] Implement `agent_chat(message, history, member_id)` building input items from last ~6 turns + selected-person context + new message.
- [x] Add `POST /api/agent` in `do_POST` — auth-gated, `llm` rate-limited, empty -> 400, body > 200000 -> 413, internal fallback to `chat_flow`.
- [x] Update `CHAT_HTML` `sendMessage` to post `/api/agent` with history/id/lang/model and maintain a client history array capped at 12; clear it in `newChat`.
- [x] Run verification (py_compile, import-level agent run, HTTP checks, JS balance check, independent verifier review).
