# Verification

## Change

ui-language-buttons

## Automated Checks

- [x] `ast.parse` + `-W error::DeprecationWarning` → clean.
- [x] esprima parses the chat inline `<script>`.
- [x] Full suite: 33 passed.
- [x] Label render: `markdown_to_chat_html('[tune][report][person]')` → es: "Ajustar ponderación e
      informe / Descargar informe (.docx) / seleccionar"; en: "Adjust weighting & report / Download
      report (.docx) / select".
- [x] Report stays Spanish in EN UI: `build_report_model('person', …, lang='en')` weighting note is
      Spanish ("Ordenado con una ponderación personalizada…").

## Manual Checks

- [ ] OWNER live glance: the in-chat buttons are the bigger CTA style; in a Spanish session no
      English appears in the buttons or the answer badge; the report reads fully in Spanish.

## Documentation Updates

- [x] No spec change needed: presentational + i18n consistency, no capability requirement change.
- [x] README / project context: no change.

## Result

PASS (static + suite + render checks green). One open item: Owner live glance.
