# Plan

## Change

agent-report-unified

## Approach

1. Add `unified_report_chat_response(member_id)` next to `build_report_model`: build the unified
   model (Spanish body), `render_html_of` it, append a `.rep-download` button (data-id, weights=null
   → default report), return `{answer (title), answer_html, kind:"report", selected_member_id,
   llm_available}`; return None if the member can't be built (caller falls through).
2. `tool_answer` `generate_report` action → `return unified_report_chat_response(member_id)`.
3. `chat_flow` `report_intent` path → call the helper; return it if non-None.
4. `/api/agent`: both response builders use `result.get("answer_html") or
   markdown_to_chat_html(result["answer"])` so a pre-rendered report HTML is sent as-is.
5. Remove `llm_report_for_person` (now unreferenced); keep `llm_payload_for_person` (used by recs).
6. Test: `tests/test_chat_report_unified.py` (hermetic — sets OPENAI_API_KEY="" BEFORE import so
   load_dotenv can't restore it) asserts the chat report is the unified report and the free-form
   function is gone.

## Files Expected To Change

- `backend_api/mvp_web_app.py`; `tests/test_chat_report_unified.py` (new);
  `sdd-plus/changes/agent-report-unified/specs/agentic-conversation.md` (delta).

## Risks

- Double-escaping the report HTML → fixed by the `answer_html` passthrough.
- Latency: the fallback report now makes a flagship prose call → mitigated by the prose cache and
  deterministic fallback (no key / failure → complete report, no prose), 60s timeout under the proxy cutoff.
- Removing a still-used function → guarded by the refcount==1 rule (only `llm_report_for_person` qualified).

## Rollback

`git revert` the single-file change + test; restore `llm_report_for_person`. No data/API change.
