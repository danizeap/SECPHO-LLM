# Verification

## Change

unified-report

## Automated Checks

- [x] `ast.parse` + `-W error::DeprecationWarning` on mvp_web_app.py → clean (no invalid escapes).
- [x] esprima parses all served-page inline JS (`tests/test_inline_js_syntax.py`).
- [x] Full suite: `python -m pytest tests/` → 33 passed (hermetic; report API tests unset the API key).
- [x] NEW `tests/test_unified_report.py`: html==docx (person, company, with-prose), injected-order
      honored, privacy allowlist (no children/gender/food in the model), escaped HTML fragment,
      weighting-note presence.
- [x] NEW `tests/test_report_api.py` cases: `/api/report-tuned` returns a safe `<div class="rep">`
      fragment; tuned `POST /api/report {weights}` returns a valid `.docx`.
- [x] Consistency (#14): `build_person_report(mid).contacts` == `get_recommendations(mid,5)` for
      members 74638 and 74663 (same matcher file, same order).

## Manual Checks

- [x] LIVE end-to-end against a real flagship key (in this environment):
      `/api/report-tuned` generated a Resumen ejecutivo + per-contact rationale (rep-why), and the
      subsequent `POST /api/report` download was byte-identical in content to the preview (76/76 lines)
      via the prose cache — chat == download WITH the LLM narrative. mode_label: "La matemática decide
      · el LLM explica · informe".
- [ ] OWNER live browser test on the Render deploy: open the tuner, generate a report, read the
      "why this is a good match" paragraphs, download, confirm the .docx matches what's on screen
      (flagship requires a valid `OPENAI_MODEL_FLAGSHIP` + key in production; without them the report
      still renders complete, just without the narrative).

## Documentation Updates

- [x] Specs updated: report-generation delta (one model/two renderers, math-fixes-numbers/LLM-prose,
      report==chat, governance).
- [x] README / user docs: no change needed (no setup/CLI change; same endpoints).
- [x] Project context: no change needed.

## Result

PASS (static + hermetic suite + live flagship end-to-end all green). One open item delegated to the
Owner: the live browser read-through on the deploy. Dead free-form-report code removed.
