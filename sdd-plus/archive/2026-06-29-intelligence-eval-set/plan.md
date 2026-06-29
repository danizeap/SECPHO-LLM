# Plan

## Change

intelligence-eval-set (P5, final slice). Testing/evaluation artifact.

## Approach

- Add `tests/test_eval_set.py` (hermetic): a tool→grant gating-matrix snapshot, a cross-concept
  composition test (the same socio across actividades/cuotas/invoices/proyectos → the per-socio tools
  compose), and a fail-closed sensitive-gate check.
- Add `sdd-plus/eval/p5-stress-questions.md`: the living mixed-concept stress-question set (the
  combined P4+P5 manual test), grouped into cross-concept / gating / no-hallucination / per-slice /
  P4 RBAC, with concrete expected behaviour and reference numbers.

## Files Expected To Change

- `tests/test_eval_set.py` — NEW (4 tests).
- `sdd-plus/eval/p5-stress-questions.md` — NEW (the living eval set).

## Risks

- The gating-matrix snapshot is intentionally brittle: adding/changing a tool's gate fails the test,
  forcing a deliberate review + snapshot update. That is the point, not a defect.
- No risk to product behavior (tests + doc only).

## Rollback

Reverting the commit removes the tests + the doc; no behavior depends on them. Nothing to undo.
