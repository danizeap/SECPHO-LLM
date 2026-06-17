# Verification

## Change

chat-conversational-reliability

## Automated Checks

- [x] `python -c "ast.parse(...)"` on `mvp_web_app.py`: parses; module imports.
- [x] Deadline unit test (mocked 3s latency, budget 8s): total time bounded (~6s,
      did not run all steps), per-call timeouts shrink (`[8, 5]`), exhaustion returns "".

## Manual Checks

- [x] Live against the real model (gpt-5-mini), all four behaviors:
  - greeting "hola" -> conversational reply, zero tool calls, no report.
  - "¿quién me sugieres testear?" -> suggests Diana + outlines a report + OFFERS + WAITS.
  - "¿cuántos socios hay por provincia?" -> answers directly (`aggregate_stats`), no over-passivity.
  - "dame las recomendaciones para Diana Martín Becerra" -> concise 5-item ranked list + tokens.
- [x] Latency measured: 4.1 / 7.7 / 23.2 / 60s+ for identical calls -> confirms the
      30s timeout was too tight (the exploratory case fell back at 30s, succeeded under 60s).

## Documentation Updates

- [x] Delta spec `specs/agentic-conversation.md` (conversational-first + reliability).
- [ ] No documentation update needed. Reason: behavior change captured in the delta spec.

## Result

PASS. Independent `drydock:verifier` subagent reviewed the diff -> PASS WITH FOLLOW-UP
(the follow-up — unbounded agent-loop time — was then closed by the 75s budget). Both
fixes are deployed live (commits `72dd947`, `44b981e`).
