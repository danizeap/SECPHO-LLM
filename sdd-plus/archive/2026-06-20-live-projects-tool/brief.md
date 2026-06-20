# Brief

## Change

live-projects-tool (P3, first slice)

## User Need

P1/P2 load SECPHO's 152 projects (proyectos) into memory but nothing queries them. Make the chat able
to answer about projects — Eli explicitly wanted Proyectos surfaced.

## Problem

The agent has no tool for projects, so "what projects does SECPHO have in photonics?" can't be answered.

## Scope

In scope:
- A `list_projects` deterministic tool (filters the in-memory proyectos table by query) + its agent
  tool schema + dispatch wiring, mirroring `list_retos`.
- Returns NON-financial fields only (title, acronym, tech, sectors, ámbitos, partners, type, stage,
  dates, lead, program, url); budget figures are gated until the access model (P4).
- Empty when the live layer is off.

Out of scope:
- The remaining sources, other tools, RAG (rest of P3); financial fields + access model (P4).
- Surfacing projects in the report's Section 6 (later increment).

## Acceptance Criteria

- [x] `list_projects` filters by query and returns matching projects; financial fields excluded; empty when no live data.
- [x] Registered as an agent tool the model can call.
- [x] Hermetic tests + a live proof (38 of 152 match "fotónica", budgets excluded).
- [x] Full suite green; off-by-default live gate unchanged.

## Impact Areas

- Backend: `list_projects` fn + dispatch + tool schema in `mvp_web_app.py`.
- Frontend / data model / API: none.
- AI/model behavior: one new deterministic tool (math decides; budgets gated).
- Documentation: agentic-conversation delta (twelfth tool).
- Operations/security: budgets excluded pre-access-model; nothing persisted; no new secret.

## Open Questions

- None.
