# Brief

## Change

07-bilingual-interface

## User Need

SECPHO is a Spanish-first organization. Demo visitors and members expect the
product to speak Spanish out of the box — both the interface chrome and the
assistant's answers — while still letting English-speaking guests switch with
one click. The language they actually type in should be respected automatically.

## Problem

The chat app shipped English-only: the UI strings, the login page, and the
LLM's responses were all hardcoded English. There was no way to present the
product in Spanish, no toggle, and no detection of the user's input language —
making it awkward for the primary Spanish-speaking audience.

## Scope

In scope:

- Spanish as the default language for UI chrome and assistant responses.
- An ES/EN toggle that switches both the UI and the response language together.
- Auto-detection of the language the user writes, flipping the toggle to match.
- A full `{es, en}` string table covering sidebar, topbar, welcome, example
  prompts, feedback modal, composer, fine-print, errors, and tuner labels.
- Localized login page (Spanish default + inline ES/EN toggle) and Spanish
  server-injected login error strings.
- Per-request enforcement of the response language in the active-LLM path.

Out of scope:

- Localizing the deterministic (non-LLM) fallback responses — they remain English.
- An ES/EN/both language picker for report downloads/exports (deferred with the
  export feature).
- Languages other than Spanish and English.

## Acceptance Criteria

- [x] Login page defaults to Spanish ("...Inicia sesión para continuar.") and
  offers an inline ES/EN toggle.
- [x] Chat UI defaults to Spanish, persists the choice in `localStorage`
  (`secpho_lang`), and exposes a topbar toggle (`#langToggle`) that switches all
  `data-i18n` / `data-i18n-ph` chrome.
- [x] Assistant responses come back in Spanish by default and in English when
  `lang=en` is sent, enforced via `language_directive()` appended in `call_llm`.
- [x] `/api/chat-flow` returns the same question localized (e.g. "Resumen
  ejecutivo" vs "Quick SECPHO intelligence briefing") per `&lang`.
- [x] `/api/report-tuned` returns the generated report in Spanish vs English per
  `&lang`.
- [x] Typing in the other language auto-flips the toggle on send (`detectLang`).
- [x] Server-injected login errors are Spanish ("Contraseña incorrecta.",
  "Demasiados intentos. Inténtalo más tarde.").

## Impact Areas

- Backend: Per-request thread-local language context; `set_request_lang` wired
  into the GET `/api/` gate and the agent POST handler.
- Frontend: i18n engine in `CHAT_HTML` (`I18N` table, `t`/`applyLang`/
  `toggleLang`/`detectLang`), `data-i18n` markup, `#langToggle`; localized
  `LOGIN_HTML` with inline toggle.
- Data model: None.
- API: No new endpoints or shape changes; existing `/api/*` now read a `lang`
  param (GET query / POST body) and localize responses accordingly.
- AI/model behavior: Response language enforced by `language_directive()`
  appended to the model `instructions` in `call_llm`.
- Documentation: This packet.
- Operations/security: None (login auth/rate-limit behavior unchanged; only
  error wording localized to Spanish).

## Open Questions

None.
