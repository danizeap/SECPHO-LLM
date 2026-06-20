# Capability: live-data-platform

## Purpose

Reflect SECPHO's *current* operational data by reading it live from their WordPress REST API
(`/wp-json/reports/v1/*`) and holding it only in memory — storing no copy. WordPress stays the sole
system of record and custodian; the platform is a stateless processor ("owns understanding, not
data"). Phase 1 establishes the layer and three low-sensitivity sources (retos, proyectos,
casos-éxito); the refresher + in-RAM change-feed, all 17 sources + LLM tools + RAG, the access model,
and the intelligence layer arrive in follow-on changes.

## Requirements

### Requirement: Zero-copy posture — persist no source data
The system SHALL NOT persist SECPHO's source data in any database, file, or cache it controls.
WordPress remains the sole system of record and custodian; the platform holds normalized data only in
memory while running. The API token SHALL be read from the environment, used server-side only, and
never logged, returned to the client, or written to disk or version control.

#### Scenario: Nothing persisted
- **WHEN** the app stops or redeploys
- **THEN** no copy of SECPHO's source data remains anywhere the platform controls; only WordPress still has it.

### Requirement: Live pull and in-memory normalization
The system SHALL fetch the configured `reports/v1` endpoints and normalize each into the canonical
in-memory shape the app/LLM query (e.g. live retos normalized to the same schema as
`retos_normalized.csv`). The live layer SHALL be opt-in — enabled only when the `SECPHO_LIVE_DATA`
flag is truthy AND a token (`SECPHO_API_AUTH_TOKEN`) is configured; otherwise the app SHALL fall back
to its CSV snapshot and make no network call (so a token in `.env` cannot accidentally enable live in
tests or local runs).

#### Scenario: Live retos match the canonical schema
- **WHEN** the live layer loads retos
- **THEN** the normalized table has the canonical retos columns, dates preserved in the consumers' format, and HTML stripped from descriptions.

#### Scenario: Disabled by default
- **WHEN** the `SECPHO_LIVE_DATA` flag is off (even if a token is configured)
- **THEN** the live layer is inert (no request) and the app serves its CSV data.

### Requirement: Best-effort, non-blocking load with per-source fallback
The system SHALL load sources in parallel without blocking startup, and SHALL isolate failures: a
source that fails or is disabled is simply absent and the caller falls back to its CSV/empty default,
never raising and never logging the token or any record values. Each successful source load SHALL
record a freshness timestamp.

#### Scenario: One source fails, others load
- **WHEN** one endpoint errors during a load
- **THEN** the other sources still load, the failed one is absent (fallback), and no token or value is logged.

#### Scenario: Freshness recorded
- **WHEN** a source loads successfully
- **THEN** its load time is recorded and available for freshness-stamping answers.
