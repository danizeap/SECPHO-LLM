# Spec Delta: agent-report-unified

Capability: agentic-conversation

## MODIFIED Requirements

### Requirement: Math decides ranking
The system SHALL source recommendation rankings and scores only from the `recommend_contacts` and
`rerank_contacts` tools, and SHALL NOT reorder, re-score, merge, or invent matches; no other tool
emits a ranking. In chat, recommendations are presented as a concise ranked list with one line of
evidence each plus the `[tune:THEIR_MEMBER_ID]` token. When the user explicitly asks for "the
report" / "el informe", the system SHALL render the SINGLE unified report (the same deterministic
report produced by the tuner and the download) inline as an HTML fragment with a "Descargar .docx"
button — NOT a free-form LLM-written document. The chat report SHALL be identical in structure,
contacts, order, and numbers to the tuner/download report.

#### Scenario: Recommendation request
- **WHEN** a user asks who a person should connect with
- **THEN** the agent calls `recommend_contacts`, presents its `recommendations_ranked_by_model` order unchanged, preserves any `[person:ID]` token, and appends `[tune:THEIR_MEMBER_ID]` / `[report:THEIR_MEMBER_ID]` on a final line.

#### Scenario: In-chat report request renders the unified report
- **WHEN** the user asks for "el informe" / "the report" for a person
- **THEN** the chat renders the unified report (deterministic structure, math-fixed numbers, flagship
  prose, "Contactos recomendados", a "Descargar .docx" button), the SAME report as the tuner and the
  download — never a free-form LLM-written briefing.
