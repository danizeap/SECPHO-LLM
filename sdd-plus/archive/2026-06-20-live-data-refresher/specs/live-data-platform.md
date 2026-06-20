# Spec Delta: live-data-refresher

Capability: live-data-platform

Phase 2: keep the in-memory view current with a background refresher, and surface what changed via an
in-RAM change-feed — still persisting nothing.

## ADDED Requirements

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
and a re-pull whose content is unchanged SHALL emit no change (no false positives).

#### Scenario: Baseline then change
- **WHEN** a source is loaded for the first time and then re-pulled with one new record
- **THEN** the first pull emits no change, and the re-pull records exactly one "added" on the change-feed.

#### Scenario: Stable re-pull is silent
- **WHEN** a source is re-pulled with identical content
- **THEN** no change is recorded (the content-hash diff produces no false positives).
