# Project Security Readiness

Copy this file to a project-specific filename before using it as a LaunchGuardian readiness record.

## Project

- Project:
- Change or launch:
- Owner:
- Reviewer:
- Date:
- Readiness status: `not_started`

Allowed readiness statuses:

- `not_started`
- `inventory_in_progress`
- `gates_classified`
- `risks_open`
- `blocked`
- `approved_with_accepted_risks`
- `approved`

## Related Gates

- Gate 0 — Scope & Permission
- Gate 1 — Product, Asset & Data Inventory
- Gate 2 — Threat Modeling
- Gate 20 — Launch Decision
- Gate 21 — Continuous Monitoring

## Activation Triggers

Mark each trigger `yes`, `no`, or `unknown`.

| Trigger | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Project will be deployed | unknown | TBD | TBD |
| Project has users | unknown | TBD | TBD |
| Project handles personal or company data | unknown | TBD | TBD |
| Project has auth | unknown | TBD | TBD |
| Project has APIs | unknown | TBD | TBD |
| Project has frontend build artifacts | unknown | TBD | TBD |
| Project has AI/RAG/agents | unknown | TBD | TBD |
| Project has payments/billing | unknown | TBD | TBD |
| Project has file uploads/imports/exports | unknown | TBD | TBD |
| Project has integrations/webhooks/background jobs | unknown | TBD | TBD |

## Onboarding Artifacts

| Artifact | Target File | Status | Owner | Notes |
| --- | --- | --- | --- | --- |
| Scope contract | `sdd-plus/security/scope-contract.yml` | not_started | TBD | Create from `scope-contract.template.yml`. |
| Product inventory | `sdd-plus/security/product-inventory.yml` | not_started | TBD | Create from `product-inventory.template.yml`. |
| Data inventory | `sdd-plus/security/data-inventory.yml` | not_started | TBD | Create from `data-inventory.template.yml`. |
| Gate applicability matrix | `sdd-plus/security/gate-applicability.yml` | not_started | TBD | Create from `gate-applicability.output.template.yml`. |
| Threat model | `sdd-plus/security/threat-model.md` | not_started | TBD | Create from `threat-model.template.md`. |
| Auth role matrix | `sdd-plus/security/auth-role-matrix.yml` | not_started | TBD | Required when APIs, auth, or data exist. |
| Dependency policy | `sdd-plus/security/dependency-policy.yml` | not_started | TBD | Create from `dependency-policy.template.yml`. |
| Accepted risks log | `sdd-plus/security/accepted-risks.md` | not_started | TBD | Create from `accepted-risks.template.md`. |
| Launch decision | `sdd-plus/security/launch-decision.md` | not_started | TBD | Create from `launch-decision.template.md`. |

## Minimum LGF Packet Before Launch

- [ ] Scope contract created and approved.
- [ ] Product inventory created.
- [ ] Data inventory created or explicitly marked not applicable with evidence.
- [ ] Gate applicability matrix created at `sdd-plus/security/gate-applicability.yml`.
- [ ] Every gate marked `applies: true`, `applies: false`, or `applies: unknown`.
- [ ] High-risk skipped gates confirmed by a human with `human_confirmation_required: true`, `confirmed_by`, `confirmed_at`, `reason`, and evidence.
- [ ] Threat model created.
- [ ] Auth role matrix created when APIs, auth, or data exist.
- [ ] Dependency policy created.
- [ ] Accepted risks log created, even when no risks are accepted.
- [ ] Launch decision file created.
- [ ] Critical findings fixed and verified, removed from launch scope, or downgraded by new evidence.
- [ ] Any exceptional Critical override includes explicit owner approval, documented rationale, compensating controls, and follow-up remediation.
- [ ] Rollback or disable plan documented.
- [ ] Final launch owner approval recorded.

## Current Blockers

| Blocker | Severity | Required Action | Owner | Status |
| --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD |

## Accepted Risks

Link to the accepted risks log or state that no risks are accepted.

## Final Readiness Notes

Summarize why the project is blocked, approved with accepted risks, or approved.
