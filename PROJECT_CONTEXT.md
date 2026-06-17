# Project Context

## Project Name

SECPHO Intelligence System

## Short Description

A conversational cluster-intelligence system over SECPHO's deep-tech ecosystem data. Its
flagship use case is contact recommendation (member-to-member matchmaking); on top of that it
is now a tool-calling assistant that answers natural-language questions over the whole dataset
(socios/companies, people, events, retos/challenges) and generates one-page value reports.

## Audience / Users

SECPHO staff (SECPHO is a Spanish deep-tech / photonics cluster association) and, through them,
its member companies ("socios"). The interface is for non-technical staff to explore the cluster
and prepare member value.

## Core Problem

SECPHO already holds rich assets — member profiles, socios, events, attendance, retos, projects,
historical activity — but no way to turn them into member value (good introductions, insight).
The project turns those assets into conversational cluster intelligence.

## Desired Outcome

Staff can ask, in Spanish or English, about the cluster and get grounded answers, model-ranked
introductions with evidence, and value reports — where the recommendation math is deterministic,
auditable, and tunable, and the LLM only explains it.

## First Useful Version

The deployed chat (contact matchmaker + dataset-wide Q&A) behind a login, on Render, that SECPHO
can use in a live feedback loop. (This exists and is the current pilot surface.)

## Stack And Tools

Preferred:

- Python 3.11, standard-library `http.server` (no web framework) — single-file app `backend_api/mvp_web_app.py`
- pandas + scikit-learn (TF-IDF + cosine + Jaccard) for the deterministic recommender (batch, in `recommendation_engine/`)
- OpenAI Responses API for explanation + the agent loop (`gpt-5-mini` default "mini" tier; `gpt-5.5` flagship tier, configurable via `OPENAI_MODEL_FLAGSHIP`)
- Deploy on Render (`render.yaml`); dependency-light by design (`requirements.txt`)
- SDD+ / Drydock governance (`sdd-plus/`, `scripts/sdd.py`)

Avoid:

- Letting the LLM be the scoring authority (it must never invent or re-rank matches)
- Heavy frameworks / databases unless a concrete need appears (kept stdlib + CSV so far)
- Hardcoded credentials anywhere in code, docs, or commits

## Data And Integrations

- SECPHO WordPress REST endpoints (`members`, `suscriptores`, `datosnegocio`, `datoscontacto`,
  `actosagenda`, `retos`) under `https://secpho.org/wp-json/reports/v1/`, authenticated with
  `SECPHO_API_AUTH_TOKEN` (env only).
- Normalized data in `data/processed/`; recommendation outputs in `recommendation_engine/outputs/`.
- OpenAI API (`OPENAI_API_KEY`, env only).
- Phase-1 recommendation universe = the **192 official socios** from `datosnegocio`; wider
  contacts/subscribers are enrichment, not primary targets.

## Constraints

- **Governing principle: "Math decides. The LLM explains."** The recommender must be measurable,
  auditable, and tunable; the LLM must not invent matches or be the scoring authority.
- Credentials live in environment variables, never committed (`.env`, `.keys` gitignored; only
  `.env.example` with placeholders is committed).
- Spanish-first (Spanish is the default UI and response language; English is a toggle).
- Co-attendance graph is **blocked** until SECPHO provides attendee-level event data; event
  signals currently mean shared *registration interest*, not confirmed attendance.
- Security must be fail-closed (admin data never exposed without a real admin password).

## Design / UX Preferences

Clean dark chat UI; conversational and decisive (acts with sensible defaults); transparent (shows
the math/evidence behind recommendations); bilingual ES/EN; fail-closed and safe for a live demo.

## Definition Of Done

Current phase: a deployed, SDD+-governed app SECPHO can test in a structured feedback loop, with
the deterministic recommender, dataset-wide conversational access, value reports, and bilingual UI
all working behind login.

## Open Questions

- Recommendation quality is only informally validated (SECPHO said the matches "make sense"); no
  precision@k yet. Structured per-recommendation feedback is the planned next step.
- Complementarity and retos supply-demand matching are feasibility-approved but **not yet
  implemented** (the recommender is currently similarity/homophily-based).
- Co-attendance remains blocked pending an attendee-level data source from SECPHO.

## Durable Decisions

| Date | Decision | Reason |
| --- | --- | --- |
| 2026-06-16 | "Math decides, the LLM explains" — scores are deterministic and precomputed; the LLM only explains/orchestrates. | Recommendations must be auditable and tunable; the LLM must not invent or re-rank matches. |
| 2026-06-16 | Phase-1 recommendation universe = the 192 official socios. | Bound the problem; richest, most reliable data; enrichment sources stay secondary. |
| 2026-06-16 | Flagship model = `gpt-5.5` (configurable via `OPENAI_MODEL_FLAGSHIP`); mini = `gpt-5-mini`. | Owner-confirmed current OpenAI flagship; configurable so a wrong id never breaks LLM calls. |
| 2026-06-17 | Adopt SDD+ / Drydock governance and retroactively reconstruct the session's work as 9 change packets. | Bring all work under spec-backed, version-controlled governance after building ahead of protocol. |
