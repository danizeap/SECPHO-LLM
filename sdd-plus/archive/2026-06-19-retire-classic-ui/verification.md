# Verification

## Change

retire-classic-ui

## Automated Checks

- [x] `ast.parse` + `-W error::DeprecationWarning` → clean.
- [x] esprima parses the chat inline `<script>`.
- [x] Full suite: 32 passed (was 33; the only delta is the auto-discovered INDEX_HTML JS test case,
      removed with the page — no assertion lost).
- [x] Boot check (server in-thread, logged in): `GET /` → 200 (main chat), `GET /classic` → 404,
      `GET /tuning` → 200. `hasattr(app, 'INDEX_HTML')` → False.
- [x] Conservative removal proof: only functions whose name appeared exactly once were dropped
      (`hash_password`). The agent's report/answer functions (`llm_report_for_person`,
      `llm_answer_question`, `answer_question`, `chat_flow`) have refcount > 1 and were retained.

## Manual Checks

- [ ] Owner glance (optional): nothing user-visible changes; `/classic` was unlinked.

## Documentation Updates

- [x] No spec change needed: removal of a deprecated, unspecified legacy surface; no capability
      requirement changes.

## Result

PASS (static + suite + runtime route checks green; verifier subagent reviewed). Follow-up logged:
migrate the agent's inline report off `llm_report_for_person` to the unified report.
