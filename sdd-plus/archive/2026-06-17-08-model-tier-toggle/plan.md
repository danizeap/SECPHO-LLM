# Plan

## Change

08-model-tier-toggle

## Approach

1. Add `OPENAI_MODEL_FLAGSHIP = os.getenv("OPENAI_MODEL_FLAGSHIP") or "gpt-5.5"`
   alongside the existing `OPENAI_MODEL` constant.
2. Introduce a per-request model tier on the existing thread-local request
   context: `set_request_model(value)` (maps anything starting with `flag` to
   `flagship`, else `mini`) and `current_model_tier()` (default `mini`).
3. Make `current_model()` tier-aware: `flagship` -> `OPENAI_MODEL_FLAGSHIP`,
   `mini` -> `OPENAI_MODEL`, each with env override and a final literal fallback.
4. Set the tier from the request: the `/api/*` GET gate reads `params["model"]`,
   the `/api/chat-flow` POST reads `payload["model"]` (both default `mini`).
5. In `call_llm`, when the tier is `flagship` and the call is an answer-length
   call (`max_output_tokens >= 1000`), raise to at least 4000 tokens so reasoning
   spend does not truncate the visible reply; leave the small router call as-is.
6. Frontend: add a Mini/Flagship toggle (`model-row` markup + CSS), a `MODEL`
   state hydrated from `localStorage` `secpho_model`, a `setModel()` that
   persists and updates the active button, and append `&model=MODEL` to `api()`,
   the chat POST body, and the tuner fetches (rerank, report-tuned). Add the
   `model_label` i18n key (EN/ES).
7. Wire `OPENAI_MODEL_FLAGSHIP=gpt-5.5` into `render.yaml`.

## Files Expected To Change

- `backend_api/mvp_web_app.py`
  - `OPENAI_MODEL_FLAGSHIP` constant.
  - `current_model()` (tier-aware), `set_request_model()`, `current_model_tier()`.
  - `/api/*` GET gate and `/api/chat-flow` POST gate (`set_request_model`).
  - `call_llm()` flagship headroom rule.
  - `CHAT_HTML`: `.model-row` markup + CSS, `MODEL`/`setModel`, `&model=` in
    `api()` / chat POST / `rerank` / `report-tuned`, `model_label` i18n key.
- `render.yaml` (adds `OPENAI_MODEL_FLAGSHIP`).

## Risks

- Wrong/blank flagship id breaks all flagship calls (the packet-01 bug class).
  Mitigated by reading from env with an owner-confirmed default and verifying the
  id resolves live on the account before shipping.
- Reasoning models truncate visible answers when output tokens are spent on
  reasoning. Mitigated by the >=4000-token headroom rule on flagship answer calls.
- Headroom wrongly applied to the small router call would waste tokens. Mitigated
  by gating the rule on `max_output_tokens >= 1000`.

## Rollback

- Operational: set `OPENAI_MODEL_FLAGSHIP` to a different id, or leave users on
  the default `mini` toggle (no flagship traffic). The toggle defaults to `mini`.
- Code: `git revert` the change, or remove the `model-row` toggle and force
  `current_model()` back to `OPENAI_MODEL`; the tier helpers default to `mini`,
  so dropping the `&model=` params reverts behavior to mini-only.
