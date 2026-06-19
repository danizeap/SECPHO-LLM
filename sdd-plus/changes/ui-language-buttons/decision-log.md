# Decision Log

## Change

ui-language-buttons

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-19 | Localize token button labels server-side via `current_lang()` | Labels were hardcoded (tune=EN, report=ES) so they bled the wrong language; `/api/agent` already sets request lang before render | Client-side relabel (rejected: buttons are server-rendered HTML) |
| 2026-06-19 | Simplify the per-answer badge to localized LLM status only | "LLM active · <model id> · <kind>" bled English and was dev-diagnostic clutter | Translate kind + keep model id (rejected: model id is untranslatable noise) |
| 2026-06-19 | Report body is always Spanish; UI language affects only the chat chrome | The IVO report structure/headings are Spanish; following UI lang for prose produced a half-English report | Fully bilingual report (rejected now: large effort to translate the whole structure) |
| 2026-06-19 | Enlarge `.inline-action` to match the tuner buttons | Owner wanted the prominent CTA look instead of thin pills | — |
