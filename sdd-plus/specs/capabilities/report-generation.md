# Capability: report-generation

## Purpose

Generate the member-facing SECPHO "Informe de Valor y Oportunidades" — for a person or official
socio — deterministically from the project's normalized data, with the deterministic matchmaker
filling the "Contactos Recomendados" section. One report model is rendered two ways from a single
shared layout — an in-chat HTML preview and a downloadable `.docx` — so they are identical. The LLM
is never in the structural path and never types a number; it only writes fixed prose slots (an
executive summary and a per-contact "why this is a good match" rationale). The report body is a
Spanish-language deliverable regardless of the chat's UI language.

## Requirements

### Requirement: Deterministic branded report document
The system SHALL generate a member-facing `.docx` report ("Informe de Valor y Oportunidades") for a given person or official socio, where the document structure and all data are produced deterministically from the project's normalized data (no LLM in the structural path), so the same input yields an identical document. Sections, in order: 1 Introducción, 2 Resumen/Ficha, 3 Contactos Recomendados, 4 Eventos y actividades, 5 Retos tecnológicos. (Section 6 Proyectos is added once the projects data source exists.)

#### Scenario: Person report
- **WHEN** `report_engine` generates a report for a person `member_id`
- **THEN** it returns a `.docx` with the índice, introduction, a "Ficha del contacto" (name, company, role, province, technologies, sectors, ámbitos), recommended contacts, events, and retos.

