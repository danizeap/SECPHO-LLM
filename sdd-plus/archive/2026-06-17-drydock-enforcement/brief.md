# Brief

## Change

drydock-enforcement

## User Need

The owner requires that EVERY change to this project goes through the SDD+/Drydock
lifecycle, no exceptions. During the demo crunch the lifecycle lapsed (code shipped,
packets reconstructed after the fact) because nothing technically prevents editing
product source without an open change. Make the protocol non-optional at the tool level.

## Problem

Drydock's plugin hooks enforce only two guardrails (secret-file edits via
`protect_secrets.py`, destructive git via `git_safety.py`). The lifecycle itself
("open a change before you touch code") is **advisory** — instructions in
`CLAUDE.md`/`AGENTS.md` that depend on the agent choosing to comply. So product
source can be edited with zero open change packets, which is exactly what happened.

## Scope

In scope:

- A PreToolUse hook that blocks `Write`/`Edit`/`MultiEdit` to product-source dirs
  (`backend_api/`, `recommendation_engine/`, `report_engine/`, `scripts/`) when there
  is no active change packet under `sdd-plus/changes/`.
- Wire it into `.claude/settings.json` (composes with the plugin's secret/git hooks).
- Fail OPEN on any error or misdetected root so a hook bug never bricks work.

Out of scope:

- Binding an edit to a *specific* change (this enforces that *an* active change exists).
  Future enhancement.
- Changing the Drydock plugin's own hooks.

## Acceptance Criteria

- [x] Editing product source with **no** active change is blocked with a clear message.
- [x] Editing product source with an active change is allowed.
- [x] Editing non-source (docs, `sdd-plus/`, `.claude/`, README) is always allowed.
- [x] Malformed input or a misdetected root fails open (allow), never blocks.

## Impact Areas

- Backend: none (no product code change)
- Operations/security: new PreToolUse hook + `.claude/settings.json`
- Documentation: this packet

## Open Questions

- None.
