# Brief

## Change

data-sync-pipeline — "zero-copy live intelligence layer"

## User Need

SECPHO (Sergio) wants the whole company's data — members, contacts, business, finances,
activities, projects, retos, success cases, subscribers — queryable by the LLM. The demo ran on
hand-normalized static CSVs; that's a frozen snapshot of a living system and goes stale immediately.

## Problem

We need the platform to reflect SECPHO's *current* data, continuously — without becoming the
custodian of their confidential financial/PII data. The Owner (this is a TFM, may not stay at the
company) explicitly must NOT create a data-governance burden they'd have to own or hand off.

## Decision that shapes everything: persist nothing confidential

The platform stores **no copy** of SECPHO's data. It pulls the live WordPress REST endpoints
(`/wp-json/reports/v1/*`) into memory, normalizes, reasons over them, and persists nothing. WordPress
stays the single system of record and custodian. We are a stateless **processor**, not a controller.

## Scope

In scope:
- Live fetch of the 17 `reports/v1` endpoints (token from env, server-side only).
- In-memory normalization into the canonical structures the app/LLM already query (replacing static CSVs).
- Background, parallel, progressive refresh on a tiered cadence; stale-while-revalidate in RAM.
- In-RAM change-diff between refresh cycles → a live change-feed (proactive alerts) with zero persistence.
- Deterministic in-memory tools for the new entities (projects, activities, finances, …) + RAG (in-memory
  vector index over the text-rich sources, rebuilt on load).
- Access model: financial/PII sources are admin-only in the chat.
- Freshness + provenance stamped on every answer.

Out of scope (and deliberately NOT built):
- Any database / persistent store / data warehouse (Supabase, Render PG, files of their data).
- A change-detection store, historical snapshots we own, or long-term trend storage on our side.
- WordPress-side security hardening (their WP guy: rotate token, IP-allowlist, header auth).
- Long-term history → handed to SECPHO via digests, or read from the source's own timestamps.

## Acceptance Criteria (blueprint stage)

- [ ] Owner approves this blueprint before any Phase-1 code.
- [ ] Architecture persists nothing confidential; WordPress remains the sole store.
- [ ] Every tradeoff has a named mitigation (history, change-alerts, cold-start, resilience, API load).
- [ ] A data-model map of all 17 sources (from the schema scan) with sensitivity tiers + change keys.
- [ ] Phasing that ships value incrementally, each phase drydocked.

## Impact Areas

- Backend: new live-ingestion module; DATA becomes a refreshed in-memory view, not CSV load.
- Frontend: minimal (freshness stamps; admin-gating of financial answers).
- Data model: in-memory only; canonical entities extended (projects, activities, finances, etc.).
- API: outbound calls to SECPHO's `reports/v1`; no new persistent store.
- AI/model behavior: new queryable tools + RAG; grounding/citation discipline extended.
- Documentation: new capability spec (live-data-platform); PROJECT_CONTEXT update.
- Operations/security: token as env secret; processor-not-controller posture; access model; keep-warm.

## Open Questions

- Keep-warm mechanism on the current Render plan (to keep the in-RAM change-memory continuous).
- Refresh cadence per source (defaults proposed; tune with Sergio).
- Whether to add the optional digest-to-SECPHO feature now or later (gives them long-term history).
