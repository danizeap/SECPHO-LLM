# Spec Delta: live-rag-success-cases

Capability: agentic-conversation

P3 (RAG slice): semantic search over SECPHO's success stories — the first "answer by meaning" piece.

## ADDED Requirements

### Requirement: Semantic search over success stories
The system SHALL provide a `search_success_cases` tool that retrieves SECPHO success cases (casos de
éxito) by semantic similarity: it embeds the case write-ups into an IN-MEMORY vector index (rebuilt
lazily when the data changes; persisting nothing) and ranks cases by cosine similarity to the query's
embedding. When embeddings are unavailable (no API key or an embedding failure) it SHALL fall back to
deterministic keyword search so it always works. It SHALL return the matched cases WITH their summary
text (so the LLM answers grounded and can cite the actual case), and SHALL return empty when the live
layer is off.

#### Scenario: Semantic match by meaning
- **WHEN** the user asks about a theme (e.g. "space and satellites") and embeddings are available
- **THEN** `search_success_cases` returns the most semantically relevant cases (including ones whose titles don't contain the query words), each with its summary and a similarity score.

#### Scenario: Keyword fallback without embeddings
- **WHEN** no embedding API is available
- **THEN** the tool falls back to keyword search over the case title/summary/sectors/technologies and still returns relevant cases.

## MODIFIED Requirements

### Requirement: Tool-calling agent loop
The tools wrap existing deterministic functions: search_people, get_person_profile, search_socios,
get_socio_profile, rank_socios, list_events, list_retos, list_projects, list_activities,
**search_success_cases**, ecosystem_overview, aggregate_stats, recommend_contacts, rerank_contacts.
`search_success_cases` does semantic (embedding) retrieval over success stories with a keyword
fallback; the others remain deterministic table queries. All return empty/grounded results and never
invent data.

#### Scenario: Success-stories question
- **WHEN** the user asks "what success stories do we have in clean energy?"
- **THEN** the agent calls `search_success_cases` and answers from the returned cases, grounded in their summaries.
