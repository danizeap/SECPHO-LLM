# Plan

## Change

live-rag-success-cases (P3 RAG slice)

## Approach

1. `mvp_web_app.py`: add `OPENAI_EMBED_URL`/`OPENAI_EMBED_MODEL` constants + `import numpy as np`.
2. `_embed_texts(texts)` → L2-normalized embeddings via OpenAI; None on no-key/failure.
3. `_CASOS_RAG` in-RAM cache + `_build_casos_index()` (lazy; rebuild when `(len, titles)` changes;
   stores rows for fallback) + `_casos_doc`/`_casos_out` helpers.
4. `search_success_cases(query, limit)`: if a vector index builds and query non-empty → embed query,
   cosine top-k, return cases+score (mode="semantic"); else keyword fallback over title/summary/
   sectors/technologies (mode="keyword"); empty when no casos. Always returns the matched summary.
5. Schema + dispatch (fourteenth tool).
6. Tests (hermetic, key="" → keyword path): keyword match, summary returned, empty, registered.

## Files Expected To Change

- `backend_api/mvp_web_app.py`; `tests/test_projects_tool.py`; agentic-conversation delta.

## Risks

- Embedding API failure → falls back to keyword (None-safe); never raises.
- Stale index after a refresh → `(len, titles)` hash triggers rebuild.
- Hermeticity (embeddings hit OpenAI) → tests run key-less (module sets `OPENAI_API_KEY=""` before import) → keyword path; semantic path proven separately live.
- Persistence → none: vectors + index live only in RAM.

## Rollback

Revert the `mvp_web_app.py` hunks + tests. The tool falls back to keyword / empty; no data/migration.
