# Tasks

## Change

08-model-tier-toggle

## Implementation

- [x] Add `OPENAI_MODEL_FLAGSHIP` constant (env-driven, default `gpt-5.5`).
- [x] Add `set_request_model()` and `current_model_tier()` on the request thread-local (default `mini`).
- [x] Make `current_model()` tier-aware (flagship -> flagship id, mini -> `OPENAI_MODEL`).
- [x] Set the tier from the `/api/*` GET gate (`params["model"]`) and the `/api/chat-flow` POST gate (`payload["model"]`).
- [x] Add the flagship answer-call token headroom rule in `call_llm` (>=4000 when flagship and `max_output_tokens >= 1000`; router call untouched).
- [x] Add the Mini/Flagship composer toggle: `model-row` markup + CSS, `MODEL` state from `localStorage` `secpho_model`, and `setModel()`.
- [x] Append `&model=MODEL` to `api()`, the chat POST body, and the tuner fetches (rerank, report-tuned).
- [x] Add the `model_label` i18n key (EN/ES).
- [x] Wire `OPENAI_MODEL_FLAGSHIP=gpt-5.5` into `render.yaml`.
- [x] Run verification (py_compile, import smoke test, live `call_llm`, HTTP tier checks).
