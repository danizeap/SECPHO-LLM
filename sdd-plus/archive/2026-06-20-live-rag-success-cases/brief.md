# Brief

## Change

live-rag-success-cases (P3, RAG slice)

## User Need

Answer "what success stories do we have in X?" by *meaning*, not keywords — the first semantic-search
piece, over SECPHO's casos-de-éxito write-ups. Establishes the RAG pattern for the text-rich sources.

## Problem

casos-éxito is loaded but only keyword-searchable; semantic questions ("clean energy", "space") need
embeddings to find relevant cases whose titles don't contain the query words.

## Scope

In scope:
- `search_success_cases` tool: in-RAM embedding index over the case write-ups (lazy build, rebuild on
  data change, persist nothing) + cosine ranking; returns matched cases WITH summary for grounding/citation.
- Keyword fallback when embeddings are unavailable (no key / failure) → always works, tests stay hermetic.
- OpenAI embeddings (`text-embedding-3-small`) via the existing requests plumbing; numpy for cosine.

Out of scope:
- RAG over other text sources (newsletters, project/reto descriptions) — later.
- Persisting embeddings (zero-copy posture). Financial sources + access model (P4).

## Acceptance Criteria

- [x] Semantic search ranks cases by meaning (finds relevant cases without literal keyword matches).
- [x] Keyword fallback without a key; empty when off; matched summary returned (grounding).
- [x] Registered agent tool; hermetic tests (keyword path) + live semantic proof.
- [x] In-memory only (nothing persisted); full suite green.

## Impact Areas

- Backend: `_embed_texts` + in-RAM casos index + `search_success_cases` + schema/dispatch; numpy import.
- Frontend / data model: none.
- API: outbound OpenAI embeddings call (when a key is present); no new inbound API.
- AI/model behavior: fourteenth tool — the first semantic/embeddings retrieval; deterministic keyword fallback.
- Documentation: agentic-conversation delta (semantic search requirement + tool).
- Operations/security: embeddings + index are in-RAM only (nothing persisted); casos are 🟢; uses the OpenAI key already in env.

## Open Questions

- Embedding cost at scale is trivial here (59 cases); revisit batching when RAG expands to larger text sources.
