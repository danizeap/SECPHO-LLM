# Tasks

## Change

financial-turnover-robust-stat

## Implementation

- [x] Confirm scope and standards (STANDARD: bounded deterministic-output fix in a known function).
- [x] Update tests: amend the exact-overview assertion; add `test_turnover_robust_to_outliers`
      (injects a €100B-style outlier, asserts no `total_turnover`, sane median, max surfaces it).
- [x] Implement the smallest coherent change (`financial_overview` turnover block).
- [x] Update spec (agentic-conversation delta: robust-turnover scenario).
- [x] Run verification: `pytest tests/` — 163 passed.