#### Scenario: Company report
- **WHEN** `report_engine` generates a report for an official socio
- **THEN** it returns a `.docx` with the company "Ficha de socio" (socio, company type, member type, public/private, value chain, province, readiness, and the union of its members' technologies/sectors/ámbitos) and the same downstream sections.

#### Scenario: Deterministic output
- **WHEN** the same `member_id`/socio is rendered twice from the same data
- **THEN** the two documents have identical section structure and content (no randomness, no LLM in the structural path).

### Requirement: Contacts come only from the matchmaker
The "Contactos Recomendados" section SHALL be populated solely from the deterministic matchmaker output (`people_matches_v1_1_events`, the same file the live app reads), in the matcher's order (stable sort); the report SHALL NOT invent, reorder, or re-score contacts. The displayed evidence (shared technologies/sectors/ámbitos, plus shared needs, same-location, and benign personal-affinity overlap) is recomputed/cleaned for readability; the ranking remains the matcher's. The app MAY inject a pre-ranked contact list (default or curator-tuned) so the report honors the same order the chat shows.

#### Scenario: Recommendations preserve matcher order
- **WHEN** the contacts section is built for a person
- **THEN** the contacts and their order come from `people_matches_v1` for that target, unchanged.

### Requirement: Event recommendations and attendance with correct dates
The system SHALL recommend upcoming events scored deterministically against the subject's profile and event history, and SHALL list attended events with their real dates. Event dates SHALL be parsed day-first; attendance dates SHALL be looked up from the canonical events table by title — the registration filename's export timestamp SHALL NOT be used as an event date. An attended event not found in the events table SHALL show an honest "Fecha no disponible", never a fabricated date.

#### Scenario: Upcoming events scored
- **WHEN** events are recommended for a subject
- **THEN** only future events (date after today) appear, each with a deterministic affinity score and its real date; an event whose only relevance is the online-attendance bonus is not surfaced.

#### Scenario: Attended events show real dates
- **WHEN** the subject has attended an event that exists in the events table
- **THEN** the event lists its real date from the events table; an attended title absent from the events table shows "Fecha no disponible", never a fabricated date.

### Requirement: Reto recommendations and history
The system SHALL recommend active retos (future closing date) scored by TF-IDF text similarity plus sector overlap, and SHALL list the retos the subject's entity has emitted and applied to, matched by whole entity token (not substring, so "Roca" never matches "ProCareLight") with parenthetical qualifiers stripped.

#### Scenario: Active retos only
- **WHEN** retos are recommended
- **THEN** only retos with a future closing date are considered.

#### Scenario: Entity reto matching is exact, not substring
- **WHEN** the emitted/applied retos are listed for a socio
- **THEN** a reto is attributed only when the socio name matches a whole entity token in the reto's issuing/applying entities, never as an incidental substring of another entity.

### Requirement: Correct text normalization
The system SHALL preserve compound ámbito names that contain commas ("New Space, defensa y seguridad", "Agricultura, bosques y océanos") through tokenization; SHALL canonicalize technology/sector vocabulary (accent-stripping, `&`→`y`, and an alias map) before cross-source overlap so member and event/reto spellings match; and SHALL render Spanish text with correct accents (UTF-8, no replacement characters).

#### Scenario: Compound ámbito preserved
- **WHEN** a cell contains "New Space, defensa y seguridad"
- **THEN** it is treated as one ámbito, not split on its internal comma.

#### Scenario: Vocabulary canonicalized across sources
- **WHEN** a member's "Robótica & Drones" is compared to an event's "Robótica y Drones" (or "Sector Farmaceutico" vs "Sector Farmacéutico")
- **THEN** they are treated as the same item for overlap scoring.

### Requirement: Report engine is a library with a CLI
The system SHALL expose report generation as a `report_engine` package usable as a library and via a CLI (`python -m report_engine --type person|company --id <id> --socio <name> --out <file.docx>`), reading only the project's normalized data and writing a `.docx`. Generated reports SHALL NOT be committed to the repository (they contain member PII).

#### Scenario: CLI generates a file
- **WHEN** `python -m report_engine --type person --id <N> --out out.docx` runs
- **THEN** `out.docx` is written and opens as a valid Word document.

### Requirement: Authenticated in-app report download
The system SHALL expose `POST /api/report` behind the `/api` authentication gate and a dedicated rate-limit bucket, returning a `.docx` for a person (`type=person`, `id`) or socio (`type=company`, `socio`). For a person, an optional `weights` object SHALL apply the curator's weighting so the downloaded document matches the on-screen preview. The document SHALL be generated in memory and streamed with `Content-Disposition: attachment`; it SHALL NOT be written to the server's disk. Invalid input SHALL return 400, a missing person/socio 404, and an unauthenticated request 401.

#### Scenario: Staff downloads a person report
- **WHEN** an authenticated staff user sends `POST /api/report {type:"person", id:N}`
- **THEN** the response is a `.docx` attachment for that person, generated in memory.

#### Scenario: Tuned person download
- **WHEN** an authenticated staff user posts `{type:"person", id:N, weights:{...}}`
- **THEN** the `.docx` reflects that weighting and order, matching the chat preview.

#### Scenario: Unauthenticated request rejected
- **WHEN** an unauthenticated request hits `POST /api/report`
- **THEN** the response is 401 and no document is generated.

### Requirement: In-chat download affordance
The system SHALL offer report downloads in the chat: a "Descargar .docx" control in the weighting tuner for a person, and `[report:ID]` / `[report-socio:NAME]` tokens rendered as download buttons. The socio name SHALL be carried in an escaped data attribute (never interpolated into an event handler), so a name containing quotes or markup cannot inject script.

#### Scenario: Download button in the tuner
- **WHEN** the weighting tuner is open for a person
- **THEN** a "Descargar .docx" button downloads that person's report.

#### Scenario: Per-report download button
- **WHEN** a report is generated inline in the chat
- **THEN** that report carries its own "Descargar .docx" button which downloads the document for the
  exact weighting that produced it (snapshotted), even after the sliders change.

### Requirement: One report model, two renderers — chat preview equals download
The report SHALL be produced from a single deterministic report model rendered two ways through one
shared layout: an HTML fragment for the in-chat preview and a `.docx` for download. For the same
subject, weighting, and language, the preview and the document SHALL be identical in structure,
wording, order, and numbers. The LLM SHALL NOT assemble the document free-form.

#### Scenario: Preview matches the file
- **WHEN** a report is shown in chat and then downloaded for the same subject and weighting
- **THEN** the visible text content of the HTML preview equals the text content of the `.docx`.

#### Scenario: No truncation
- **WHEN** the LLM is slow, unavailable, or returns nothing
- **THEN** the deterministic structure still renders a COMPLETE report (prose slots stay empty).

### Requirement: The math fixes the numbers; the LLM only writes prose
Rankings, scores, contact selection, and shared-item lists SHALL be produced deterministically and
rendered by code. The LLM SHALL fill only fixed prose slots — a short executive summary and one "why
this is a good match" paragraph per contact — reasoning solely from the deterministic evidence,
leading with professional reasons (shared technologies/sectors/needs/location) and treating personal
overlap as a light note. It SHALL NOT type, alter, reorder, or invent any number, score, or contact.
Report prose SHALL always use the flagship model, and SHALL be cached by (subject, weighting, language)
so the preview and the download reuse the same prose.

#### Scenario: Scores come from the math
- **WHEN** a report renders
- **THEN** every score and the contact order derive from the matcher, never from LLM text.

#### Scenario: Per-contact rationale
- **WHEN** the LLM is available
- **THEN** each recommended contact carries an LLM "why this is a good match" paragraph and the report leads with a brief executive summary, both on the flagship model.

### Requirement: Personal-data governance in the report
The report SHALL surface professional overlap (technologies, sectors, ámbitos, needs, role, city) and
benign personal-affinity overlap (shared hobbies, sports, languages, university). It SHALL NEVER
include sensitive fields — children, gender, or food preferences — which are excluded by allowlist
(the report model only carries known-safe fields).

#### Scenario: Sensitive fields excluded
- **WHEN** a report is generated for a member whose record contains children/gender/food_preferences
- **THEN** none of those values appear anywhere in the report.
