# Plan

## Change

chat-conversational-reliability

## Approach

1. `AGENT_INSTRUCTIONS`: replace the single "Default to ACTING" bullet with four
   bullets — converse first; answer direct data questions directly; open/exploratory
   -> suggest + offer + WAIT, never dump a report unprompted; recommendations =
   concise list + `[tune:ID]`, full report only on an explicit "the report"/"el informe".
2. `call_llm` timeout 25 -> 60; `call_agent_step` timeout 30 -> 60.
3. `call_agent_step(..., timeout: int = 60)` — thread a per-call timeout.
4. `run_agent`: `AGENT_TOTAL_BUDGET_S = 75`; `deadline = time.monotonic() + budget`;
   before each step break if `<5s` left, else call with `timeout=min(60, remaining)`;
   guard the final capped call the same way; on exhaustion return "" so `agent_chat`
   falls back to the heuristic `chat_flow`.

## Files Expected To Change

- `backend_api/mvp_web_app.py` (AGENT_INSTRUCTIONS, call_llm, call_agent_step, run_agent)

## Risks

- A genuinely slow multi-tool turn can now wait up to ~75s before answering or
  falling back (rare; common case ~5-15s). Bounded under the ~100s proxy cutoff.
- Explicit-report trigger keys on the literal strings "the report"/"el informe";
  other phrasings get the concise list + tuner button (degrades gracefully).

## Rollback

Revert commits `72dd947` and `44b981e`. Pure prompt/timeout change in one file;
no data or API-contract change.
