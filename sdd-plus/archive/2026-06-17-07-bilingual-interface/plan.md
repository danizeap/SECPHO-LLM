# Plan

## Change

07-bilingual-interface

## Approach

All work is contained in `backend_api/mvp_web_app.py`.

1. Per-request language context (backend): add `_REQUEST_CTX =
   threading.local()`, `set_request_lang(value)` (normalizes anything starting
   with "en" to `"en"`, else `"es"`), and `current_lang()` (default `"es"`).
2. Single LLM change point: `language_directive()` returns an English or Spanish
   instruction; append its return value to the model `instructions` wherever the
   model is invoked (the `call_llm` config dict and the agent config), so the
   response language is enforced without threading a `lang` parameter through
   every tool/function.
3. Read language per request: the GET `/api/` gate calls
   `set_request_lang(params.get("lang", ["es"])[0])`; the agent POST handler
   calls `set_request_lang(payload.get("lang", "es"))`.
4. Frontend i18n engine in `CHAT_HTML`: an `I18N` object with full `{es, en}`
   string tables; `t()`, `applyLang()`, `toggleLang()`, `detectLang()`;
   `data-i18n` / `data-i18n-ph` attributes on all UI chrome; an ES/EN toggle
   button (`#langToggle`, default "es"); `localStorage` persistence under
   `secpho_lang`; localized example-prompt queries (`q_*`) and tuner slider
   labels (`sig_*`, rebuilt on language change).
5. Detect-on-send: in `sendMessage`, run `detectLang(text)` and call
   `applyLang(detected)` when the user writes the other language.
6. Wire `&lang=` (and `&model=`) into every client fetch: `api()`, the rerank
   fetch, the tuned-report fetch, and the agent POST body all send `LANG`.
7. Localize `LOGIN_HTML` to Spanish by default with `data-es`/`data-en`
   attributes and a small inline ES/EN toggle (`loginToggle`/`loginApply`);
   change the server-injected login error strings to Spanish.

## Files Expected To Change

- `backend_api/mvp_web_app.py`
  - `_REQUEST_CTX`, `set_request_lang`, `current_lang`, `language_directive`.
  - `call_llm` config (`"instructions": LLM_INSTRUCTIONS + language_directive()`)
    and the agent config (`AGENT_INSTRUCTIONS + language_directive()`).
  - GET `/api/` gate (`set_request_lang(params.get("lang", ["es"])[0])`) and the
    agent POST handler (`set_request_lang(payload.get("lang", "es"))`).
  - `CHAT_HTML`: `I18N`, `t`/`applyLang`/`toggleLang`/`detectLang`, `data-i18n`
    markup, `#langToggle`, `sendMessage` detect-on-send, and the
    `lang=`/`model=` query/body wiring in `api()`, rerank, and report fetches.
  - `LOGIN_HTML`: `data-es`/`data-en` markup, `loginApply`/`loginToggle`, and the
    `LOGIN_HTML.replace("{{ERROR}}", ...)` Spanish error strings.

## Risks

- Embedding a large `I18N` object inside the `CHAT_HTML` `<script>` could
  introduce a brace/quote imbalance and blank-page the chat. Mitigated by a
  string-aware brace/quote balance check on the embedded script (returned OK).
- A `lang` value never reaching `call_llm` would leave responses in the default.
  Mitigated by enforcing language at a single choke point (`language_directive()`
  appended in the LLM config) and defaulting to `"es"` everywhere.
- Deterministic fallbacks stay English, so a fallback answer could mismatch a
  Spanish UI. Accepted: the active-LLM path covers the demo; documented as out
  of scope.

## Rollback

- The feature is plain code in one file; revert by `git revert` / restoring the
  prior `backend_api/mvp_web_app.py`.
- To neutralize the response-language behavior without a full revert, make
  `language_directive()` return `""` (responses fall back to the model default)
  — the UI toggle and detection are inert client-side strings with no backend
  state. There is no env-var flag; default behavior is Spanish.
