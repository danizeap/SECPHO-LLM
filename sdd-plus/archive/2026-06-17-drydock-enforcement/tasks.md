# Tasks

## Change

drydock-enforcement

## Implementation

- [x] Write `require_active_change.py` mirroring the plugin hook contract (stdin JSON, exit 2 = block).
- [x] Guard `backend_api/`, `recommendation_engine/`, `report_engine/`, `scripts/` only.
- [x] Confirm a real drydock root; fail open on misdetected root / malformed input.
- [x] Wire into `.claude/settings.json` (PreToolUse, `Write|Edit|MultiEdit`).
- [x] Test: block (no active), allow (active), allow (non-source), fail-open (bad root/input).
