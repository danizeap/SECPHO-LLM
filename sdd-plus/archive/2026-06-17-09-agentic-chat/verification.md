# Verification

## Change

09-agentic-chat

## Automated Checks

- [x] `python -m py_compile backend_api/mvp_web_app.py` passed.
- [x] Two live OpenAI Responses API probes confirmed the function-calling wire format and a full stateless round-trip (model `gpt-5.5 -> gpt-5.5-2026-04-23`; final answer "There are 75 official SECPHO socios based in Barcelona.").
- [x] String-aware JS balance check on the chat script returned OK.

## Manual Checks

- [x] Import-level `agent_chat` run — cross-source question (top 3 socios by province + 2 photonics events) chained tools and returned a grounded answer.
- [x] Import-level recommend question — called `get_person_profile` then `recommend_contacts`, set `selected=74449`, and the answer carried `[tune:74449]` and `[person:ID]` tokens.
- [x] Import-level memory follow-up ("de esos, quien encaja mejor por necesidades?") used the conversation history, called `get_person_profile` four times, and returned a grounded comparison.
- [x] Over HTTP `POST /api/agent` — the cross-source question acted with defaults (used the readiness ranking) instead of asking; the recommend turn set the selected person and the tune token; a trivial turn returned 200; an empty message returned 400.
- [x] Independent `drydock:verifier` review returned VERIFIED: loop is bounded (`max_steps`) and exception-safe; the no-reorder guarantee holds (no other tool emits a ranking); bulk-email leakage prevented by `_agent_compact_person`; endpoint is auth-gated/rate-limited/size-capped and degrades to the router instead of 500-ing; no regression to existing `/api/chat-flow`, `/api/rerank`, `/api/report-tuned`, `/tuning`, or `/admin`.

## Documentation Updates

- [x] Specs updated (delta + living `agentic-conversation` capability spec).
- [x] No README change needed. Reason: internal chat behavior change; no user-facing setup change beyond the existing `OPENAI_API_KEY`.

## Result

PASS -- bounded, grounded, fail-closed agent loop ships behind the auth-gated `POST /api/agent` with internal fallback; live and HTTP checks plus an independent verifier review all passed.
