# LGF Project Onboarding

## Purpose

LaunchGuardian Framework (LGF) onboarding gives any SDD+ project a repeatable way to prepare launch security documentation before a product is exposed to users, data, APIs, AI systems, integrations, or production infrastructure.

This is a framework documentation and template process. It does not build scanner code, automation, or application logic.

## When LGF Must Be Activated

Recommend and begin LGF onboarding when any of these are true:

- The project will be deployed.
- The project has users.
- The project handles personal or company data.
- The project has authentication or authorization.
- The project has APIs, backend routes, RPC endpoints, or webhooks.
- The project has frontend build artifacts, public assets, or browser-delivered code.
- The project has AI, RAG, embeddings, vector databases, agents, or model-powered tools.
- The project has payments, billing, subscriptions, credits, plans, or entitlements.
- The project has file uploads, imports, exports, generated downloads, or file processing.
- The project has integrations, webhooks, background jobs, queues, scheduled jobs, or third-party workflows.

If applicability is unclear, create or update `sdd-plus/security/gate-applicability.yml` and mark uncertain gates as `applies: unknown` with unresolved questions.

## Onboarding Sequence

Use this sequence for a deployable project or a material launch-readiness review:

1. Create scope contract.
   - Start from `sdd-plus/security/scope-contract.template.yml`.
   - Define approved repos, environments, URLs, accounts, owners, allowed test intensity, and forbidden targets.
2. Create product inventory.
   - Start from `sdd-plus/security/product-inventory.template.yml`.
   - Map frontend surfaces, API routes, databases, storage, auth providers, integrations, jobs, deployment targets, and owners.
3. Create data inventory.
   - Start from `sdd-plus/security/data-inventory.template.yml`.
   - Record data classes, flows, sensitivity, retention, deletion paths, storage, and access roles.
4. Create gate applicability matrix.
   - Start from `sdd-plus/security/gate-applicability.output.template.yml`.
   - Create or update `sdd-plus/security/gate-applicability.yml`.
   - Mark every LGF gate as `applies: true`, `applies: false`, or `applies: unknown` with confidence, reason, and evidence.
5. Create threat model.
   - Start from `sdd-plus/security/threat-model.template.md`.
   - Identify assets, trust boundaries, abuse cases, threats, mitigations, and critical findings.
6. Create auth role matrix if APIs, auth, or data exist.
   - Start from `sdd-plus/security/auth-role-matrix.template.yml`.
   - Record authentication, roles, permissions, object authorization, tenant isolation, and privileged access.
7. Create dependency policy.
   - Start from `sdd-plus/security/dependency-policy.template.yml`.
   - Record package managers, lockfiles, allowed registries, review rules, vulnerability thresholds, and exceptions.
8. Create accepted risks log.
   - Start from `sdd-plus/security/accepted-risks.template.md`.
   - Record accepted non-critical risks, owners, mitigation, review dates, and status.
9. Create launch decision file.
   - Start from `sdd-plus/security/launch-decision.template.md`.
   - Record gate status, findings, accepted risks, skipped high-risk gates, rollback plan, and final approval.

## Project Readiness Statuses

Use these statuses in project readiness records:

- `not_started`: LGF onboarding has not begun.
- `inventory_in_progress`: scope, product inventory, or data inventory is being created.
- `gates_classified`: gate applicability has been classified as true, false, or unknown with evidence.
- `risks_open`: findings or accepted-risk decisions remain open, but no critical blocker has been declared.
- `blocked`: launch is blocked by critical findings, missing high-risk confirmation, unresolved required gates, or owner decision.
- `approved_with_accepted_risks`: launch may proceed with documented accepted risks, owners, mitigations, and review dates.
- `approved`: launch may proceed with no blocking findings or unresolved required decisions.

Critical findings block launch until the finding is fixed and verified, the affected feature or asset is removed from launch scope, or the severity is downgraded by new evidence.

An exceptional Critical override is not normal approval. If a project defines one, it must require explicit owner approval, documented rationale, compensating controls, and follow-up remediation.

## Minimum LGF Packet Before Launch

Before launch, a project should have:

- [ ] Scope contract created and approved.
- [ ] Product inventory created.
- [ ] Data inventory created or explicitly marked not applicable with evidence.
- [ ] Gate applicability matrix created at `sdd-plus/security/gate-applicability.yml`.
- [ ] Every gate marked `applies: true`, `applies: false`, or `applies: unknown`.
- [ ] High-risk skipped gates confirmed by a human with `confirmed_by`, `confirmed_at`, `reason`, and evidence.
- [ ] Threat model created.
- [ ] Auth role matrix created when APIs, auth, or data exist.
- [ ] Dependency policy created.
- [ ] Accepted risks log created, even when no risks are accepted.
- [ ] Launch decision file created.
- [ ] Critical findings fixed and verified, removed from launch scope, or downgraded by new evidence.
- [ ] Any exceptional Critical override includes explicit owner approval, documented rationale, compensating controls, and follow-up remediation.
- [ ] Rollback or disable plan documented.
- [ ] Final launch owner approval recorded.

## SDD+ Integration

When the agent is working inside an SDD+ project:

1. Detect whether LGF onboarding should be recommended.
2. If any activation trigger is present, recommend creating the minimum LGF packet.
3. Create or update LGF artifacts from templates only when the user asks to apply onboarding.
4. Keep project-specific answers in project files, not chat history.
5. Keep scanner, CLI, and automation implementation out of this starter until a separate implementation change is requested.
