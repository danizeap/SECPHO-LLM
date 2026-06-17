# Plan

## Change

drydock-enforcement

## Approach

1. `.claude/hooks/require_active_change.py` — read the tool-call JSON from stdin
   (mirrors the plugin hook contract: exit 2 blocks with stderr as the reason, exit 0
   allows). If `file_path` is under a guarded source dir AND `sdd-plus/changes/` has no
   packet (a dir containing `brief.md`), exit 2; else exit 0. Confirm a real drydock
   root (`sdd-plus/` exists under the resolved cwd) before assessing — otherwise fail
   open. Wrap everything so any exception returns 0.
2. `.claude/settings.json` — register the hook as a PreToolUse matcher on
   `Write|Edit|MultiEdit`, invoked via
   `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/require_active_change.py"`.

## Files Expected To Change

- `.claude/hooks/require_active_change.py` (new)
- `.claude/settings.json` (new)

## Risks

- A blocking governance hook could disrupt flow if mis-scoped → mitigated by guarding
  only product-source dirs and failing open on any error / unknown root.
- Enforces "an active change exists", not file-to-change binding (accepted; it backstops
  the real failure mode of editing source with zero packets).

## Rollback

Remove the PreToolUse block from `.claude/settings.json` (or delete the hook file). No
product code is affected.
