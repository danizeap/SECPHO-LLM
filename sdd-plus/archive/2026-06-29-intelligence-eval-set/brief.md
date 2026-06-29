# Brief

## Change

intelligence-eval-set (P5, final slice). A testing/evaluation artifact — no product behavior change.

## User Need

After three P5 intelligence slices (financial, health/churn, network), SECPHO needs confidence the
whole P4+P5 surface holds together: the access model is correct, the intelligence tools compose for
mixed-concept questions, and the agent doesn't hallucinate figures or leak gated data. This is the
combined test the Owner banked.

## Problem

The slices were each verified in isolation. There was no single guardrail over the WHOLE access model
(one tool→grant snapshot), no automated proof the per-socio intelligence tools compose, and no curated
mixed-concept stress set for the live run.

## Scope

In scope:

- Automated guardrail `tests/test_eval_set.py`: the full tool→grant gating-matrix snapshot (drift
  forces review), cross-concept composition (the intelligence tools key on the same socio), and the
  fail-closed sensitive gates.
- A living eval-set document `sdd-plus/eval/p5-stress-questions.md`: mixed-concept stress questions +
  gating + no-hallucination checks for the live manual run (the combined P4+P5 test).

Out of scope:

- No new product behavior, tools, data, or gating changes.
- No LLM-driven automated eval harness (the LLM-reasoning checks are run live against the doc).

## Acceptance Criteria

- [x] The gating-matrix snapshot covers all 25 tools and matches `TOOL_REQUIRED_GRANT`.
- [x] Cross-concept composition test: socio_health + socio_financials + socio_network compose on one socio.
- [x] Sensitive tools refused fail-closed to a `data.socios`-only caller.
- [x] The stress-question document covers cross-concept, gating, no-hallucination, per-slice, P4 RBAC.
- [ ] Verify + archive at close-out.

## Impact Areas

- Backend: none (tests only).
- Frontend: none.
- Data model: none.
- API: none.
- AI/model behavior: none (documents + guards existing behavior).
- Documentation: new eval-set document; this packet.
- Operations/security: the gating-matrix snapshot guards the access model against silent drift.

## Open Questions

- None. (A future LLM-eval harness that auto-runs the stress questions is a possible enhancement.)
