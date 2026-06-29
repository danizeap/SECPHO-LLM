# Tasks

## Change

chat-history-isolation

## Implementation

- [x] Confirm scope and standards (FULL-tier: sensitive-data isolation under RBAC).
- [x] Add tests: `tests/test_chat_history_isolation.py` (helper opacity/stability/keying, page
      injection, per-user HTTP differentiation) + esprima guard still passes.
- [x] Implement the smallest coherent change (`_user_tag`, `/` injection, meta tag, client
      purge-on-mismatch, logout clear).
- [x] Update specs (access-control delta requirement) and decision log.
- [x] Run verification: full hermetic suite (157 passed) + inline-JS guard.
- [x] Verifier subagent review — VERIFIED (6 edits present/correct, 157→162 tests pass, purge runs
      before any load, email never reaches DOM/localStorage).
- [x] Adversarial security review (4 lenses) — found 1 HIGH (shared-password forgeable tag; not
      reachable in named-account prod) + 1 INFO (multi-tab); both fixed (`_history_tag` + `saveActive`
      guard) and covered by regression tests. Injection + crypto lenses: holds.
- [ ] Owner approval, then deploy + manual two-user check.
