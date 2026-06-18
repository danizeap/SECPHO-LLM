# Capability: report-generation

## Purpose

Generate the member-facing SECPHO "Informe de Valor y Oportunidades" — a branded `.docx`
report for a person or official socio — deterministically from the project's normalized data,
with the deterministic matchmaker filling the "Contactos Recomendados" section. The LLM is
never in the structural path, so the format is identical every run.

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
The "Contactos Recomendados" section SHALL be populated solely from the deterministic matchmaker output (`people_matches_v1`), in the matcher's order (stable sort); the report SHALL NOT invent, reorder, or re-score contacts. The displayed evidence (shared technologies/sectors/ámbitos) is recomputed cleanly from the members data at parent level and matched by canonical key for readability; the ranking remains the matcher's.

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
