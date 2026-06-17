# Capability: conversational-data-access

Purpose: Let the SECPHO chat act as a conversational analyst over the whole dataset — events, retos, ecosystem overviews, and deterministic distributions — answering correctly with or without an OpenAI API key, including English questions over Spanish data.

## Requirements

### Requirement: Event search
The system SHALL let the chat search SECPHO events by topic, technology, sector, province, or timeframe and return a deterministic, rendered list with total and shown counts.

#### Scenario: Search events by topic with timeframe
- **WHEN** a user asks for "upcoming events about photonics"
- **THEN** `search_events` filters `events_normalized` rows whose searchable fields match the expanded topic tokens, restricts to `_date >= today` for the upcoming timeframe, and returns up to 8 rows with a "Upcoming SECPHO events" header

#### Scenario: No matching events
- **WHEN** no events match the query
- **THEN** the rendered answer is "I could not find SECPHO events matching that."

### Requirement: Reto listing with graceful none-open fallback
The system SHALL let the chat list or search retos (challenges) by topic and open/closed status, and when the user asks for open retos but none are currently open it SHALL return the most recent retos under a `none_open` status instead of an empty result.

#### Scenario: Open retos requested but none are open
- **WHEN** a user asks for "open retos" and 0 retos have a `closing_date` on or after today
- **THEN** `list_retos` returns status `none_open` with the most recent retos sorted by closing date, rendered under "No retos are currently open - showing the most recent SECPHO retos"

### Requirement: Ecosystem overview
The system SHALL provide a whole-dataset overview with counts (official socios, recommendable people, all members, subscribers, events and upcoming events, retos and open retos, recommendation rows) plus top technologies, sectors, and socio provinces.

#### Scenario: User asks what data is available
- **WHEN** a user asks "what can you tell me about the SECPHO ecosystem?"
- **THEN** `ecosystem_overview` returns deterministic counts and top-term lists and the rendered answer states the socio/people/member/subscriber/event/reto/recommendation counts

### Requirement: Aggregate distributions
The system SHALL compute deterministic distributions of socios or members along a named dimension (province, company_type, member_type, public_private, technology, sector, readiness), inferring the dimension from the question when not given explicitly.

#### Scenario: Breakdown by province
- **WHEN** a user asks "how many socios by province?"
- **THEN** `aggregate_stats` infers the `province` dimension, counts `socios` rows by province, and returns a ranked distribution (e.g. Barcelona 75, Madrid 41, Valencia 9) rendered as deterministic counts

### Requirement: Accent-insensitive bilingual search
The system SHALL match topic searches across accents and English↔Spanish synonyms so English keywords reach the Spanish source data.

#### Scenario: English photonics query matches Spanish data
- **WHEN** `search_events` is called with query "photonics"
- **THEN** terms expand via NFKD accent-stripping and the EN→ES synonym map (photonics → fotonica) and the search returns matches against "Fotonica" rows (298 results), and the equivalent "fotonica" query also returns results (293)

### Requirement: API-key-independent routing
The system SHALL route chat questions to the correct backend action whether or not an OpenAI API key is configured, using a keyword heuristic router as the fallback.

#### Scenario: Routing without an API key
- **WHEN** no `OPENAI_API_KEY` is set and a user asks an events/retos/overview/breakdown question
- **THEN** `llm_route_question` delegates to `heuristic_route_question`, which routes to `search_events` / `list_retos` / `ecosystem_overview` / `aggregate_stats` by keyword instead of returning `general_answer`
