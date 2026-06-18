# Spec Delta: unified-report

Capability: report-generation

## ADDED Requirements

### Requirement: One report model, two renderers — chat preview equals download
The report SHALL be produced from a single deterministic report model rendered two ways: an HTML
fragment for the in-chat preview and a `.docx` for download, both consuming one shared layout
(`report_engine/layout.py`). For the same subject, weighting, and language, the chat preview and
the downloaded document SHALL be identical in structure, wording, order, and numbers. The report
SHALL NOT be assembled free-form by the LLM (which previously caused divergent structure and
mid-document truncation).

#### Scenario: Preview matches the file
- **WHEN** a report is shown in chat and then downloaded for the same subject and weighting
- **THEN** the visible text content of the HTML preview equals the text content of the `.docx`.

#### Scenario: No truncation
- **WHEN** the LLM is slow, unavailable, or returns nothing
- **THEN** the deterministic structure still renders a COMPLETE report (prose slots simply stay empty).

### Requirement: The math fixes the numbers; the LLM only writes prose
Rankings, scores, contact selection, and shared-item lists SHALL be produced deterministically by
the matcher and rendered by code. The LLM SHALL fill only fixed prose slots — a short executive
summary and one "why this is a good match" paragraph per contact — reasoning solely from the
deterministic evidence. The LLM SHALL NOT type, alter, reorder, or invent any number, score, or
contact. Report prose SHALL always use the flagship model regardless of the chat's selected model,
and SHALL be cached by (subject, weighting, language) so the preview and the download reuse the same
prose.

#### Scenario: Scores come from the math
- **WHEN** a report renders
- **THEN** every score and the contact order derive from `rerank_for_person`/the matcher, never from LLM text.

#### Scenario: Per-contact rationale
- **WHEN** the LLM is available
- **THEN** each recommended contact carries an LLM "why this is a good match" paragraph and the report leads with a brief executive summary, both on the flagship model.

### Requirement: Report contacts equal the chat's recommendations
The report SHALL read the same matcher output as the live app (`people_matches_v1_1_events.csv`),
so the report's contacts and order equal the chat's `recommend_contacts` for the same subject. When
a curator applies a custom weighting, that exact weighting and order SHALL flow into both the chat
preview and the downloaded `.docx`.

#### Scenario: Report agrees with chat
- **WHEN** a default-weighting report is generated for a person
- **THEN** its recommended contacts and order match the chat's recommendations for that person.

#### Scenario: Tuned download matches the preview
- **WHEN** a curator tunes the weighting, sees the report, and downloads it
- **THEN** the `.docx` reflects that exact weighting and order.

### Requirement: Personal-data governance in the report
The report SHALL surface professional overlap (technologies, sectors, ámbitos, role, city) and
benign personal-affinity overlap (shared hobbies, sports, languages, university) as icebreaker
evidence. It SHALL NEVER include sensitive fields — children, gender, or food preferences — which
are excluded by allowlist (the report model only carries known-safe fields).

#### Scenario: Sensitive fields excluded
- **WHEN** a report is generated for a member whose record contains children/gender/food_preferences
- **THEN** none of those values appear anywhere in the report.

## MODIFIED Requirements

### Requirement: Authenticated in-app report download
The system SHALL expose `POST /api/report` behind the `/api` authentication gate and a dedicated
rate-limit bucket, returning a `.docx` for a person (`type=person`, `id`) or socio (`type=company`,
`socio`), generated in memory and streamed with `Content-Disposition: attachment`, never written to
disk. For a person, an optional `weights` object SHALL apply the curator's weighting so the download
matches the on-screen preview. Invalid input SHALL return 400, a missing person/socio 404, and an
unauthenticated request 401.

#### Scenario: Tuned person download
- **WHEN** an authenticated staff user posts `{type:"person", id:N, weights:{...}}`
- **THEN** the `.docx` reflects that weighting and order, generated in memory.
