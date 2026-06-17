# Capability: scoring-console

## Purpose

Make the recommendation scoring visible and explorable: SECPHO can adjust the six signal weights and watch a person's candidate pool re-rank live, deterministically, so "math decides" is interactive rather than a black box.

## Requirements

### Requirement: Deterministic weighted re-ranking
The system SHALL re-rank a person's precomputed candidate pool using only arithmetic over the six tunable signals, with `custom_score = sum(weight_i/100 * signal_i)` and no LLM involvement.

#### Scenario: Default weights match the model
- **WHEN** `rerank_for_person` is called for a person with the default signal weights (profile_similarity 44, structured_overlap 24, event_interest_overlap_score 14, needs_overlap 10, location_overlap_score 6, personal_affinity_score 2)
- **THEN** the top candidate matches the default model ranking (e.g. person 74449 -> Carlos Alberto Castano Moraga)

#### Scenario: Custom weights re-order the pool
- **WHEN** a weight is changed so a different signal dominates
- **THEN** candidates are re-sorted by `custom_score`, and each carries `new_rank`, `default_rank`, and `movement = default_rank - new_rank`

#### Scenario: Person has no candidate pool
- **WHEN** `rerank_for_person` is called for a member id with no matching rows in `DATA["matches"]`
- **THEN** it returns `{found: false, target: null, candidates: []}`

### Requirement: Per-signal contribution and evidence breakdown
The system SHALL return, for each re-ranked candidate, the per-signal contribution (weight, signal value, contribution) and the shared evidence (technologies, sectors, location, needs, events).

#### Scenario: Breakdown accompanies each candidate
- **WHEN** the re-ranked list is produced
- **THEN** each candidate includes a `contributions` array (one entry per signal with `weight`, `signal`, `contribution`, `color`) and an `evidence` object

### Requirement: Rerank API endpoint
The system SHALL expose `GET /api/rerank`, gated behind authentication, returning the re-ranked candidate list as JSON.

#### Scenario: Valid request
- **WHEN** an authenticated client calls `GET /api/rerank?id=<member_id>&<signal weights>`
- **THEN** it responds with the re-ranked candidates and their contribution breakdowns as JSON

#### Scenario: Invalid id
- **WHEN** the `id` query param is missing or non-numeric
- **THEN** it responds with HTTP 400 `{error: "invalid_id"}`

#### Scenario: Unauthenticated request
- **WHEN** an unauthenticated client calls `GET /api/rerank`
- **THEN** the request is rejected by the authentication gate

### Requirement: Scoring console page
The system SHALL serve an auth-gated `GET /tuning` "Scoring console" page with a person search box, six 0-100 weight sliders, and a live re-ranked candidate list (contribution bars and up/down movement markers) that calls `/api/rerank` on slider input.

#### Scenario: Authenticated load
- **WHEN** an authenticated user opens `GET /tuning`
- **THEN** the page returns HTTP 200 and renders the console

#### Scenario: Unauthenticated load
- **WHEN** an unauthenticated user opens `GET /tuning`
- **THEN** the user is redirected to `/login`

#### Scenario: Sidebar entry point
- **WHEN** a user views the chat UI
- **THEN** a "Scoring console" sidebar block links to `/tuning`
