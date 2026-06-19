# Plan

## Change

sidebar-declutter

## Approach

1. Remove the five `.side-block` cards from the chat `<aside>`; keep brand + "+ New conversation"
   + the conversation list.
2. Add a `.side-foot` footer pinned to the bottom (`margin-top:auto`) with a ⚙ Admin link
   (`/admin`) and Sign out (`/logout`).
3. CSS: replace `.side-block` with `.side-foot` / `.side-foot-link` (+ `.gear`).
4. i18n: add `admin_link` (Admin / Administración); remove the now-dead `block_*` keys from both
   the en and es dictionaries.

## Files Expected To Change

- `backend_api/mvp_web_app.py` (chat page markup + CSS + i18n only).

## Risks

- Breaking the inline JS string (the recurring `"""`-escaping trap) → mitigated: esprima test +
  AST/escape check both run green.
- Orphaning /tuning → mitigated: reachable via the in-chat tuner; page itself unchanged.

## Rollback

Single-file, additive/subtractive markup+CSS+i18n. Revert the `mvp_web_app.py` chat-page hunk.
No data or API change.
