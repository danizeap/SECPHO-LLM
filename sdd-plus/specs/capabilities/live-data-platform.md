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

### Requirement: Background refresher with per-source cadence and stale-while-revalidate
When live is enabled, the system SHALL re-pull the live sources in the background on a per-source
cadence (configurable; defaulting to hours), doing an immediate first load and then periodic
refreshes. It SHALL update the in-memory view for a source ONLY on a successful pull; a failed pull
SHALL leave the last-good in-memory view in place (stale-while-revalidate). The refresher SHALL never
block startup and SHALL persist nothing.

#### Scenario: Failed refresh keeps last-good
- **WHEN** a source's re-pull fails (e.g. the API is down)
- **THEN** the previously loaded in-memory view for that source is retained and served, and no error propagates.

#### Scenario: Cadence
- **WHEN** the refresher runs
- **THEN** each source is re-pulled no more often than its configured interval.

### Requirement: In-RAM change-feed
The system SHALL diff each new pull of a source against its previous in-memory pull (by record key
plus content hash) and record the added / modified / removed counts as a bounded, in-memory
change-feed (zero persistence). The first pull of a source SHALL be the baseline (no change emitted),
and a re-pull whose content is unchanged SHALL emit no change (no false positives). For sensitive
sources (added in later phases) the change-feed's record-key samples SHALL be gated like the data
itself.

#### Scenario: Baseline then change
- **WHEN** a source is loaded for the first time and then re-pulled with one new record
- **THEN** the first pull emits no change, and the re-pull records exactly one "added" on the change-feed.

#### Scenario: Stable re-pull is silent
- **WHEN** a source is re-pulled with identical content
- **THEN** no change is recorded (the content-hash diff produces no false positives).

### Requirement: Financial sources in the live layer (🔴, zero-copy)
The system SHALL live-load and normalize SECPHO's financial reports/v1 sources into canonical
in-memory frames, persisting nothing: `negocio_financiero` (turnover + investment), `cuotas` (cuota
amount, join/leave dates, churn reason), `invoices` (the per-socio billing ledger with
status/concept/due/paid/amount), and `contributions` (per-socio yearly contributions). They load only
when the live layer is enabled, are members of `SENSITIVE_SOURCES`, and their EXPOSURE is gated at the
tool layer (see the `access-control` capability), not at load. A socio counts as a `baja` (left) only
when `Fecha de baja definitiva` is a real date — the source uses the literal "No consta" for active
members. The change-feed records counts for these sources but OMITS the changed-key sample, so a
surfaced feed cannot reveal which socios had financial changes.

#### Scenario: Financial frames normalize and gate
- **WHEN** the live layer is on and a financial source is pulled
- **THEN** it normalizes into its canonical frame, "No consta" counts as active, and any change-feed
  entry for it carries counts only (no key sample).
