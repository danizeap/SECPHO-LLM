# LGF Gate Applicability System

## Purpose

The LaunchGuardian Framework (LGF) Gate Applicability System helps any SDD+ project decide which LGF gates apply before launch.

It is a documentation and process layer. It does not scan code, call external tools, test live systems, or enforce policies automatically. Future tooling may generate or validate these records, but the starter only defines the framework, evidence model, and reusable output template.

## Source Of Truth

Use these files as the local source of truth:

- `sdd-plus/specs/launchguardian-framework.md`
- `sdd-plus/standards/security-shipping-standards.md`
- `sdd-plus/security/gate-applicability.template.yml`
- `sdd-plus/specs/MASTER_LAUNCHGUARDIAN_CONTEXT.md`, if present

Template roles:

- `sdd-plus/security/gate-applicability.template.yml` is the neutral schema/reference template. It may leave gates unknown to show the fields without making project assumptions.
- `sdd-plus/security/gate-applicability.output.template.yml` is the project-use output template. It should apply always-on defaults for deployable projects.

## Required Output

Before applying LGF to a project, create or update:

```text
sdd-plus/security/gate-applicability.yml
```

Use `sdd-plus/security/gate-applicability.output.template.yml` as the reusable project output template. Do not copy the neutral schema/reference template as the project output unless you also apply the required project defaults.

Each gate must be marked with:

- `applies: true`
- `applies: false`
- `applies: unknown`

Each gate must include confidence, evidence, reason, and human confirmation fields.

## Status Values

### applies: true

Use when the gate applies to the project or change.

Examples:

- A frontend exists, so Gate 5 applies.
- API routes exist, so Gate 6 applies.
- Personal data exists, so Gate 14 applies.

### applies: false

Use only when there is evidence that the gate does not apply.

For any high-risk gate, `applies: false` is invalid unless all of the following are filled:

- `human_confirmation_required: true`
- `confirmed_by`
- `confirmed_at`
- `reason`
- `evidence`

### applies: unknown

Use when the agent or reviewer cannot determine applicability from available evidence.

Unknown gates must include unresolved questions and should not be treated as safely skipped.

## Confidence Levels

- `high`: strong repo/config evidence or explicit human confirmation supports the applicability decision.
- `medium`: several signals support the decision, but some uncertainty remains.
- `low`: weak evidence, inference, missing files, or unresolved questions remain.

## Evidence Requirements

Evidence must be durable and safe to commit. Do not include secrets, credentials, tokens, production data, or sensitive raw user data.

Evidence types:

- `repo_evidence`: files, folders, route names, dependency manifests, lockfiles, schemas, or code references.
- `config_evidence`: deployment config, environment variable names without values, hosting config, CI config, DNS/TLS notes, or security headers.
- `human_statement`: an explicit statement from an owner or reviewer.
- `unresolved_question`: a question that blocks a confident decision.

Every gate should include at least one evidence item. If no evidence exists, mark the gate `applies: unknown` and add an unresolved question.

## Always-On Gates

These gates should apply to deployable projects by default:

- Gate 0 — Scope & Permission
- Gate 1 — Product, Asset & Data Inventory
- Gate 3 — Code Security
- Gate 4 — Secrets & Config Hygiene
- Gate 10 — Dependency, SBOM & Supply Chain
- Gate 17 — Observability, Logs & Incident Readiness
- Gate 20 — Launch Decision

An always-on gate may be marked `applies: false` only with explicit human confirmation and evidence.

## Conditional Trigger Rules

Use these triggers to propose applicability for conditional gates:

| Trigger | Gate Result |
| --- | --- |
| Frontend detected | Gate 5 — Frontend Exposure applies |
| API routes detected | Gate 6 — API Auth & Object Authorization applies |
| User input crossing trust boundaries detected | Gate 7 — Injection & Input Safety applies |
| Auth, sessions, cookies, OAuth, magic links, or login detected | Gate 8 — Auth, Sessions & CSRF applies |
| Upload, import, export, file processing, URL fetching, or SSRF-like flows detected | Gate 9 — File Upload, SSRF, Imports & Exports applies |
| Public deployment, hosting, DNS, TLS, CDN, WAF, or infrastructure detected | Gate 11 — Infrastructure, DNS, TLS & Web Hardening applies |
| Public deployment, rate-limit-sensitive APIs, AI costs, abuse paths, or traffic exposure detected | Gate 12 — Resilience, DDoS, Abuse & Cost Defense applies |
| Webhooks, background jobs, queues, scheduled jobs, third-party integrations, or OAuth scopes detected | Gate 13 — Webhooks, Background Jobs & Integrations applies |
| Personal data, sensitive data, retention, deletion, legal, or processor obligations detected | Gate 14 — Privacy, Legal & Data Lifecycle applies |
| LLMs, RAG, vector DBs, embeddings, agent tools, model calls, or AI workflow automation detected | Gate 15 — AI/RAG/Agent Security applies |
| Tenant, organization, workspace, client, team, account, internal role, or cross-user permission model detected | Gate 16 — Multi-Tenant & Internal Permission Isolation applies |
| Backups, deletion, recovery, token rotation, or persistent user/business data detected | Gate 18 — Backup, Recovery, Deletion & Rotation applies |
| Business rules, credits, payments, plans, subscriptions, coupons, invitations, trials, quotas, or entitlements detected | Gate 19 — Business Logic Abuse applies |
| Production launch, live users, scheduled release, uptime expectations, or post-launch ownership detected | Gate 21 — Continuous Monitoring applies |

