# Plan

## Change

09-agentic-chat

## Approach

1. De-risk: probe the live OpenAI Responses API twice to confirm the function-calling wire format — `tools = [{type:"function", name, description, parameters}]`; the model returns `output` items of type `function_call` with `name`, `arguments` (JSON string), `call_id`; continue statelessly by re-sending `input = [...prior, {type:"function_call", call_id, name, arguments}, {type:"function_call_output", call_id, output}]` with the tools; the final answer arrives as a `message` item read by the existing `extract_response_text`. Confirmed `gpt-5.5 -> gpt-5.5-2026-04-23` and a full stateless round-trip.
2. Write `AGENT_INSTRUCTIONS`: grounding prompt — use tools for real data, never invent, rankings come only from the recommender tools (math decides), Phase-1 scope, event-interest caveat, no bulk emails, preserve `[person:ID]`, append `[tune:ID]`, act with sensible defaults.
3. Define `AGENT_TOOL_SCHEMAS`: 11 function tools wrapping existing deterministic functions (search_people, get_person_profile, search_socios, get_socio_profile, rank_socios, list_events, list_retos, ecosystem_overview, aggregate_stats, recommend_contacts, rerank_contacts).
4. Implement `dispatch_tool(name, args, ctx)` routing each tool to its deterministic function, whole body in try/except returning `{"error": ...}`; add `_agent_compact_person` (drops email) and `_agent_resolve_member_id` (id or name).
5. Implement `call_agent_step` (posts to Responses API; flagship gets higher `max_output_tokens`; `store: False`) and `run_agent` (the bounded loop, `max_steps=6`, one final capped call, returns `""` on None/error for caller fallback).
6. Implement `agent_chat(message, history, member_id)` building input items from last ~6 turns + optional selected-person context + new message.
7. Add `POST /api/agent` in `do_POST`: behind `/api` auth gate, `llm` rate-limit, empty -> 400, body > 200000 -> 413; run `agent_chat` when `openai_available()` and answer non-empty, else fall back to `chat_flow`.
8. Frontend: `sendMessage` posts `/api/agent` with `history.slice(-6)`, id, lang, model; maintain a client history array capped at 12; `newChat` clears it.

## Files Expected To Change

- `backend_api/mvp_web_app.py` — `AGENT_INSTRUCTIONS`, `_agent_compact_person`, `_agent_resolve_member_id`, `dispatch_tool`, `AGENT_TOOL_SCHEMAS`, `call_agent_step`, `run_agent`, `agent_chat`, the `POST /api/agent` block in `do_POST`, and `CHAT_HTML` `sendMessage`/`newChat`.

## Risks

- Unbounded tool loop / runaway cost — mitigated by `max_steps=6`, a single final capped call, and `store: False` stateless calls.
- Model reordering or inventing rankings — mitigated by the grounding prompt plus the fact that ranking can only originate from `recommend_contacts`/`rerank_contacts`; no other tool emits a ranking.
- Leaking bulk personal emails — mitigated by `_agent_compact_person` dropping `email` from people lists.
- Tool exceptions crashing the request — mitigated by `dispatch_tool` returning `{"error": ...}` instead of raising.
- Chat breaking with no API key or LLM error — mitigated by internal fallback to `chat_flow`; the endpoint never 500s.
- Unauthenticated or oversized requests — mitigated by the `/api` auth gate, `llm` rate-limit bucket, and the 200000-byte body cap.

## Rollback

Revert the agent functions and the `POST /api/agent` block in `backend_api/mvp_web_app.py` (git revert) and restore `sendMessage` to post the prior endpoint. Operationally, the endpoint already degrades to `chat_flow` whenever `OPENAI_API_KEY` is unset, so unsetting the key disables the agent path without code changes.
