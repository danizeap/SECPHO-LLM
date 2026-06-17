# Verification

## Change

drydock-enforcement

## Automated Checks

- [x] Hook unit test (simulated PreToolUse stdin), Windows-style paths:
  - product source + active change -> exit 0 (allow)
  - non-source (README, `sdd-plus/` doc) -> exit 0 (allow)
  - misdetected root (`/c/...` style) + malformed stdin -> exit 0 (fail open)
  - real root + NO active change -> exit 2 (block, with the guidance message)

## Manual Checks

- [x] Composes with the existing Drydock plugin hooks (`protect_secrets.py`, `git_safety.py`)
      as an additional PreToolUse entry in `.claude/settings.json`; does not replace them.

## Documentation Updates

- [x] No product capability spec affected (this is governance tooling, not a product capability) — no delta spec.
- [ ] No documentation update needed. Reason: enforcement behavior is captured in this packet.

## Result

PASS. The lifecycle is now enforced at the tool level: product source under the guarded
dirs cannot be edited with zero open change packets. Scope is "an active change exists"
(not per-file binding); fail-open keeps a hook bug from blocking legitimate work.
