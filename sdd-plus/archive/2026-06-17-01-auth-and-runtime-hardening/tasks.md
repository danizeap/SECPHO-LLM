# Tasks

## Change

01-auth-and-runtime-hardening

## Implementation

- [x] Make `Handler.session()` open-mode return role `"user"` instead of a synthetic admin.
- [x] Add `ADMIN_ENABLED = bool(ADMIN_PASSWORD)` and require it in `is_admin()` to double-gate admin endpoints.
- [x] Add `_load_or_create_session_secret()` (env first, else persisted `data/app_state/.session_secret`) and `SESSION_SECRET_FROM_ENV`.
- [x] Add `to_int(value, default)` and apply it to `?id=`/payload id parsing in `/api/person`, `/api/llm-report`, `/api/llm-chat`, `/api/chat-flow`, `/api/rerank`, `/api/report-tuned`, returning 400 on bad ids.
- [x] Add `STATE_LOCK` and wrap `save_feedback`, `save_missing_tool_request`, `update_tool_request_status`, `save_generated_tools_registry`, `append_tool_build_event`.
- [x] Emit `send_security_headers()` + `Content-Length: 0` on the `do_GET` and `do_POST` 404 branches.
- [x] Change `OPENAI_MODEL` to `os.getenv("OPENAI_MODEL") or "gpt-5-mini"` and add `current_model()`.
- [x] Add `ensure_state_dirs()` and call it at import and in `main()`.
- [x] Add the `main()` startup banner (model, LLM key, auth + admin-password state, session-secret warning).
- [x] Run verification (py_compile + live HTTP checks + independent verifier review).
