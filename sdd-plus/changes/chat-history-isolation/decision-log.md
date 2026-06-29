# Decision Log

## Change

chat-history-isolation

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-29 | Tag is a keyed hash of the email, not the email | Never write PII (the email) into the DOM or localStorage; keying by SESSION_SECRET prevents cross-account enumeration | Plain `sha256(email)` (enumerable from a known email); raw email (leaks PII to storage) |
| 2026-06-29 | Purge (`removeItem`), don't just hide, on user mismatch | The carried-over content is sensitive (euros/PII); hiding leaves it recoverable in storage | Namespace keys per user but leave old data in place (still recoverable); server-side history (breaks zero-persistence) |
| 2026-06-29 | Mismatch-purge at load is the guarantee; logout clear is bonus | Covers the real threat (different user logs in) regardless of how the prior session ended; logout-from-admin/tuning has no chat JS to clear | Rely on logout clear alone (misses crash/closed-tab/other-page logout) |
| 2026-06-29 | Single global keys + `secpho_uid` marker, not per-uid namespacing | Minimal edit surface → lower risk against the inline-JS escaping trap; same security outcome (only the current user's history is ever present) | Namespacing every key (`secpho_convs_<uid>`) — more edit points, same result |
| 2026-06-29 | History stays client-only | Owner mandate: zero-persistence, not a data custodian; the leak is local cross-account, fixable client-side | Move history server-side keyed by user (rejected — persistence) |
| 2026-06-29 | Tag binds to the per-login nonce when the email isn't a roster account (`_history_tag`) | Adversarial review (HIGH): in shared-password mode the login email is self-asserted, so an email-only tag is forgeable across accounts. Reachable only when USERS is empty (named-account mode disables shared-password login), so the live deployment was never exposed; fixed for robustness | Tag by email only (forgeable in shared-password mode); document shared-password as out-of-scope (rejected — don't ship a known hole) |
| 2026-06-29 | `saveActive()` aborts on owner-tag mismatch (multi-tab guard) | Adversarial review (INFO): two users in concurrent tabs could let a stale tab re-stamp its conversation under the new user's namespace | Leave multi-tab out of scope (rejected — cheap to close) |
