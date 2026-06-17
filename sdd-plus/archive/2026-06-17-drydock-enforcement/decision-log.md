# Decision Log

## Change

drydock-enforcement

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-17 | Block source edits when NO active change packet exists (not warn-only) | Owner wants Drydock non-optional; a hard block at the tool level is the only thing that actually prevents code-before-packet | Warn-only (rejected: advisory is precisely what failed this session); per-file change binding (deferred: more complex; the presence check already kills the real failure mode) |
| 2026-06-17 | Guard only product-source dirs (`backend_api`, `recommendation_engine`, `report_engine`, `scripts`) | Docs, specs, `sdd-plus/`, `.claude/`, and config must stay editable — including the change packets themselves — or the lifecycle can't function | Guard the whole repo (rejected: would block writing the very packets that satisfy the rule) |
| 2026-06-17 | Fail OPEN on errors / misdetected root | A buggy governance hook must never brick legitimate work; security fail-closed is already covered by `protect_secrets.py` / `git_safety.py` | Fail closed (rejected: too risky for a self-imposed process guardrail) |
