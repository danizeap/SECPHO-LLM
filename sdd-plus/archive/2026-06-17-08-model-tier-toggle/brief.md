# Brief

## Change

08-model-tier-toggle

## User Need

Chat users want to pick the model behind each conversation: a flagship model for
complex questions and a cheaper "mini" model for everyday ones, chosen from a
toggle on the chat composer without leaving the page.

## Problem

The chat always used a single fixed model (`gpt-5-mini`). There was no way to
escalate hard questions to a stronger model, nor to keep cheaper defaults for
routine ones. The flagship id also could not be hardcoded safely (a wrong/blank
model id is the same bug class fixed in packet 01), so it had to be configurable.

## Scope

In scope:

- Tier-aware model selection (`mini` default / `flagship`) driven per request.
- `OPENAI_MODEL_FLAGSHIP` env constant (default `gpt-5.5`).
- Mini/Flagship toggle on the chat composer, persisted to `localStorage`.
- Passing the chosen tier on chat, `/api` GET, and tuner (rerank/report-tuned) calls.
- Extra output-token headroom for flagship answer calls to avoid truncation.
- `render.yaml` env wiring for the flagship model.

Out of scope:

- Changing the mini model id (stays `gpt-5-mini`, still overridable via `OPENAI_MODEL`).
- Per-user or per-role model policy; everyone gets the same toggle.
- Cost accounting / usage metering for the flagship tier.

## Acceptance Criteria

- [x] `current_model()` returns `gpt-5-mini` for the mini tier and the flagship id for the flagship tier.
- [x] `/api/chat-flow?model=mini` resolves to `gpt-5-mini`; `?model=flagship` resolves to the flagship model.
- [x] The flagship id is read from `OPENAI_MODEL_FLAGSHIP` (default `gpt-5.5`), never hardcoded blank.
- [x] Flagship answer calls get at least 4000 `max_output_tokens` so the visible reply is not truncated; the small router call is unaffected.
- [x] A Mini/Flagship toggle appears on the chat composer and persists the choice across reloads via `localStorage` key `secpho_model`.

## Impact Areas

- Backend: Tier-aware `current_model()`, thread-local tier, GET/POST gates, `call_llm` headroom.
- Frontend: Model-row toggle markup + CSS, `MODEL`/`setModel` JS, `&model=` on fetches, `model_label` i18n.
- Data model: None.
- API: `/api/*` GET and `/api/chat-flow` POST now accept a `model` parameter (`mini`/`flagship`); default `mini`.
- AI/model behavior: Flagship tier routes to a reasoning model with raised token headroom for answers.
- Documentation: None (no user-facing docs file changed).
- Operations/security: `render.yaml` adds `OPENAI_MODEL_FLAGSHIP=gpt-5.5`.

## Open Questions

None.
