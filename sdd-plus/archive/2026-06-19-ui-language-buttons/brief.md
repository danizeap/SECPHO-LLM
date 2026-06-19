# Brief

## Change

ui-language-buttons

## User Need

Owner: the in-chat action buttons should look like the tuner's prominent buttons (not thin
pills), and the UI must not mix languages — if the session is Spanish, everything is Spanish.

## Problem

- The `[tune]`/`[report]`/`[person]` chat buttons were small pills; the Owner wanted the bigger
  CTA look of the tuner buttons.
- Language bleed: the `[tune]` button label was hardcoded English ("Adjust weighting & report")
  and `[report]` hardcoded Spanish; the per-answer badge showed English "LLM active · <model> ·
  <kind>"; and the report's prose/weighting note followed the UI language while its structure is
  hardcoded Spanish (so an EN session produced a half-English report).

## Scope

In scope:
- Restyle `.inline-action` to a bigger, bolder button (matches the tuner button sizing).
- Localize the server-rendered token button labels by `current_lang()` (set per request).
- Simplify the per-answer badge to a localized LLM-status (drop the English model id/kind).
- Make the report body always Spanish (it is a Spanish deliverable); UI language affects only the
  chat chrome.

Out of scope:
- Translating the report structure/headings into English (the report is a Spanish artifact).
- The separate INDEX_HTML demo page badge.

## Acceptance Criteria

- [x] `.inline-action` buttons are larger/bolder, consistent with the tuner buttons.
- [x] Token labels render in the session language (es: "Ajustar ponderación e informe" / "seleccionar";
      en: "Adjust weighting & report" / "select").
- [x] The per-answer badge is localized (t('llm_on')/t('llm_off')), no English model/kind string.
- [x] A report is fully Spanish even when the UI is English.
- [x] AST/escape clean, chat JS valid (esprima), full suite green.

## Impact Areas

- Backend: `markdown_to_chat_html` localizes labels; `build_report_model` forces report_lang=es.
- Frontend: `.inline-action` CSS; chat mode-badge JS.
- Data model / API: none.
- AI/model behavior: report prose forced to Spanish (was UI-lang).
- Documentation: none needed (bilingual coverage improved, no capability requirement change).
- Operations/security: none.

## Open Questions

- None. (If bilingual *reports* are ever wanted, that's a separate, larger effort.)
