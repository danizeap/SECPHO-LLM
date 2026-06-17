# Brief

## Change

chat-conversational-reliability

## User Need

SECPHO staff talk to the assistant like a colleague. A chatty, exploratory message
("hola, ¿quién me sugieres testear?") must get a conversational reply — a suggestion
and an offer — not an immediate wall-of-text report. The chat must also answer
reliably, not randomly degrade to a dumber engine.

## Problem

1. The tool-calling agent over-acted: its instructions said "Default to ACTING...
   Answer the question asked", with nothing about conversing or confirming. So an
   open question was read as "generate a report now" and it dumped a full one-page
   matchmaking report instead of talking first.
2. gpt-5-mini latency is highly variable (measured 4s to 60s+ for the same call).
   The LLM request timeouts were 25s (`call_llm`) / 30s (`call_agent_step`), so on
   every latency spike the app silently fell back to the heuristic router and
   reports timed out.
3. Raising per-call timeouts to 60s created an unbounded worst case: up to 5 agent
   steps x 60s could exceed the proxy/CDN ~100s cutoff and 524 the user.

## Scope

In scope:

- Rewrite `AGENT_INSTRUCTIONS` to be conversational-first.
- Raise both OpenAI request timeouts to 60s.
- Add a 75s cumulative wall-clock budget to the agent loop; per-call timeout shrinks
  with the remaining budget; on exhaustion fall back to the deterministic router.

Out of scope:

- The "Math decides, the LLM explains" hard rules (unchanged; reinforced).
- The deterministic recommendation engine and scoring (unchanged).

## Acceptance Criteria

- [x] Greeting / open question -> conversational reply, no unprompted report.
- [x] Direct data question -> answered directly (no over-passivity / permission-asking).
- [x] Explicit "recommendations for X" -> concise ranked list + `[tune:ID]` token.
- [x] Latency spikes within 60s no longer fall back to the heuristic router.
- [x] A single chat turn is time-bounded (~75s) and degrades gracefully past it.

## Impact Areas

- Backend: `AGENT_INSTRUCTIONS`, `call_agent_step` (timeout param), `run_agent` (deadline), `call_llm` (timeout)
- Frontend: none
- Data model: none
- API: `/api/agent` behavior (same request/response contract)
- AI/model behavior: conversational-first agent; reliability under variable latency
- Documentation: this packet; `agentic-conversation` delta spec
- Operations/security: none (timeouts are outbound; `Handler.timeout` slowloris bound unchanged)

## Open Questions

- None.
