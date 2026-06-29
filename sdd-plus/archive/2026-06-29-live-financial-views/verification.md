# Verification

## Change

live-financial-views (P5, slice 1)

## Automated Checks

- [x] Full suite green: `python -m pytest -q` → **128 passed**. New: `test_financial_normalizers.py`
      (7) + `test_financial_tools.py` (11, incl. exact aggregates + fail-closed gating + multi-value
      `Estado`).
- [x] `python scripts/sdd.py verify live-financial-views` → artifacts verified.
- [x] Secret sweep: WP token literal absent from the tree; financial values never logged.

## Manual Checks

- [x] **Verifier subagent (independent):** PASS WITH CONCERNS → 128/128; all five priority claims
      confirmed against the code (4 tools fail-closed under `data.financiero`; euros computed in
      pandas; Estado-derived status with Cancelada excluded and outstanding = Vencida+Enviada;
      "No consta" = active; change-feed omits sensitive key samples). Its one substantive concern —
      a multi-value `Estado` could silently drop from totals via `_inv_status` — was FIXED (priority
      substring matching + regression test `test_inv_status_handles_multivalue`).
- [x] **Adversarial security review (workflow):** 5 financial-risk dimensions (authorization-leak,
      hallucination/math, PII-in-output, fail-open/injection, zero-copy/logging), each finding
      adversarially re-verified → **0 confirmed findings**.
- [~] **LaunchGuardian local scan:** gitleaks 0, trivy 0, api_surface 0, frontend_exposure 0, 0
      blockers. Status INCOMPLETE only because semgrep cannot run on native Windows (`socketpair`);
      run on Linux/CI for the SAST gate.
- [x] **Live proof (shapes/coverage only, no values):** 195/318/4779/171 rows; 4779/4779 amounts
      parse; overdue count = `Estado=Vencida`; year-2025 invoices = 454; 140 active / 178 left after
      the `"No consta"` fix.

## Documentation Updates

- [x] Delta specs synced into living capabilities: `live-data-platform.md` (financial sources +
      sensitive change-feed gating), `agentic-conversation.md` (financial tools), `access-control.md`
      (`data.financiero` gates the financial tools).
- [x] Decision log records the schema-probe approach, source choices, status semantics, the
      `"No consta"` fix, deterministic-math rule, and gating.
- [ ] No README/PROJECT_CONTEXT change required beyond the specs.

## Result

PASS — 128 tests green; verifier PASS (concern fixed); adversarial review 0 findings; no secrets/PII
in financial outputs; zero-copy holds. Going-LIVE prerequisite (already met): `SECPHO_LIVE_DATA` +
token on Render. Follow-up: run LaunchGuardian once on Linux/CI for the semgrep SAST gate.
