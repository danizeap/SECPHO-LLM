# Launch Decision

Copy this file to a project-specific filename before using it as a launch record.

## Summary

- Project:
- Change:
- Date:
- Owner:
- Launch target:
- Decision: Pending

Decision must remain BLOCKED while any Critical finding is open. Critical findings block launch until the finding is fixed and verified, the affected feature or asset is removed from launch scope, or the severity is downgraded by new evidence.

An exceptional Critical override is not normal approval. If a project defines one, it must require explicit owner approval, documented rationale, compensating controls, and follow-up remediation.

## Related Gates

- Gate 20 — Launch Decision
- Gate 21 — Continuous Monitoring

## Gate Status

| Gate | Applies | Status | Evidence | Notes |
| --- | --- | --- | --- | --- |
| Gate 0 — Scope & Permission | unknown | TBD | TBD | TBD |
| Gate 1 — Product, Asset & Data Inventory | unknown | TBD | TBD | TBD |
| Gate 2 — Threat Modeling | unknown | TBD | TBD | TBD |
| Gate 3 — Code Security | unknown | TBD | TBD | TBD |
| Gate 4 — Secrets & Config Hygiene | unknown | TBD | TBD | TBD |
| Gate 5 — Frontend Exposure | unknown | TBD | TBD | TBD |
| Gate 6 — API Auth & Object Authorization | unknown | TBD | TBD | TBD |
| Gate 7 — Injection & Input Safety | unknown | TBD | TBD | TBD |
| Gate 8 — Auth, Sessions & CSRF | unknown | TBD | TBD | TBD |
| Gate 9 — File Upload, SSRF, Imports & Exports | unknown | TBD | TBD | TBD |
| Gate 10 — Dependency, SBOM & Supply Chain | unknown | TBD | TBD | TBD |
| Gate 11 — Infrastructure, DNS, TLS & Web Hardening | unknown | TBD | TBD | TBD |
| Gate 12 — Resilience, DDoS, Abuse & Cost Defense | unknown | TBD | TBD | TBD |
| Gate 13 — Webhooks, Background Jobs & Integrations | unknown | TBD | TBD | TBD |
| Gate 14 — Privacy, Legal & Data Lifecycle | unknown | TBD | TBD | TBD |
| Gate 15 — AI/RAG/Agent Security | unknown | TBD | TBD | TBD |
| Gate 16 — Multi-Tenant & Internal Permission Isolation | unknown | TBD | TBD | TBD |
| Gate 17 — Observability, Logs & Incident Readiness | unknown | TBD | TBD | TBD |
| Gate 18 — Backup, Recovery, Deletion & Rotation | unknown | TBD | TBD | TBD |
| Gate 19 — Business Logic Abuse | unknown | TBD | TBD | TBD |
| Gate 20 — Launch Decision | true | TBD | TBD | TBD |
| Gate 21 — Continuous Monitoring | unknown | TBD | TBD | TBD |

## Findings

| Severity | Count | Launch Impact |
| --- | --- | --- |
| Critical | 0 | Blocks launch if greater than 0 until fixed and verified, removed from launch scope, or downgraded by new evidence |
| High | 0 | Blocks launch unless explicitly accepted by a human owner |
| Medium | 0 | Track mitigation or follow-up |
| Low | 0 | Track if useful |

## Skipped High-Risk Gates

| Gate | Reason | Confirmed By | Date |
| --- | --- | --- | --- |
| None |  |  |  |

## Accepted Risks

Link to the accepted risks record or state that no risks were accepted.

## Rollback Or Disable Plan

Describe how the launch can be rolled back, disabled, or contained.

## Final Approval

- Approved by:
- Approval date:
- Conditions:
