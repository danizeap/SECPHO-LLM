# Decision Log

## Change

08-model-tier-toggle

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-16 | Make the flagship model configurable via `OPENAI_MODEL_FLAGSHIP` instead of hardcoding it | A wrong/blank hardcoded id is the same bug class fixed in packet 01; env keeps it correctable without a deploy | Hardcode the flagship id in source |
| 2026-06-16 | Default the flagship to `gpt-5.5` | Owner-confirmed current OpenAI flagship and verified live (API resolved it to `gpt-5.5-2026-04-23`) | Pin a dated id; leave the default blank |
| 2026-06-16 | Keep mini as `gpt-5-mini` | Cheap, fast default for everyday questions; still overridable via `OPENAI_MODEL` | Switch the default to `gpt-5.4-mini` |
| 2026-06-16 | Apply >=4000-token headroom only to flagship answer calls (`max_output_tokens >= 1000`) | Reasoning models spend output tokens on reasoning and would otherwise truncate the visible reply | Raise tokens for every call; leave tokens unchanged |
| 2026-06-16 | Default the request tier to `mini` and carry the choice in `localStorage` | Safe, cheap default; persists the user's pick across reloads without server state | Default to flagship; store the tier server-side per session |
