# Verification

## Change

chat-history-isolation

## Automated Checks

- [x] `python -m pytest tests/test_chat_history_isolation.py tests/test_inline_js_syntax.py` — 16 passed.
  - `_user_tag`: stable + case-insensitive, per-user-distinct, 16 hex chars, opaque (no email),
    keyed by SESSION_SECRET (changes when the secret rotates → not a bare enumerable hash), `anon` on empty.
  - `_history_tag`: named (roster) account → stable per user, nonce-independent; shared-password
    (USERS empty) → bound to the per-login nonce so the SAME self-asserted email across two logins
    yields DIFFERENT tags (not forgeable); `anon` when no nonce.
  - `CHAT_HTML` contains the `{{UID}}` placeholder, the `secpho-uid` meta, `purgeIfDifferentUser`,
    `removeItem(CONV_KEY)`, `UID_KEY`, and the `saveActive` multi-tab guard.
  - Over real HTTP: the served `/` page embeds the caller's own tag, never the literal `{{UID}}`,
    never another user's tag; two named users receive different pages; in shared-password mode two
    logins typing the same email receive different pages.
- [x] `python -m pytest tests/` — 162 passed (no regression; +11 from this change).
- [x] Inline-JS esprima guard passes — the JS edits did not trip the escaping trap.

## Independent Review

- [x] **drydock verifier — VERIFIED.** All 6 original edits present/correct; both test commands
      independently re-run and pass; `purgeIfDifferentUser` provably runs before any history load;
      email never reaches the DOM or localStorage. Only open item: post-deploy manual two-user check.
- [x] **Adversarial security review (4 lenses).** Injection + crypto lenses: HOLDS (hex-only tag, no
      XSS; HMAC keyed by SESSION_SECRET, non-enumerable, collision-negligible). Found 1 HIGH
      (shared-password mode: self-asserted email made the tag forgeable — reachable ONLY when USERS
      is empty, so the named-account production was never exposed) and 1 INFO (concurrent multi-tab
      re-stamp). Both FIXED (`_history_tag` binds to the per-login nonce off-roster; `saveActive`
      aborts on owner-tag mismatch) and covered by new regression tests.

## Manual Checks

- [ ] Deploy; in one browser log in as user A, hold a financial conversation, log out.
- [ ] Log in as a limited user B in the SAME browser → history pane is EMPTY (no A content); ask a
      financial question → still refused by the live gate.
- [ ] Log back in as A → A's own history is gone (purged on B's load) — acceptable per decision log.
- [ ] (Hardening) confirm no `secpho_convs`/`secpho_active` value contains a plaintext email.

## Documentation Updates

- [x] Specs updated: access-control delta requirement (conversation-history isolation + scenarios).
- [x] No README/user-facing doc change needed. Reason: internal security hardening, no new user workflow.
- [ ] Project context: no change needed.

## Result

Implementation + automated verification COMPLETE (162 passed). Independent verifier: VERIFIED.
Adversarial review (4 lenses): the named-account production path was never exposed; the one HIGH
(shared-password fallback) and one INFO (multi-tab) it surfaced are both fixed and regression-tested.
Pending only: Owner approval, then deploy + the post-deploy two-user manual check.
