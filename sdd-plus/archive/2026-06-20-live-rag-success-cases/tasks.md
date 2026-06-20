# Tasks

## Change

live-rag-success-cases (P3 RAG slice)

## Implementation

- [x] Embeddings constants + numpy import; `_embed_texts` (None-safe).
- [x] In-RAM `_CASOS_RAG` index + lazy `_build_casos_index` (rebuild on data change) + `_casos_doc`/`_casos_out`.
- [x] `search_success_cases` (semantic top-k; keyword fallback; matched summary returned) + schema + dispatch.
- [x] Hermetic tests (keyword path): match, summary returned, empty, registered.
- [x] Live semantic proof: "espacio y satélites" → space-sector cases by meaning (no literal keyword), cosine-ranked.
- [x] agentic-conversation delta + verify + verifier + sync + archive.
- [ ] Owner glance (when live + key on): "qué casos de éxito tenemos en energía limpia" → relevant stories.
