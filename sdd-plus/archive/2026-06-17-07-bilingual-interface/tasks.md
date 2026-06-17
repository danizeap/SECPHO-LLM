# Tasks

## Change

07-bilingual-interface

## Implementation

- [x] Add per-request language context: `_REQUEST_CTX = threading.local()`,
  `set_request_lang(value)`, `current_lang()` (default `"es"`).
- [x] Add `language_directive()` returning the Spanish or English instruction,
  and append it to the model `instructions` in the `call_llm` config and the
  agent config (single LLM change point).
- [x] Read the language per request: `set_request_lang` from the `&lang` param
  in the GET `/api/` gate and from `payload["lang"]` in the agent POST handler.
- [x] Build the frontend i18n engine in `CHAT_HTML`: `I18N` `{es, en}` table,
  `t()`, `applyLang()`, `toggleLang()`, `detectLang()`.
- [x] Annotate all UI chrome with `data-i18n` / `data-i18n-ph` (sidebar blocks,
  topbar, welcome, example prompts, feedback modal, composer, fine-print).
- [x] Add the ES/EN toggle button (`#langToggle`, default "es") and persist the
  choice in `localStorage` under `secpho_lang`.
- [x] Localize the example-prompt queries (`q_*`) and tuner slider labels
  (`sig_*`), rebuilding tuner sliders on language change.
- [x] Detect-on-send: run `detectLang(text)` in `sendMessage` and flip the
  toggle (`applyLang`) when the user writes the other language.
- [x] Send `&lang=LANG` (and `&model=MODEL`) from `api()`, the rerank fetch, the
  tuned-report fetch, and the agent POST body.
- [x] Localize `LOGIN_HTML` to Spanish by default with `data-es`/`data-en` and an
  inline ES/EN toggle (`loginApply`/`loginToggle`).
- [x] Change the server-injected login error strings to Spanish
  ("Contraseña incorrecta.", "Demasiados intentos. Inténtalo más tarde.").
- [x] Run verification (see verification.md).
