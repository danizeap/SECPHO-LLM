# Plan

## Change

chat-history-isolation

## Approach

1. **Server — opaque per-user tag.** Add `_user_tag(email)`: lowercases/strips the email, returns
   `"anon"` when empty, else `hmac(SESSION_SECRET, email, sha256)[:16]`. Keyed by the session secret
   so the tag cannot be enumerated from a known email and never carries the email itself.
2. **Server — inject on serve.** The `/` handler replaces a `{{UID}}` placeholder in `CHAT_HTML`
   with `_history_tag(session)` (mirrors the existing `LOGIN_HTML.replace("{{ERROR}}", …)`).
   `_history_tag` returns `_user_tag(email)` for a roster-validated named account (stable per user),
   else `_user_tag("session:" + role + ":" + nonce)` — bound to the per-login nonce so a
   self-asserted email in shared-password mode cannot forge another user's namespace.
3. **Page — carry the tag.** A `<meta name="secpho-uid" content="{{UID}}">` in the chat `<head>`.
4. **Client — read + purge.** Read the tag into `CONV_UID`. `purgeIfDifferentUser()` runs first in
   `initConversations()`: if `localStorage[UID_KEY] !== CONV_UID`, `removeItem` the conversation
   keys (clears, not hides) and record the new owner. This also wipes the legacy un-tagged keys on
   first post-deploy load.
5. **Client — logout hygiene.** The chat page's `/logout` link clears the keys on click.
6. **Client — multi-tab guard.** `saveActive()` aborts when `localStorage[UID_KEY]` no longer matches
   this tab's `CONV_UID` (another tab switched user), so a stale tab can't re-stamp its conversation
   under the new user's namespace.

## Files Expected To Change

- `backend_api/mvp_web_app.py` — `_user_tag` helper, `/` handler injection, `CHAT_HTML` meta +
  conversation-history JS (`CONV_UID`, `UID_KEY`, `purgeIfDifferentUser`, logout clear).
- `tests/test_chat_history_isolation.py` — new hermetic test (helper + page wiring + per-user HTTP).
- `sdd-plus/changes/chat-history-isolation/specs/access-control.md` — delta requirement.

## Risks

- **Inline-JS escaping trap** (history: a stray `\'` has killed the whole `<script>` twice). Mitigated:
  edits use data-attr/meta reads + simple single-quoted strings, no backslash escapes; the esprima
  guard (`test_inline_js_syntax.py`) gates it.
- **Existing local history wiped once on upgrade** (the legacy keys are un-tagged → first load purges
  them). Acceptable: it's client-side convenience data, and clearing it is the safe direction.
- **Shared-password / anon mode** — the login email is self-asserted there (not roster-validated), so
  `_history_tag` binds the tag to the per-login `nonce` rather than the email: every login gets a
  fresh namespace, so a user cannot type a privileged user's email to forge their tag (adversarial
  review HIGH, now closed). Reachable only when `USERS` is empty — in named-account mode the
  shared-password login path is dead (`check_credentials` returns None), so the live deployment was
  never exposed. Auth-disabled / no-nonce sessions fall back to `"anon"` (no RBAC, no sensitive data).

## Rollback

Pure code; no migration, no schema, no env. Revert the commit (or the six edits) and redeploy — the
client falls back to the global keys. Disabling needs no flag.
