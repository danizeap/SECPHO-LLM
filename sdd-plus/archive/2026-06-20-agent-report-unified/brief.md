# Brief

## Change

agent-report-unified

## User Need

One report everywhere. Asking the chat "dame el informe de X" must produce the SAME unified
report as the tuner "Generar reporte" and the download — not a different, old free-form report.

## Problem

The chat's heuristic fallback still produced the old free-form `llm_report_for_person` report
(LLM writes the whole document; can truncate, retypes numbers, different structure). Two sites:
`tool_answer`'s `generate_report` action and `chat_flow`'s `report_intent` path. So a report
asked in chat differed from the tuner/download report.

## Scope

In scope:
- A helper `unified_report_chat_response(member_id)` that renders the unified report (HTML
  fragment via `render_html_of(build_report_model(...))`) plus a "Descargar .docx" button.
- Both heuristic report sites now call it.
- The `/api/agent` response builders pass `answer_html` through (so the report HTML isn't
  re-escaped as markdown).
- Remove the now-dead `llm_report_for_person` (the last free-form "LLM writes the report" path).

Out of scope:
- The agent (LLM) path already defers to the `[report]` token → unified download; unchanged.
- `llm_payload_for_person` stays (still used by recommendations).

## Acceptance Criteria

- [x] Chat report request → unified report HTML (`.rep`, "Informe de Valor y Oportunidades",
      Contactos recomendados, download button), not the old "Matchmaker Brief".
- [x] The report shown in chat carries a working "Descargar .docx" button.
- [x] `llm_report_for_person` no longer exists; `llm_payload_for_person` retained.
- [x] Deterministic without an API key (prose skipped); flagship prose when available.
- [x] AST/escape clean, esprima JS valid, suite green (35; +3 chat-report tests, hermetic).

## Impact Areas

- Backend: new helper; two heuristic sites migrated; two response builders pass `answer_html`
  through; `llm_report_for_person` removed.
- Frontend: none (reuses the existing `downloadReportFromBtn` + `.rep` styles).
- Data model / API: none (same `/api/agent` shape; `answer_html` already a field).
- AI/model behavior: the in-chat report is now deterministic structure + flagship prose (cached),
  never a free-form LLM document.
- Documentation: agentic-conversation delta (inline report == unified report).
- Operations/security: report HTML is server-rendered + escaped; no new PII surface.

## Open Questions

- None.
