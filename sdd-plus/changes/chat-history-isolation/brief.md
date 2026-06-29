# Brief

## Change

chat-history-isolation

## User Need

A staff member who logs into the chat must never see another user's prior conversation. With RBAC
(P4), different roles (dev/admin/user) can share a browser; conversation history must respect the
same access boundary as the live tools.

## Problem

Conversation history is stored in browser `localStorage` under two GLOBAL keys (`secpho_convs`,
`secpho_active`) that are not namespaced by user and never cleared on login/logout/user-change
(`initConversations` restores `secpho_active` regardless of who is logged in). Conversation history
predates P4 multi-user RBAC and assumed one user per browser. Effect (live-test finding #7): in the
same browser, a `user` inherits a dev/admin's prior conversation — euros, churn reasons, PII —
bypassing the RBAC gates for data-at-rest. Bounded to the same browser/device (localStorage is
per-origin) — not a remote leak — but a must-fix before real staff get accounts on shared machines.

## Scope

In scope:

- Inject an opaque, per-user tag into the served chat page (hash of the session email, keyed by
  SESSION_SECRET; never the email itself).
- Client clears (`removeItem`) `secpho_convs`/`secpho_active` whenever the stored owner tag differs
  from the logged-in user, before any history loads; clears on logout for hygiene.
- One-time migration: the legacy un-tagged keys are purged on the first post-deploy load.

Out of scope:

- Server-side conversation persistence (history stays client-only, by design — zero-persistence).
- Encrypting localStorage / defending a user against themselves on their own device.
- The other live-test findings (#1/#3/#5/#6 stats, #2 tool, #4 network) — separate changes.

## Acceptance Criteria

- [x] `_user_tag` is opaque (no email), stable per user, keyed by SESSION_SECRET (not enumerable).
- [x] The served chat page embeds the caller's tag and never the literal `{{UID}}`.
- [x] Two different users receive different tags in their served page.
- [x] Client purges history when the owner tag changes (cleared, not hidden) before loading.
- [x] Inline-JS esprima guard still passes (no escaping-trap regression).
- [ ] Manual: User B logging in on User A's browser lands on empty history; A keeps theirs on return.

## Impact Areas

- Backend: `_user_tag` helper; `/` handler injects the tag into `CHAT_HTML`.
- Frontend: `CHAT_HTML` meta tag + conversation-history JS (purge-on-mismatch, logout clear).
- Data model: none.
- API: none (no new endpoint; tag rides on the existing page).
- AI/model behavior: none.
- Documentation: access-control capability delta spec.
- Operations/security: closes the data-at-rest RBAC bypass; existing local history is wiped once on upgrade.

## Open Questions

- None blocking. (Logout clear only fires from the chat page's link; the mismatch-purge is the
  real guarantee and covers logout-from-admin/tuning on the next login.)
