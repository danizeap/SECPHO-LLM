# Verification

## Change

health-churn-intelligence (P5, slice 2)

## Automated Checks

- [x] Full suite green: `python -m pytest -q` → **139 passed**. New: `tests/test_health_churn.py`
      (11: engagement recency/ranking, active-only filter, churn breakdown + tenure, two-tier gating,
      membership-vs-feed basis, prompt-contract).
- [x] `python scripts/sdd.py verify health-churn-intelligence` → artifacts verified.

## Manual Checks

- [x] **Verifier subagent (independent):** **VERIFIED** (no material discrepancies) → 137/137 at run
      time; gating fail-closed at both tiers; engagement + churn outputs deterministic and PII-minimal
      (no author/description, no email/NIF/phone, no `cuota_amount` in churn); `active_only` no-ops
      gracefully without cuotas; delta specs match.
- [x] **Adversarial security review (workflow):** 4 dimensions (churn-reason-leak, gating-fail-open,
      determinism-hallucination, PII-overexposure). **1 MEDIUM found + FIXED:** the anti-fabrication
      rule was euro-scoped, so the LLM could derive a churn rate from counts (wrong denominator). Fix:
      generalized the agent rule to forbid deriving ANY rate/percentage/ratio, and `health_overview`
      now returns a correctly-denominated `going_quiet_pct` over ACTIVE members (membership basis) +
      regression tests. Re-review clean.
- [~] **LaunchGuardian local scan:** gitleaks 0, trivy 0, api_surface 0, frontend_exposure 0, 0
      blockers. INCOMPLETE only for semgrep-on-Windows; run on Linux/CI for the SAST gate.
- [x] **Live proof (counts/aggregate only):** 317 socios with activity, 139 active / 178 quiet (≈ the
      140/178 membership split); `at_risk` active-only narrowed 178 → 11 actionable active members;
      `churn_breakdown` grouped the 178 leavers by reason (Económico 59 / No creen en secpho 41 /
      No les aportamos 39 / …).

## Documentation Updates

- [x] Delta specs synced into living capabilities: `agentic-conversation.md` (health/churn tools +
      no-derived-rate rule) and `access-control.md` (two-tier health/churn gating).
- [x] Decision log records the two-tier gating, the active-member refinement, the threshold, and the
      deterministic-math rule.
- [ ] No README/PROJECT_CONTEXT change required beyond the specs.

## Result

PASS — 139 tests green; verifier VERIFIED; adversarial review 1 MEDIUM found + fixed (re-clean);
deterministic, gated, PII-minimal, zero-copy. Going-LIVE prerequisite (already met): `SECPHO_LIVE_DATA`
+ token on Render. Follow-up: run LaunchGuardian once on Linux/CI for the semgrep SAST gate.
