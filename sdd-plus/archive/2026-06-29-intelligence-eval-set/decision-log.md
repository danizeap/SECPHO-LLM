# Decision Log

## Change

intelligence-eval-set

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-29 | The eval set = an automated hermetic guardrail (gating-matrix snapshot + cross-concept composition + fail-closed gates) PLUS a living stress-question document for the live run. | The deterministic surface is testable hermetically; the LLM-reasoning/grounding part can only be evaluated against the real agent, so it's a curated question bank (which doubles as the Owner's banked combined P4+P5 test). | A full LLM-eval harness that auto-runs the questions (deferred — needs the API + recorded expectations); a doc only (rejected — misses the access-model snapshot guard). |
| 2026-06-29 | The gating matrix is asserted as full snapshot equality, intentionally brittle. | Any new tool or changed gate fails the test, forcing a deliberate access-model review + snapshot update — exactly what guards a permission model. | A loose "every tool has some grant" check only (rejected — wouldn't catch a tool gated at the WRONG tier). |
