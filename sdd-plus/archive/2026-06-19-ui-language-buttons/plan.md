# Plan

## Change

ui-language-buttons

## Approach

1. CSS: enlarge `.inline-action` (radius 8px, padding 8px 14px, min-height 36px, font-weight 600,
   margin for spacing, hover) so chat action buttons match the tuner buttons.
2. `markdown_to_chat_html`: compute labels from `current_lang()` and render the `[person]/[tune]/
   [report]/[report-socio]` buttons with localized text (the chat sends `lang`; `/api/agent` calls
   `set_request_lang` before rendering).
3. Chat mode-badge JS: render `t('llm_on')/t('llm_off')` only (drop the English model id + kind).
4. `build_report_model`: force `report_lang = "es"` for the weighting note and prose — the report is
   a Spanish deliverable; UI language affects only the chat chrome.

## Files Expected To Change

- `backend_api/mvp_web_app.py` (CSS + `markdown_to_chat_html` + chat badge JS + `build_report_model`).

## Risks

- Inline-JS `"""`-escaping trap → mitigated: esprima test + AST/escape check green.
- Forcing report Spanish could surprise an EN user → acceptable: the report structure is Spanish
  anyway; this removes a half-English render. Flagged to Owner.

## Rollback

Single-file; revert the four hunks. No data/API change.
