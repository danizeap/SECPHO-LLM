# Tasks

## Change

agent-report-unified

## Implementation

- [x] Map the report paths: confirmed the agent has no generate_report tool; free-form only in
      `tool_answer` + `chat_flow` heuristic sites.
- [x] Add `unified_report_chat_response`; migrate both heuristic sites.
- [x] Pass `answer_html` through in both `/api/agent` response builders.
- [x] Remove the now-dead `llm_report_for_person`; keep `llm_payload_for_person`.
- [x] Tests: `tests/test_chat_report_unified.py` (hermetic) — chat report == unified report; helper
      returns HTML; free-form function gone.
- [x] Verify: AST/escape, esprima chat JS, full suite (35), live check (chat report = unified HTML
      with download button), durations check (no real LLM calls).
- [x] Docs: agentic-conversation delta spec.
- [ ] Owner live glance: ask the chat "dame el informe de X" → unified report + download button.
