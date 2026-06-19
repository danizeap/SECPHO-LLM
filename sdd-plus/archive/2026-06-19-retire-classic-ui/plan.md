# Plan

## Change

retire-classic-ui

## Approach

1. Remove the `INDEX_HTML` assignment (AST node) and the `/classic` GET route.
2. Remove the `/classic`-only GET handlers by `if parsed.path == "…"` block: `/api/llm-report`,
   `/api/chat`, `/api/llm-chat`, `/api/chat-flow`.
3. Iteratively remove module-level functions whose name appears exactly once (def only) — a
   conservative rule that can only remove truly-unreferenced functions. Live functions the agent
   still uses (refcount > 1) are protected automatically.
4. Verify the app boots, `/` and `/tuning` still serve, `/classic` 404s, agent intact.

## Files Expected To Change

- `backend_api/mvp_web_app.py` (deletions only).

## Risks

- Removing a still-used function → mitigated by the refcount==1 rule (only `hash_password` qualified)
  and a runtime boot check (main chat 200, agent intact).
- Removing a shared endpoint → mitigated: `/api/search` (shared with /tuning) was explicitly kept.

## Rollback

`git revert` the single-file deletion commit. No data/migration.