Gate 2 — Threat Modeling should apply when the project has sensitive data, auth, APIs, AI/RAG, public deployment, multi-tenant boundaries, money movement, files, integrations, or other high-impact areas.

## Human Confirmation

Agents may propose applicability. Humans must confirm skipped high-risk gates.

For any high-risk gate, `applies: false` is invalid unless all of the following are filled:

- `human_confirmation_required: true`
- `confirmed_by`
- `confirmed_at`
- `reason`
- `evidence`

Use `applies: unknown` when confirmation is missing.

## Example Completed Matrix: Generic SaaS AI App

This example assumes a generic SaaS AI app with a web frontend, API routes, user login, organizations, subscriptions, LLM calls, vector retrieval, webhooks, background jobs, and production launch plans.

| Gate | Applies | Confidence | Example Evidence |
| --- | --- | --- | --- |
| Gate 0 — Scope & Permission | true | high | Human owner approved repo and staging URL scope. |
| Gate 1 — Product, Asset & Data Inventory | true | high | Frontend, API, database, auth provider, LLM provider, vector DB, jobs, and webhooks identified. |
| Gate 2 — Threat Modeling | true | high | Public SaaS with auth, AI, tenant data, payments, and integrations. |
| Gate 3 — Code Security | true | high | Deployable app code exists. |
| Gate 4 — Secrets & Config Hygiene | true | high | Environment variables and third-party providers detected. |
| Gate 5 — Frontend Exposure | true | high | Web frontend and public routes detected. |
| Gate 6 — API Auth & Object Authorization | true | high | API routes and user/org resources detected. |
| Gate 7 — Injection & Input Safety | true | high | User prompts, forms, API inputs, and search/filter inputs detected. |
| Gate 8 — Auth, Sessions & CSRF | true | high | Login, sessions, cookies, OAuth, or auth provider detected. |
| Gate 9 — File Upload, SSRF, Imports & Exports | unknown | medium | No upload route confirmed yet; exports may exist. |
| Gate 10 — Dependency, SBOM & Supply Chain | true | high | Package manifests and lockfiles detected. |
| Gate 11 — Infrastructure, DNS, TLS & Web Hardening | true | high | Public deployment target detected. |
| Gate 12 — Resilience, DDoS, Abuse & Cost Defense | true | high | Public app, API endpoints, auth flows, and AI cost exposure detected. |
| Gate 13 — Webhooks, Background Jobs & Integrations | true | high | Payment webhook and background worker detected. |
| Gate 14 — Privacy, Legal & Data Lifecycle | true | high | User profiles, org data, prompts, and retained AI outputs detected. |
| Gate 15 — AI/RAG/Agent Security | true | high | LLM provider and vector DB detected. |
| Gate 16 — Multi-Tenant & Internal Permission Isolation | true | high | Organization/workspace model detected. |
| Gate 17 — Observability, Logs & Incident Readiness | true | high | Always-on gate for deployable projects. |
| Gate 18 — Backup, Recovery, Deletion & Rotation | true | medium | Database and retained user data detected; restore evidence unresolved. |
| Gate 19 — Business Logic Abuse | true | high | Plans, subscription checks, credits, or entitlements detected. |
| Gate 20 — Launch Decision | true | high | Always-on gate for deployable projects. |
| Gate 21 — Continuous Monitoring | true | high | Production launch and live users expected. |

## SDD+ Workflow

For each deployable project or material deployable change:

1. Create or update `sdd-plus/security/gate-applicability.yml`.
2. Mark each gate `true`, `false`, or `unknown`.
3. Add confidence, evidence, and reason.
4. Require human confirmation for skipped high-risk gates.
5. Treat unknown gates as unresolved until answered or explicitly accepted.
6. Use the applicability matrix to decide which LGF templates and launch evidence must be completed.
