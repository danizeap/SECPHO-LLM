# Capability: model-selection

Purpose: Let chat users choose, per request, between a cheaper `mini` model for
everyday questions and a `flagship` model for complex ones, via a persisted
toggle on the chat composer.

## Requirements

### Requirement: Per-request model tier
The system SHALL select the chat LLM per request from a model tier (`mini` or
`flagship`), defaulting to `mini`, where `flagship` resolves to
`OPENAI_MODEL_FLAGSHIP` (default `gpt-5.5`) and `mini` resolves to `OPENAI_MODEL`
(default `gpt-5-mini`).

#### Scenario: Mini tier resolves the mini model
- **WHEN** a request is handled with no tier or `model=mini`
- **THEN** `current_model()` returns `gpt-5-mini`

#### Scenario: Flagship tier resolves the flagship model
- **WHEN** a request sets `model=flagship`
- **THEN** `current_model()` returns the `OPENAI_MODEL_FLAGSHIP` value (`gpt-5.5` by default)

#### Scenario: Flagship id is configurable, never hardcoded blank
- **WHEN** `OPENAI_MODEL_FLAGSHIP` is set in the environment
- **THEN** the flagship tier uses that value instead of the literal default

### Requirement: Model parameter on chat requests
The system SHALL read the requested tier from the `model` parameter on `/api/*`
GET requests and on the `/api/chat-flow` POST body, treating any value starting
with `flag` as `flagship` and everything else as `mini`.

#### Scenario: HTTP chat resolves the requested tier
- **WHEN** a client calls `/api/chat-flow?model=mini` and then `?model=flagship`
- **THEN** the responses report `gpt-5-mini` and the flagship model respectively

### Requirement: Flagship answer token headroom
The system SHALL raise `max_output_tokens` to at least 4000 for flagship
answer-length calls (`max_output_tokens >= 1000`) so reasoning spend does not
truncate the visible reply, while leaving the small router call unchanged.

#### Scenario: Flagship answer is not truncated
- **WHEN** a flagship answer call is made with the default 1400 tokens
- **THEN** the call is sent with at least 4000 tokens and returns a complete answer

#### Scenario: Router call keeps its small budget
- **WHEN** a flagship call is made with `max_output_tokens < 1000`
- **THEN** the token budget is left unchanged

### Requirement: Model toggle on the chat composer
The system SHALL show a Mini/Flagship toggle on the chat composer, default it to
`mini`, persist the choice to `localStorage` key `secpho_model`, and send the
selected tier as `&model=` on the chat, `/api` GET, and tuner (rerank,
report-tuned) fetches.

#### Scenario: Choice persists across reloads
- **WHEN** the user selects Flagship and reloads the page
- **THEN** the toggle is restored to Flagship from `localStorage` and subsequent fetches send `model=flagship`
