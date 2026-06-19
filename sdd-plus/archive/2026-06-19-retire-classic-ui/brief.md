# Brief

## Change

retire-classic-ui

## User Need

Remove the dead pre-redesign interface so the codebase has one chat surface and less attack/
confusion surface. Flagged by the verifier during the unified-report close-out.

## Problem

`/classic` (INDEX_HTML) is an older authenticated interface, not linked anywhere, fully
superseded by the main chat at `/`. It carried its own GET endpoints (`/api/llm-report`,
`/api/chat`, `/api/llm-chat`, plus the already-orphaned `/api/chat-flow`).

## Scope

In scope:
- Remove `INDEX_HTML` and the `/classic` route.
- Remove the `/classic`-only GET endpoints (`/api/llm-report`, `/api/chat`, `/api/llm-chat`,
  `/api/chat-flow`).
- Remove any function that becomes genuinely unreferenced as a result (conservative: only names
  that appear exactly once). Result: only `hash_password` (a dead leftover) was removable.

Out of scope / NOT removed:
- `llm_report_for_person`, `llm_payload_for_person`, `answer_question`, `llm_answer_question`,
  `chat_flow` — these are STILL used by the live agent / `chat_flow` fallback, so they stay.
- The agent's inline report path still uses the old free-form `llm_report_for_person` — a SEPARATE,
  larger follow-up (migrate it to the unified report). See open follow-up.

## Acceptance Criteria

- [x] `/classic` returns 404; `INDEX_HTML` gone; the four `/classic`-only endpoints removed.
- [x] The main chat (`/`) and `/tuning` still work; the agent and `chat_flow` are intact.
- [x] No live function removed (conservative refcount rule); AST/escape clean, esprima JS valid,
      suite green (32; the only drop is INDEX_HTML's JS test case, gone with the page).

## Impact Areas

- Backend: removed INDEX_HTML, `/classic`, four GET endpoints, `hash_password`.
- Frontend: none (page was unlinked).
- Data model / AI: none (agent functions retained).
- API: removed four `/classic`-only endpoints (no other caller).
- Documentation: none needed.
- Operations/security: smaller surface; `/api/llm-report` etc. no longer exposed.

## Open Questions

- Follow-up: migrate the agent `generate_report` action + `chat_flow` report path off
  `llm_report_for_person` to the unified report, so EVERY in-chat report is the unified one and the
  last free-form path can be removed.
