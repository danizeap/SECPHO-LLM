# Decision Log

## Change

chat-conversational-reliability

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-17 | Conversational-first agent instructions; act directly only on clear data/recommendation requests | The agent dumped a full report on a chatty question; staff want a colleague, not a report machine | A separate "intent classifier" step (rejected: extra latency/cost; the instructions carry it) |
| 2026-06-17 | Keep in-chat recommendations a concise list + `[tune:ID]`; full report only on explicit ask | The full one-page report is a deliberate, button-triggered deliverable (the tuner flow); inline dumps preempt it | Always render the full report inline (rejected: that was the bug) |
| 2026-06-17 | Raise OpenAI request timeouts 25s/30s -> 60s | gpt-5-mini latency is 4-60s+; tight timeouts traded a rare slow answer for frequent silent fallbacks to the dumb router | Keep 30s (rejected: measured frequent spikes); unbounded (rejected: no ceiling) |
| 2026-06-17 | Cap the agent loop at a 75s cumulative budget, shrinking each call's timeout | Per-call 60s x up to 5 steps could exceed the proxy/CDN ~100s cutoff and 524 the user | Lower `max_steps` (rejected: hurts multi-tool answers); rely on per-call timeout only (rejected: no total bound) |
