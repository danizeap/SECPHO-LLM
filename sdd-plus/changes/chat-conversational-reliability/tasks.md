# Tasks

## Change

chat-conversational-reliability

## Implementation

- [x] Rewrite `AGENT_INSTRUCTIONS` to conversational-first behavior.
- [x] Raise `call_llm` and `call_agent_step` OpenAI timeouts to 60s.
- [x] Thread a per-call timeout through `call_agent_step`.
- [x] Add the 75s cumulative agent-loop budget with shrinking per-call timeout + graceful fallback.
- [x] Verify behavior live (4 scenarios) and the deadline logic (unit test).
- [x] Independent verifier-subagent review of the diff.
