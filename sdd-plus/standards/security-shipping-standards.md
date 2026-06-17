# Security Shipping Standards

## Purpose

Use these standards when a change can affect whether a project is safe to deploy, expose, operate, or connect to real data and users.

These standards are generic and apply across stacks. They complement SDD+ change packets and the LaunchGuardian Framework spec.

## LaunchGuardian Requirement

LaunchGuardian Framework (LGF) is required for deployable projects.

Before launch or a material deployable change, create project-specific LGF records from the templates in `sdd-plus/security/` or update the existing project records.

## Agent Responsibilities

Agents may:

- identify whether LGF appears to apply
- propose applicable gates
- propose skipped gates and reasons
- draft inventories, threat models, role matrices, risk records, and launch decisions
- flag missing evidence or unresolved critical findings

Agents must not silently waive high-risk gates. Humans must confirm skipped high-risk gates.

## High-Impact Areas

Treat the following as high-impact:

- security controls or security assumptions
- authentication, authorization, sessions, identity, or permissions
- privacy, personal data, sensitive data, production data, or retention
- deployment, hosting, domains, networking, secrets, or environment configuration
- database schema, migrations, storage, backups, or destructive data operations
- frontend exposure, client-side tokens, public routes, CORS, CSP, or browser storage
- infrastructure, CI/CD, dependency policy, or supply-chain controls

High-impact changes require explicit documentation in the active SDD+ change packet and, when deployable, LGF artifact updates.

## Gate Confirmation

For each deployable change, record:

- which gates apply
- which gates do not apply
- who confirmed skipped high-risk gates
- what evidence supports each completed gate
- any unresolved findings or accepted risks

Skipped high-risk gates must include a human-confirmed reason.

For any high-risk gate, `applies: false` is invalid unless all of the following are filled:

- `human_confirmation_required: true`
- `confirmed_by`
- `confirmed_at`
- `reason`
- `evidence`

## Required LGF Gates

Evaluate every gate for deployable projects:

- Gate 0 — Scope & Permission
- Gate 1 — Product, Asset & Data Inventory
- Gate 2 — Threat Modeling
- Gate 3 — Code Security
- Gate 4 — Secrets & Config Hygiene
- Gate 5 — Frontend Exposure
- Gate 6 — API Auth & Object Authorization
- Gate 7 — Injection & Input Safety
- Gate 8 — Auth, Sessions & CSRF
- Gate 9 — File Upload, SSRF, Imports & Exports
- Gate 10 — Dependency, SBOM & Supply Chain
- Gate 11 — Infrastructure, DNS, TLS & Web Hardening
- Gate 12 — Resilience, DDoS, Abuse & Cost Defense
- Gate 13 — Webhooks, Background Jobs & Integrations
- Gate 14 — Privacy, Legal & Data Lifecycle
- Gate 15 — AI/RAG/Agent Security
- Gate 16 — Multi-Tenant & Internal Permission Isolation
- Gate 17 — Observability, Logs & Incident Readiness
- Gate 18 — Backup, Recovery, Deletion & Rotation
- Gate 19 — Business Logic Abuse
- Gate 20 — Launch Decision
- Gate 21 — Continuous Monitoring

Each gate may be marked `applies: true`, `applies: false`, or `applies: unknown`. A high-risk gate marked `applies: false` must satisfy the high-risk skip rule above.

## Blocking Findings

Critical findings block launch until the finding is fixed and verified, the affected feature or asset is removed from launch scope, or the severity is downgraded by new evidence.

A change must not be marked launch-ready while any critical finding remains open. An exceptional Critical override is not normal approval. If a project defines one, it must require explicit owner approval, documented rationale, compensating controls, and follow-up remediation.

High findings should block launch unless a human owner accepts the risk with a mitigation, due date, and rollback or containment plan.

## Required Evidence

Evidence should be concrete and durable:

- file paths, configuration names, or command output summaries
- links to issue trackers or review records when available
- test names, verification steps, or manual review notes
- named owners for follow-up work and accepted risks

Do not store secrets, credentials, tokens, or production data in LGF artifacts.

## Minimum Launch Record

A launch decision should include:

- scope summary
- gate status
- open findings by severity
- accepted risks
- rollback plan
- final decision
- human approver for launch or for skipped high-risk gates
