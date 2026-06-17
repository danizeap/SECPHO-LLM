# Capability: recommendation-reports

## Purpose

Let a SECPHO curator human-curate the matchmaking for one person inside the chat — adjusting how much each signal counts — and turn that curated ranking into a transparent one-page value report. The ranking is always produced by deterministic math; the LLM only explains it.

## Requirements

### Requirement: Curator-tunable in-chat weighting
The system SHALL let a curator adjust the six signal weights for one person inside the chat and re-rank that person's candidates live against a 50-deep precomputed pool, with re-ranking done by deterministic math (no LLM).

#### Scenario: Recommendation answer offers a tuner
- **WHEN** the chat returns a recommendation answer for a person (via `tool_answer` recommend_contacts or `chat_flow` rec_intent)
- **THEN** the answer carries a `[tune:ID]` token that `markdown_to_chat_html` renders as an "Adjust weighting & report" button which opens an inline six-slider panel

#### Scenario: Live re-rank against the deep pool
- **WHEN** the curator moves a slider in the tuner panel
- **THEN** the panel calls `/api/rerank` against the 50-deep pool and updates the ranking, scores, and movement-vs-model indicators without an LLM call

#### Scenario: Tuning surfaces a buried match
- **WHEN** `rerank_for_person(74449, ...)` is called with `needs_overlap` weighted to 100
- **THEN** Patricia Valero (model rank #18) and Joan Labal Abad (model rank #35) rise into the tuned top, proving the deepened pool lets buried candidates appear rather than only reshuffling the default top-10

### Requirement: Tuned value report
The system SHALL generate a one-page matchmaker report from the curator's tuned top-5 ranking, where the ranking is produced by math and the LLM only explains it, and SHALL state the applied weighting in plain language.

#### Scenario: Report from a custom weighting
- **WHEN** `GET /api/report-tuned?id=<valid>&<weights>` is requested by an authenticated client
- **THEN** the system returns a 200 LLM report whose text states the curator's custom weighting and keeps the math-produced recommendation order

#### Scenario: Default weighting is named honestly
- **WHEN** the report is generated with the sliders left at their model defaults
- **THEN** `weighting_text` returns the model's default-weighting statement instead of a custom-weighting statement

#### Scenario: Report follows the chat language
- **WHEN** the report is requested with a `lang` parameter
- **THEN** the report and its progress messages render in that language

#### Scenario: Invalid person id
- **WHEN** `GET /api/report-tuned` is requested with a non-numeric or missing `id`
- **THEN** the system returns HTTP 400

### Requirement: Tuned report safety
The system SHALL produce tuned reports without divide-by-zero, KeyError, or HTML injection, and without regressing the existing default report path.

#### Scenario: All-zero weights
- **WHEN** every signal weight is set to 0
- **THEN** `weighting_text` does not divide by zero (the weight total is guarded with `or 1.0`)

#### Scenario: Missing signal column
- **WHEN** a candidate row lacks a signal column
- **THEN** `rerank_for_person` treats it as 0 rather than raising `KeyError`

#### Scenario: Report content is escaped before tokens
- **WHEN** report markdown is converted by `markdown_to_chat_html`
- **THEN** the content is HTML-escaped before `[tune:]` and markdown substitution, so report text cannot inject script

### Requirement: Deep, faithful candidate pool
The system SHALL precompute the top-50 candidates per person while preserving each person's existing top-5 exactly.

#### Scenario: Pool deepened without changing top-5
- **WHEN** `people_matches_v1_1_events.csv` is regenerated with `TOP_K = 50`
- **THEN** the file holds 19500 rows and each sampled person's pre-existing top-5 is unchanged
