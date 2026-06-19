# Tasks

## Change

ui-language-buttons

## Implementation

- [x] Enlarge `.inline-action` to match the tuner buttons.
- [x] Localize the `markdown_to_chat_html` token button labels via `current_lang()`.
- [x] Localize the chat per-answer badge (drop English model id/kind).
- [x] Force the report body to Spanish (`report_lang="es"` in `build_report_model`).
- [x] Verification: AST/escape, esprima, full suite (33), label render check es/en, report-Spanish check.
- [ ] Owner live glance: buttons look like the tuner CTAs; no English text in a Spanish session.
