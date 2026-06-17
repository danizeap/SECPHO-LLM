# Verification

## Change

08-model-tier-toggle

## Automated Checks

- [x] `python -m py_compile backend_api/mvp_web_app.py` passed.
- [x] Import smoke test: `current_model()` returns `gpt-5-mini` for the mini tier and `gpt-5.5` for the flagship tier.

## Manual Checks

- [x] Live `call_llm` at flagship tier returned mode `llm_gpt-5.5` with real text.
- [x] The flagship default `gpt-5.5` resolved live on the account (API resolved it to `gpt-5.5-2026-04-23`).
- [x] Over HTTP, `/api/chat-flow?model=mini` returned `response.model` `gpt-5-mini`; `?model=flagship` returned the flagship model.
- [x] A realistic flagship answer (default 1400 tokens, raised by the headroom rule) returned a full 3-bullet answer with no truncation.

## Documentation Updates

- [ ] README or user-facing docs updated, if needed.
- [ ] Project context updated, if needed.
- [x] Specs updated (delta + living capability spec `model-selection`).
- [ ] No documentation update needed. Reason:

## Result

PASS -- mini/flagship toggle resolves the correct model per request and flagship answers return untruncated.
