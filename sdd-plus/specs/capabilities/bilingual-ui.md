# Capability: bilingual-ui

Purpose: Make the SECPHO chat product Spanish-first — UI, login, and assistant
responses default to Spanish — with one-click English switching and automatic
detection of the language the user writes.

## Requirements

### Requirement: Spanish-default bilingual interface

The system SHALL present the chat UI, the login page, and the assistant's
responses in Spanish by default, and SHALL let the user switch the entire
experience to English.

#### Scenario: Default language is Spanish

- **WHEN** a user loads the chat or login page with no stored preference
- **THEN** the UI chrome renders in Spanish (default `secpho_lang = "es"`) and
  the assistant responds in Spanish (`current_lang()` defaults to `"es"`).

#### Scenario: Toggle switches UI and response language together

- **WHEN** the user clicks the `#langToggle` button (or the inline login toggle)
- **THEN** `applyLang` re-renders every `data-i18n` / `data-i18n-ph` element in
  the other language, persists the choice in `localStorage` under `secpho_lang`,
  and subsequent API calls send `lang=<new>` so responses switch too.

### Requirement: Per-request response-language enforcement

The system SHALL enforce the assistant's response language per request, in the
active-LLM path, from a `lang` value supplied by the client.

#### Scenario: lang param drives the LLM response language

- **WHEN** an `/api/` request carries `lang=en` (GET query) or `"lang": "en"`
  (agent POST body)
- **THEN** `set_request_lang` records it in the thread-local context and
  `language_directive()` (appended to the model `instructions` in `call_llm`)
  instructs the model to answer entirely in English; otherwise it answers in
  Spanish.

#### Scenario: Same endpoint returns localized output per lang

- **WHEN** `/api/chat-flow` or `/api/report-tuned` is called with `lang=es`
  versus `lang=en`
- **THEN** the same content is returned localized (e.g. "Resumen ejecutivo" vs
  "Quick SECPHO intelligence briefing").

### Requirement: Input-language auto-detection

The system SHALL detect the language the user writes and flip the active
language to match before sending the message.

#### Scenario: Typing the other language flips the toggle

- **WHEN** the active language is Spanish and the user submits a clearly English
  message (`detectLang` returns `"en"`)
- **THEN** `sendMessage` calls `applyLang("en")`, switching the UI and the
  `lang` sent with the request, before the message is dispatched.

### Requirement: Localized login

The system SHALL render the login page in Spanish by default with an inline
ES/EN toggle, and SHALL emit login error messages in Spanish.

#### Scenario: Login page and errors are Spanish

- **WHEN** the login page is served, or a login fails on a bad password or too
  many attempts
- **THEN** the page defaults to Spanish ("...Inicia sesión para continuar.") with
  a `loginToggle` control, and the server injects Spanish errors
  ("Contraseña incorrecta." / "Demasiados intentos. Inténtalo más tarde.").

### Requirement: Scope boundaries

The system SHALL localize the active-LLM response path while leaving
deterministic (non-LLM) fallback responses in English, and SHALL NOT (yet)
provide an ES/EN/both language picker for report downloads.

#### Scenario: Fallback responses remain English

- **WHEN** a deterministic fallback (no active LLM) produces a response
- **THEN** that response is in English, regardless of the selected UI language.
