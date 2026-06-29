# Tasks

## Change

intelligence-eval-set (P5, final slice). Testing/evaluation artifact — no product behavior change.

## Implementation

- [x] **Automated guardrail** `tests/test_eval_set.py` (4 tests): full tool→grant gating-matrix
      snapshot (25 tools); every schema tool gated; sensitive (financial/churn) tools refused
      fail-closed to a `data.socios`-only caller; cross-concept composition (socio_health +
      socio_financials + socio_network compose on one socio). Suite 151.
- [x] **Living eval set** `sdd-plus/eval/p5-stress-questions.md`: mixed-concept stress questions +
      gating + no-hallucination + per-slice + P4 RBAC checks, with reference numbers, for the live run.
- [x] No product behavior / spec change (documents + guards existing behavior).
- [x] Run verification + archive.

## Verification

- [x] `python scripts/sdd.py verify intelligence-eval-set` ✓; 151 tests green; evidence in
      `verification.md`. Test artifact — no adversarial review needed (no new product/attack surface).
