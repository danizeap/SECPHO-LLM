# Capability: report-generation (delta)

Delta from change `report-download`. Merge into the living `report-generation` capability spec on sync.

## ADDED Requirements

### Requirement: Authenticated in-app report download
The system SHALL expose `POST /api/report` behind the `/api` authentication gate and a dedicated rate-limit bucket, returning a `.docx` for a person (`type=person`, `id`) or socio (`type=company`, `socio`). The document SHALL be generated in memory and streamed with `Content-Disposition: attachment`; it SHALL NOT be written to the server's disk. Invalid input SHALL return 400, a missing person/socio 404, and an unauthenticated request 401.

#### Scenario: Staff downloads a person report
- **WHEN** an authenticated staff user sends `POST /api/report {type:"person", id:N}`
- **THEN** the response is a `.docx` attachment for that person, generated in memory.

#### Scenario: Unauthenticated request rejected
- **WHEN** an unauthenticated request hits `POST /api/report`
- **THEN** the response is 401 and no document is generated.

### Requirement: In-chat download affordance
The system SHALL offer report downloads in the chat: a "Descargar .docx" control in the weighting tuner for a person, and `[report:ID]` / `[report-socio:NAME]` tokens rendered as download buttons. The socio name SHALL be carried in an escaped data attribute (never interpolated into an event handler), so a name containing quotes or markup cannot inject script.

#### Scenario: Download button in the tuner
- **WHEN** the weighting tuner is open for a person
- **THEN** a "Descargar .docx" button downloads that person's report.
