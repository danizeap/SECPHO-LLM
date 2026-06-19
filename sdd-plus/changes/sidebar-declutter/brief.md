# Brief

## Change

sidebar-declutter

## User Need

The chat's left sidebar carried five static explainer/blurb cards (Model rule, SECPHO
voice, Try, Scoring console, Admin console). The Owner found them not useful and cluttered,
and wanted Admin reduced to a small settings control at the bottom.

## Problem

The blurbs pushed the conversation list down and added noise; Admin was a verbose card
rather than an unobtrusive control.

## Scope

In scope (Owner-chosen Option B):
- Remove the Model rule / SECPHO voice / Try explainer cards and the Scoring console blurb.
- Move Admin into a small ⚙ settings link pinned at the bottom of the left column, with Sign out.
- Scoring console (/tuning) reached via the in-chat "Adjust weighting" tuner; the standalone page
  stays but is unlinked from the sidebar.

Out of scope:
- Removing the /tuning or /admin pages themselves (only the sidebar blurbs/links change).
- Any backend/API/auth change.

## Acceptance Criteria

- [x] The five side-block cards are gone from the chat sidebar.
- [x] A ⚙ Admin link and Sign out sit pinned at the bottom of the left column.
- [x] The conversation list still renders above the footer.
- [x] App parses, chat JS still valid (esprima), full suite green.

## Impact Areas

- Backend: none.
- Frontend: chat `<aside>` markup, `.side-foot` CSS, removed `.side-block` CSS, removed dead i18n keys.
- Data model / API / AI: none.
- Documentation: none needed (presentational; bilingual coverage preserved — admin_link added in both langs).
- Operations/security: none (links unchanged; /admin still admin-gated server-side).

## Open Questions

- None. Owner confirmed Option B.
